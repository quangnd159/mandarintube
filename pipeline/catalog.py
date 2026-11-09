#!/usr/bin/env python3
"""Step 3: fetch each candidate channel's public video list with yt-dlp.

Input : data/channels.json   [{"url": "...", "seed": bool, ...}]
Output: data/raw/catalog/<channel_id>.json
Dates are YouTube's relative dates ("3 years ago") turned into approximate
timestamps, which is accurate enough for sorting and age checks.
A failed or suspiciously short fetch keeps the previous list. Exits 4 when many channels
fail, which usually means yt-dlp needs updating.
"""
import concurrent.futures as cf
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data/raw/catalog"
FIELDS = ("id", "title", "duration", "view_count", "timestamp", "availability")
MIN_KEPT = 0.7  # A channel rarely deletes this much at once, but a throttled fetch can look like it.
MAX_FAILED = 0.1


def fetch(entry):
    url = entry["url"].rstrip("/")
    marker = OUT / (url.split("youtube.com/")[-1].replace("/", "_") + ".marker")
    if marker.exists() and "--force" not in sys.argv:
        return f"cached {url}"
    try:
        p = subprocess.run(
            ["yt-dlp", "--no-update", "--flat-playlist", "--ignore-errors", "--extractor-args",
             "youtubetab:approximate_date", "-J", url + "/videos"],
            capture_output=True, text=True, timeout=900)
        d = json.loads(p.stdout) if p.stdout.strip() else None
    except (subprocess.TimeoutExpired, json.JSONDecodeError) as e:
        return f"FAILED {url}: {e!r}"[:300]
    if not d or not d.get("channel_id"):  # yt-dlp prints "null" for a channel that doesn't exist.
        return f"FAILED {url}: {p.stderr[-200:]}"
    videos = [{k: e.get(k) for k in FIELDS} for e in (d.get("entries") or []) if e and e.get("id")]
    previous = OUT / f"{d['channel_id']}.json"
    if previous.exists():
        held = len(json.loads(previous.read_text())["videos"])
        if len(videos) < held * MIN_KEPT:
            return f"FAILED {url}: only {len(videos)} of {held} videos came back, kept the old list"
    slim = {"channel_id": d.get("channel_id"), "name": (d.get("channel") or "").strip(),
            "handle": d.get("uploader_id"), "followers": d.get("channel_follower_count"),
            "description": d.get("description") or "", "input_url": url, "videos": videos}
    (OUT / f"{slim['channel_id']}.json").write_text(json.dumps(slim, ensure_ascii=False))
    marker.write_text(slim["channel_id"] or "")
    return f"ok {slim['name']} ({len(videos)} videos, {slim['followers']} followers)"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    entries = json.loads((ROOT / "data/channels.json").read_text())
    failed = 0
    with cf.ThreadPoolExecutor(3) as ex:
        for msg in ex.map(fetch, entries):
            failed += msg.startswith("FAILED")
            print(msg, flush=True)
    print(f"{failed} of {len(entries)} channels failed", flush=True)
    if failed > len(entries) * MAX_FAILED:
        sys.exit(4)


if __name__ == "__main__":
    main()
