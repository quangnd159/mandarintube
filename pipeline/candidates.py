#!/usr/bin/env python3
"""Step 2: turn the Reddit harvest into a tally of candidate channels.

Two kinds of evidence are extracted:
  * links   - YouTube URLs. Video links are resolved to their channel via oEmbed.
  * names   - capitalised phrases such as "Lazy Chinese", for people who
              recommend a channel without linking it.
Output: data/raw/candidate_links.json and data/raw/candidate_names.json.
"""
import collections
import concurrent.futures as cf
import json
import pathlib
import re
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
OEMBED = RAW / "oembed.json"

VIDEO = re.compile(r"(?:youtube\.com/(?:watch\?(?:[^\s)\]]*&)?v=|embed/|live/|shorts/)|youtu\.be/)([\w-]{11})")
HANDLE = re.compile(r"youtube\.com/@([\w.\-%]+)")
CHAN = re.compile(r"youtube\.com/(channel/UC[\w-]{22}|c/[\w.\-%]+|user/[\w.\-%]+)")
NAME = re.compile(
    r"\b((?:[A-Z][\w'’]*\s+){0,4}(?:Chinese|Mandarin|HSK|Hanyu)(?:\s+(?:with|With|by|from|Corner|Click|Pod|Class|Podcast|Online|Blueprint|Learning|Zero|to|Hero|[A-Z][\w'’]*)){0,4})")
STOP = {"chinese", "mandarin", "hsk", "learn chinese", "learning chinese", "learn mandarin", "learning mandarin",
        "the chinese", "in chinese", "standard mandarin", "simplified chinese", "traditional chinese", "modern chinese",
        "taiwanese mandarin", "native chinese", "my chinese", "i chinese", "speak chinese", "speaking chinese",
        "spoken chinese", "written chinese", "basic chinese", "beginner chinese", "easy chinese", "real chinese"}
SELF = re.compile(r"\b(my|our) (own )?(youtube |yt )?(channel|video|videos|podcast)\b|\bi (made|created|started|uploaded|run)\b"
                  r"|\bwe (made|created|started|run)\b|\bsubscribe to (my|our)\b", re.I)


def rows():
    with (RAW / "reddit.jsonl").open() as f:
        for line in f:
            r = json.loads(line)
            r["text"] = " ".join(str(r.get(k) or "") for k in ("body", "title", "selftext", "url"))
            r["thread"] = (r.get("link_id") or r["id"]).replace("t3_", "")
            yield r


def oembed(video_id):
    url = "https://www.youtube.com/oembed?format=json&url=" + urllib.parse.quote(f"https://youtu.be/{video_id}")
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"}), timeout=20) as r:
            d = json.load(r)
            return {"name": d.get("author_name"), "url": d.get("author_url"), "title": d.get("title")}
    except urllib.error.HTTPError as e:
        return {"dead": e.code}
    except Exception as e:
        return {"error": str(e)}


def main():
    cache = json.loads(OEMBED.read_text()) if OEMBED.exists() else {}
    links = []
    names = collections.defaultdict(lambda: {"authors": set(), "threads": set()})
    for r in rows():
        author = r.get("author") or "[deleted]"
        if author in ("AutoModerator", "[deleted]") or (r.get("score") or 0) < 1:
            continue
        if SELF.search(r["text"]):
            continue
        # A bare link post is usually someone promoting their own channel.
        is_link_post = r["kind"] == "post" and "youtu" in (r.get("url") or "")
        base = {"author": author, "thread": r["thread"], "score": r.get("score") or 0,
                "t": int(r["created_utc"]), "linkpost": is_link_post, "id": r["id"]}
        for v in set(VIDEO.findall(r["text"])):
            links.append({**base, "video": v})
        for h in set(HANDLE.findall(r["text"])):
            links.append({**base, "target": "@" + urllib.parse.unquote(h).lower()})
        for c in set(CHAN.findall(r["text"])):
            links.append({**base, "target": c})
        for m in set(NAME.findall(r["text"])):
            n = re.sub(r"\s+", " ", m).strip(" '’")
            if n.lower() in STOP or len(n) > 45:
                continue
            names[n]["authors"].add(author)
            names[n]["threads"].add(r["thread"])

    todo = sorted({l["video"] for l in links if "video" in l} - cache.keys())
    print("resolving", len(todo), "videos")
    with cf.ThreadPoolExecutor(8) as ex:
        for i, (v, d) in enumerate(zip(todo, ex.map(oembed, todo))):
            if "error" not in d:
                cache[v] = d
            if i % 200 == 0:
                OEMBED.write_text(json.dumps(cache, ensure_ascii=False))
    OEMBED.write_text(json.dumps(cache, ensure_ascii=False))

    tally = collections.defaultdict(lambda: {"name": None, "authors": set(), "threads": set(), "years": set(), "videos": collections.Counter()})
    for l in links:
        if l["linkpost"]:
            continue
        if "video" in l:
            o = cache.get(l["video"]) or {}
            if not o.get("url"):
                continue
            key = o["url"].split("youtube.com/")[-1]
            key = key.lower() if key.startswith("@") else key
            tally[key]["name"] = o["name"]
            tally[key]["videos"][l["video"]] += 1
        else:
            key = l["target"]
        t = tally[key]
        t["authors"].add(l["author"])
        t["threads"].add(l["thread"])
        t["years"].add(1970 + l["t"] // 31556952)
    out = [{"key": k, "name": v["name"], "authors": len(v["authors"]), "threads": len(v["threads"]),
            "years": sorted(v["years"]), "top_videos": v["videos"].most_common(5)} for k, v in tally.items()]
    out.sort(key=lambda x: -x["authors"])
    (RAW / "candidate_links.json").write_text(json.dumps(out, ensure_ascii=False, indent=0))
    nm = [{"name": k, "authors": len(v["authors"]), "threads": len(v["threads"])} for k, v in names.items() if len(v["authors"]) >= 2]
    nm.sort(key=lambda x: -x["authors"])
    (RAW / "candidate_names.json").write_text(json.dumps(nm, ensure_ascii=False, indent=0))
    print("link candidates", len(out), "name candidates", len(nm))
    for x in out[:80]:
        print(x["authors"], x["threads"], x["key"], "|", x["name"])
    print("--- names")
    for x in nm[:120]:
        print(x["authors"], x["threads"], x["name"])


if __name__ == "__main__":
    main()
