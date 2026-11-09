#!/usr/bin/env python3
"""Add the strongest channels not yet assessed to data/channels.json as candidates.

Reads data/raw/candidate_links.json (Reddit) and data/raw/discovered.json (YouTube search).
A candidate can't reach the site: build.py holds it until review.py approves it. Adding it
only means the next steps gather its evidence and frames for that review.
Usage: shortlist.py [how many, default 10]
"""
import datetime as dt
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHANNELS = ROOT / "data/channels.json"
MIN_PEOPLE, MIN_QUERIES = 3, 3


def norm(key):
    """One spelling for @name, user/name, c/name and channel/UC... forms of an address."""
    key = (key or "").split("youtube.com/")[-1].strip("/").lower()
    return re.sub(r"^(@|user/|c/|channel/)", "", key)


def known_channels():
    known = {norm(e["url"]) for e in json.loads(CHANNELS.read_text())}
    review = json.loads((ROOT / "data/review.json").read_text())
    known |= {norm(h) for h in review["exclude"]} | {norm(h) for h in review.get("reviewed", {})}
    for f in (ROOT / "data/raw/catalog").glob("*.json"):
        c = json.loads(f.read_text())
        known |= {norm(c.get("handle")), norm(c.get("channel_id")), norm(c.get("input_url"))}
    return known - {""}


def url_for(key):
    return "https://www.youtube.com/" + key


def rank(links, search, known):
    """Candidates with at least some independent evidence, strongest first."""
    found = {}
    for x in links:
        n = norm(x["key"])
        if n not in known and x["authors"] >= MIN_PEOPLE:
            found[n] = {"url": url_for(x["key"]), "name": x.get("name"), "people": x["authors"], "queries": 0}
    for x in search:
        n = norm(x.get("handle")) or norm(x["id"])
        if norm(x["id"]) in known or n in known or len(x["queries"]) < MIN_QUERIES:
            continue
        row = found.setdefault(n, {"url": url_for(x.get("handle") or f"channel/{x['id']}"), "name": x["name"], "people": 0, "queries": 0})
        row["queries"] = len(x["queries"])
        row["name"] = row["name"] or x["name"]
    # A person recommending a channel counts for more than a search engine surfacing it.
    return sorted(found.values(), key=lambda r: -(2 * r["people"] + r["queries"]))


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    links = json.loads((ROOT / "data/raw/candidate_links.json").read_text())
    search = json.loads((ROOT / "data/raw/discovered.json").read_text())["search"]
    picks = rank(links, search, known_channels())[:limit]
    channels = json.loads(CHANNELS.read_text())
    today = dt.date.today().isoformat()
    channels += [{"url": p["url"], "candidate": today} for p in picks]
    CHANNELS.write_text(json.dumps(channels, ensure_ascii=False, indent=2) + "\n")
    print(len(picks), "candidates added")
    for p in picks:
        print(f"{p['people']:>3} recommenders  {p['queries']:>2} searches  {p['url']}  {p['name'] or ''}")


if __name__ == "__main__":
    main()
