#!/usr/bin/env python3
"""Find newer candidate channels through YouTube search and @mentions in seed titles.

Being found here only makes a channel a candidate. Reddit and fan evidence rank it.
Output: data/raw/discovered.json
"""
import collections
import concurrent.futures as cf
import glob
import json
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
QUERIES = ["comprehensible input chinese", "comprehensible input mandarin", "chinese comprehensible input beginner",
           "chinese comprehensible input intermediate", "learn chinese through stories", "chinese listening practice HSK3",
           "chinese listening practice HSK4", "chinese listening practice intermediate", "slow chinese podcast",
           "easy chinese podcast", "intermediate chinese podcast", "advanced chinese podcast", "mandarin immersion all chinese",
           "chinese vlog with subtitles for learners", "learn chinese with stories beginners", "HSK 2 chinese story",
           "chinese conversation for learners", "street interviews chinese learners", "中文听力 中级", "中文播客 外国人学中文",
           "用中文讲故事 学中文", "汉语听力练习 HSK", "TPRS chinese", "learn mandarin in mandarin"]


def search(q):
    p = subprocess.run(["yt-dlp", "--no-update", "--flat-playlist", "--playlist-end", "60", "-J", f"ytsearch60:{q}"],
                       capture_output=True, text=True, timeout=240)
    try:
        return q, json.loads(p.stdout).get("entries") or []
    except json.JSONDecodeError:
        return q, []


def main():
    tally = collections.defaultdict(lambda: {"name": None, "handle": None, "queries": set(), "hits": 0, "sample": []})
    with cf.ThreadPoolExecutor(3) as ex:
        for q, entries in ex.map(search, QUERIES):
            print(q, len(entries), flush=True)
            for e in entries:
                cid = e.get("channel_id")
                if not cid:
                    continue
                t = tally[cid]
                t["name"], t["handle"] = (e.get("channel") or "").strip(), e.get("uploader_id")
                t["queries"].add(q)
                t["hits"] += 1
                if len(t["sample"]) < 2:
                    t["sample"].append(e.get("title"))
    mentions = collections.Counter()
    for f in glob.glob(str(ROOT / "data/raw/catalog/*.json")):
        d = json.loads(pathlib.Path(f).read_text())
        for v in d["videos"]:
            for m in re.findall(r"@([\w.\-]{3,})", v.get("title") or ""):
                mentions[m.lower()] += 1
        for m in re.findall(r"@([\w.\-]{3,})", d.get("description") or ""):
            if "." not in m:
                mentions[m.lower()] += 1
    out = sorted(({"id": k, **{x: (sorted(v[x]) if x == "queries" else v[x]) for x in v}} for k, v in tally.items()),
                 key=lambda x: (-len(x["queries"]), -x["hits"]))
    (ROOT / "data/raw/discovered.json").write_text(json.dumps({"search": out, "mentions": mentions.most_common()}, ensure_ascii=False, indent=0))
    for x in out:
        if len(x["queries"]) >= 2:
            print(len(x["queries"]), x["hits"], x["handle"], "|", x["name"], "|", (x["sample"][0] or "")[:60])
    print("--- mentions", mentions.most_common(25))


if __name__ == "__main__":
    main()
