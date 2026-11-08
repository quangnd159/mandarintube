#!/usr/bin/env python3
"""Step 1: pull every Reddit comment/post that might recommend a Mandarin video.

Source: the Arctic Shift archive (reddit.com itself blocks scripted search).
Output: data/raw/reddit.jsonl, one de-duplicated record per comment/post.
        data/raw/reddit_gaps.json, every time window the archive would not serve.

The archive times out on heavy searches, so each query walks time windows and
splits a window in half when it times out. Finished windows are remembered, so
a re-run resumes where it stopped.
"""
import calendar
import http.client
import json
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
OUT = RAW / "reddit.jsonl"
DONE = RAW / "reddit_done.json"
GAPS = RAW / "reddit_gaps.json"
API = "https://arctic-shift.photon-reddit.com/api"

# Language-specific subs: every hit is on topic.
ZH_SUBS = ["ChineseLanguage", "MandarinChinese", "learnchinese", "Chinese"]
# Most useful first, so an interrupted run still holds the best evidence.
QUERIES = ["youtube", "youtu.be", "comprehensible input", "youtuber", "podcast", "channel"]
# General subs: the search phrase itself has to establish the topic.
GENERAL_SUBS = ["languagelearning"]
GENERAL_QUERIES = ["chinese youtube", "mandarin youtube", "chinese comprehensible input",
                   "mandarin comprehensible input"]

KEEP = ("id", "author", "score", "created_utc", "body", "link_id", "subreddit", "permalink",
        "author_flair_text", "title", "selftext", "url", "num_comments")
FIRST_YEAR = 2012
MIN_WINDOW = 7 * 86400


class ArchiveTimeout(Exception):
    pass


def get(kind, params):
    url = f"{API}/{kind}/search?" + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "mandarintube-harvest/1.0"})
            with urllib.request.urlopen(req, timeout=60) as r:
                remaining = r.headers.get("x-ratelimit-remaining")
                if remaining is not None and int(remaining) < 5:
                    time.sleep(int(r.headers.get("x-ratelimit-reset", 30)) + 1)
                return json.load(r).get("data") or []
        except urllib.error.HTTPError as e:
            if e.code == 400:
                raise RuntimeError(f"bad request {url}: {e.read()[:200]!r}")
            if e.code == 422:  # the archive's own query timeout
                time.sleep(2 + attempt * 3)
                continue
            time.sleep(2 ** attempt * 3)
        except (OSError, http.client.HTTPException, json.JSONDecodeError) as e:
            # Connection drops mean the archive is struggling, so back off properly.
            print(f"  retry: {e!r}", file=sys.stderr, flush=True)
            time.sleep(20 * (attempt + 1))
    raise ArchiveTimeout(url)


def walk_window(kind, sub, field, query, start, end, seen, out, gaps):
    """Fetch [start, end), splitting on timeouts. Returns the number of new rows."""
    added = 0
    after = start
    while after < end:
        try:
            rows = get(kind, {"subreddit": sub, field: query, "limit": 100, "sort": "asc",
                              "after": after, "before": end})
        except ArchiveTimeout:
            if end - after <= MIN_WINDOW:
                gaps.append({"kind": kind, "sub": sub, "query": query, "after": after, "before": end})
                print(f"  gap {kind} {sub} {query!r} {after}-{end}", flush=True)
                return added
            mid = (after + end) // 2
            return (added
                    + walk_window(kind, sub, field, query, after, mid, seen, out, gaps)
                    + walk_window(kind, sub, field, query, mid, end, seen, out, gaps))
        if not rows:
            break
        for row in rows:
            if row["id"] in seen:
                continue
            seen.add(row["id"])
            rec = {k: row[k] for k in KEEP if k in row}
            rec["kind"] = "comment" if kind == "comments" else "post"
            rec["q"] = query
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            added += 1
        out.flush()
        if len(rows) < 100:
            break
        newest = int(rows[-1]["created_utc"])
        # A full page sharing one timestamp would loop forever, so always move forward.
        after = newest if newest > after else after + 1
        time.sleep(0.2)
    return added


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    seen = set()
    if OUT.exists():
        with OUT.open() as f:
            seen = {json.loads(line)["id"] for line in f}
    done = set(json.loads(DONE.read_text())) if DONE.exists() else set()
    gaps = []  # A year with gaps is not marked done, so a re-run retries it.
    this_year = time.gmtime().tm_year
    with OUT.open("a") as out:
        jobs = [(sub, q) for q in QUERIES for sub in ZH_SUBS] + [(sub, q) for q in GENERAL_QUERIES for sub in GENERAL_SUBS]
        for sub, q in jobs:
            for kind, field in (("comments", "body"), ("posts", "query")):
                added = 0
                for year in range(FIRST_YEAR, this_year + 1):
                    key = f"{kind}|{sub}|{q}|{year}"
                    if key in done:
                        continue
                    start = calendar.timegm((year, 1, 1, 0, 0, 0))
                    end = calendar.timegm((year + 1, 1, 1, 0, 0, 0))
                    before = len(gaps)
                    added += walk_window(kind, sub, field, q, start, end, seen, out, gaps)
                    # The current year is never final, so a re-run fetches it again.
                    if year < this_year and len(gaps) == before:
                        done.add(key)
                    DONE.write_text(json.dumps(sorted(done)))
                    GAPS.write_text(json.dumps(gaps))
                print(f"{kind} {sub} {q!r}: +{added} (total {len(seen)}, gaps {len(gaps)})", flush=True)
    print("done", len(seen), "gaps", len(gaps), flush=True)


if __name__ == "__main__":
    main()
