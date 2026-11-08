#!/usr/bin/env python3
"""Download the full history of the Mandarin-learning subreddits, newest first.

The archive's text search times out on common words, but plain date-ordered reads
are cheap. So everything comes down once and channel names are matched locally.
Output: data/raw/corpus/<kind>_<sub>.jsonl, plus a .cursor file for resuming.
"""
import calendar
import concurrent.futures as cf
import json
import pathlib
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from reddit_harvest import ArchiveTimeout, get  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data/raw/corpus"
WORKERS = 5


def year_ts(y):
    return calendar.timegm((y, 1, 1, 0, 0, 0))


# Small subs are one stream each. r/ChineseLanguage holds a million comments, so it is
# split by year and the executor works newest-first: a cut-off run loses the oldest rows.
STOP_ALL = year_ts(2010)
STREAMS = [("comments", s, STOP_ALL, None, f"comments_{s}") for s in ("MandarinChinese", "learnchinese")]
STREAMS += [("posts", s, STOP_ALL, None, f"posts_{s}") for s in ("ChineseLanguage", "MandarinChinese", "learnchinese")]
STREAMS += [("comments", "ChineseLanguage", year_ts(2026), None, "comments_ChineseLanguage")]
STREAMS += [("comments", "ChineseLanguage", year_ts(y), year_ts(y + 1), f"comments_ChineseLanguage_{y}") for y in range(2025, 2013, -1)]
KEEP_C = ("id", "author", "score", "created_utc", "body", "link_id", "permalink")
KEEP_P = ("id", "author", "score", "created_utc", "title", "selftext", "url", "permalink", "num_comments")


def run(stream):
    kind, sub, stop, start, name = stream
    path = OUT / f"{name}.jsonl"
    cursor_path = path.with_suffix(".cursor")
    before = int(cursor_path.read_text()) if cursor_path.exists() else (start or int(time.time()))
    keep = KEEP_C if kind == "comments" else KEEP_P
    seen_at_edge, total, fails = set(), 0, 0
    with path.open("a") as out:
        while before > stop:
            try:
                rows = get(kind, {"subreddit": sub, "limit": 100, "sort": "desc", "before": before + 1})
            except ArchiveTimeout:
                fails += 1
                time.sleep(min(300, 30 * fails))
                continue
            fails = 0
            fresh = [r for r in rows if r["id"] not in seen_at_edge]
            if not fresh:
                if len(rows) < 100:
                    break
                before -= 1  # A full page sharing one timestamp: step past it.
                continue
            for r in fresh:
                if int(r["created_utc"]) < stop:
                    continue
                rec = {k: r[k] for k in keep if k in r}
                rec["kind"] = "comment" if kind == "comments" else "post"
                rec["subreddit"] = sub
                out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            total += len(fresh)
            before = int(rows[-1]["created_utc"])
            seen_at_edge = {r["id"] for r in rows if int(r["created_utc"]) == before}
            cursor_path.write_text(str(before))
            if total % 5000 < 100:
                print(f"{name}: {total} rows, back to {time.strftime('%Y-%m', time.gmtime(before))}", flush=True)
            if len(rows) < 100:
                break
            time.sleep(0.2)
    (path.with_suffix(".done")).write_text("done")
    print(f"{name}: finished, {total} rows this run", flush=True)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    todo = [s for s in STREAMS if not (OUT / f"{s[4]}.done").exists()]
    with cf.ThreadPoolExecutor(WORKERS) as ex:
        for f in cf.as_completed([ex.submit(run, s) for s in todo]):
            f.result()
    print("done", flush=True)


if __name__ == "__main__":
    main()
