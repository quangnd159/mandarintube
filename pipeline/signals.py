#!/usr/bin/env python3
"""Step 4: sample each channel's videos for comments, captions and AI markers.

Output: data/raw/signals/<video_id>.json   comments (commenter IDs hashed), stats
        data/raw/captions/<video_id>.txt   plain Chinese caption text with timing total
Raw comments stay in data/raw, which is git-ignored and never published.
Re-runs skip finished videos, and a 429 pauses the worker rather than recording nothing.
"""
import concurrent.futures as cf
import glob
import hashlib
import json
import os
import pathlib
import random
import re
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data/raw/catalog"
SIG = ROOT / "data/raw/signals"
CAP = ROOT / "data/raw/captions"
SALT = "mandarintube-fan-graph"
SAMPLE = int(os.environ.get("SAMPLE", 14))
WORKERS = int(os.environ.get("WORKERS", 3))
pause_until = [0.0]
lock = threading.Lock()
# YouTube's own creator disclosure, shown on the watch page.
AI_LABEL = re.compile(r"Altered or synthetic content|howThisWasMadeSection", re.I)


def sample(videos):
    """Half the most-watched, half spread across the channel's history."""
    public = [v for v in videos if not v.get("availability") and (v.get("duration") or 0) >= 90]
    top = sorted(public, key=lambda v: -(v.get("view_count") or 0))[: SAMPLE // 2]
    ids = {v["id"] for v in top}
    rest = [v for v in sorted(public, key=lambda v: v.get("timestamp") or 0) if v["id"] not in ids]
    n = SAMPLE - len(top)
    if rest and n:
        step = max(1, len(rest) // n)
        top += rest[::step][:n]
    return top


def wait_if_paused():
    while True:
        with lock:
            delay = pause_until[0] - time.time()
        if delay <= 0:
            return
        time.sleep(min(delay, 15))


def backoff(seconds):
    with lock:
        pause_until[0] = max(pause_until[0], time.time() + seconds)
    print(f"  rate limited, pausing {seconds}s", flush=True)


def vtt_to_text(path):
    """Returns (text, seconds of speech covered) from a WebVTT file."""
    text, seconds, last = [], 0.0, None
    stamp = re.compile(r"(\d+):(\d+):(\d+)\.(\d+) --> (\d+):(\d+):(\d+)\.(\d+)")
    for line in pathlib.Path(path).read_text(errors="ignore").splitlines():
        m = stamp.search(line)
        if m:
            g = [int(x) for x in m.groups()]
            seconds += max(0, (g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000) - (g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000))
            continue
        line = re.sub(r"<[^>]+>", "", line).strip()
        if not line or line.isdigit() or line.startswith(("WEBVTT", "Kind:", "Language:")) or line == last:
            continue
        text.append(line)
        last = line
    return "\n".join(text), seconds


def fetch(video_id):
    sig_path = SIG / f"{video_id}.json"
    if sig_path.exists():
        return "cached"
    wait_if_paused()
    with tempfile.TemporaryDirectory() as tmp:
        p = subprocess.run(
            ["yt-dlp", "--no-update", "--skip-download", "--no-warnings", "--write-comments",
             "--extractor-args", "youtube:max_comments=150,all,0,0;comment_sort=top",
             "--write-subs", "--write-auto-subs", "--sub-langs", "zh-Hans,zh-CN,zh,zh-Hans-orig,zh-orig", "--sub-format", "vtt",
             "--ignore-no-formats-error", "--ignore-errors", "--sleep-subtitles", "2",
             "-o", f"{tmp}/%(id)s.%(ext)s", "-J", "--no-simulate", f"https://youtu.be/{video_id}"],
            capture_output=True, text=True, timeout=300)
        if "429" in p.stderr or "Sign in to confirm" in p.stderr:
            backoff(180)
        if not p.stdout.strip():
            return f"FAILED {video_id}: {p.stderr.strip()[-160:]}"
        d = json.loads(p.stdout)
        manual = bool(d.get("subtitles") and any(k.startswith("zh") for k in d["subtitles"]))
        # YouTube offers machine-translated zh-Hans captions for videos in other languages,
        # and those would make an English lesson look fully Mandarin. "-orig" marks the
        # language actually spoken, so auto captions only count when they are Chinese.
        auto_orig = [k for k in (d.get("automatic_captions") or {}) if k.endswith("-orig")]
        spoken_zh = (d.get("language") or "").startswith("zh") or any(k.startswith("zh") for k in auto_orig)
        vtts = sorted(glob.glob(f"{tmp}/*.vtt")) if (manual or spoken_zh) else []
        cap_seconds = 0.0
        if vtts:
            text, cap_seconds = vtt_to_text(vtts[0])
            (CAP / f"{video_id}.txt").write_text(text)
    comments = [{"a": hashlib.sha256((SALT + (c.get("author_id") or "")).encode()).hexdigest()[:16],
                 "t": c.get("text") or "", "l": c.get("like_count") or 0, "u": bool(c.get("author_is_uploader"))}
                for c in (d.get("comments") or [])]
    disclosed = False
    try:
        req = urllib.request.Request(f"https://www.youtube.com/watch?v={video_id}", headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"})
        with urllib.request.urlopen(req, timeout=30) as r:
            disclosed = bool(AI_LABEL.search(r.read().decode("utf-8", "ignore")))
    except OSError:
        pass
    sig_path.write_text(json.dumps({
        "id": video_id, "channel": d.get("channel_id"), "views": d.get("view_count"), "likes": d.get("like_count"),
        "comment_count": d.get("comment_count"), "upload_date": d.get("upload_date"), "duration": d.get("duration"),
        "manual_captions": manual, "language": d.get("language"), "auto_orig": auto_orig, "title": d.get("title"), "caption_seconds": cap_seconds, "ai_disclosed": disclosed,
        "playable_embed": d.get("playable_in_embed"), "comments": comments}, ensure_ascii=False))
    time.sleep(random.uniform(0.5, 1.5))
    return "ok"


def main():
    SIG.mkdir(parents=True, exist_ok=True)
    CAP.mkdir(parents=True, exist_ok=True)
    only = set(sys.argv[1:])
    todo = []
    for f in sorted(CATALOG.glob("*.json")):
        d = json.loads(f.read_text())
        if only and d["channel_id"] not in only:
            continue
        todo += [(d["name"], v["id"]) for v in sample(d["videos"])]
    print(f"{len(todo)} videos to sample", flush=True)
    results = {}
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        futures = {ex.submit(fetch, vid): (name, vid) for name, vid in todo}
        for i, fut in enumerate(cf.as_completed(futures), 1):
            try:
                r = fut.result()
            except Exception as e:  # One bad video must not stop the run.
                r = f"FAILED {futures[fut][1]}: {e!r}"
            key = r.split()[0]
            results[key] = results.get(key, 0) + 1
            if r.startswith("FAILED"):
                print(r, flush=True)
            if i % 25 == 0:
                print(f"{i}/{len(todo)} {results}", flush=True)
    print("done", results, flush=True)


if __name__ == "__main__":
    main()
