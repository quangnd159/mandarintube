#!/usr/bin/env python3
"""Decide on candidate channels. A channel is only listed once it's approved here.

Usage: review.py list                      channels waiting, with their evidence
       review.py approve @handle [level]   list it, optionally with a level from 1 to 4
       review.py reject @handle "reason"   keep it out. The reason stays local.
Run build.py afterwards, or let the next update pick it up.
"""
import datetime as dt
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REVIEW = ROOT / "data/review.json"
NOTES = ROOT / "data/raw/review_notes.json"


def load():
    return json.loads(REVIEW.read_text())


def save(review):
    REVIEW.write_text(json.dumps(review, ensure_ascii=False, indent=2) + "\n")


def known_handle(handle):
    audit = json.loads((ROOT / "data/audit.json").read_text())
    for a in audit:
        if (a["handle"] or "").lower() == handle.lower():
            return a["handle"]
    sys.exit(f"{handle} isn't in data/audit.json. Run build.py, or check the spelling.")


def without(items, handle):
    return [x for x in items if x.lower() != handle.lower()]


def approve(handle, level=None):
    review = load()
    review["exclude"] = without(review["exclude"], handle)
    review["reviewed"][handle] = dt.date.today().isoformat()
    review["reviewed"] = dict(sorted(review["reviewed"].items(), key=lambda kv: kv[0].lower()))
    if level:
        review["levels"][handle] = level
    save(review)


def reject(handle, reason):
    review = load()
    review["reviewed"] = {k: v for k, v in review["reviewed"].items() if k.lower() != handle.lower()}
    review["exclude"] = sorted(without(review["exclude"], handle) + [handle], key=str.lower)
    save(review)
    notes = json.loads(NOTES.read_text()) if NOTES.exists() else {}
    notes.setdefault("exclude", {})[handle] = {"kind": "other", "reason": reason}
    NOTES.write_text(json.dumps(notes, ensure_ascii=False, indent=1))


def pending():
    return [a for a in json.loads((ROOT / "data/audit.json").read_text()) if a["status"] == "pending-review"]


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "list"
    if command == "list":
        rows = pending()
        print(len(rows), "waiting for review")
        for a in sorted(rows, key=lambda a: -a["people"]):
            print(f"{a['handle']:32} {a['people']:>3} recommenders  {a['shared'] or 0:>3} shared fans  {a['videos']:>4} videos  {a['name']}")
    elif command == "approve" and len(sys.argv) in (3, 4):
        level = int(sys.argv[3]) if len(sys.argv) == 4 else None
        if level is not None and level not in (1, 2, 3, 4):
            sys.exit("Level must be 1 beginner, 2 lower intermediate, 3 intermediate or 4 advanced.")
        approve(known_handle(sys.argv[2]), level)
        print("approved", sys.argv[2])
    elif command == "reject" and len(sys.argv) == 4:
        reject(known_handle(sys.argv[2]), sys.argv[3])
        print("rejected", sys.argv[2])
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
