#!/usr/bin/env python3
"""Ask Claude to look at channel frames and write advice for a person to act on.

Usage: frame_review.py                candidates waiting for review
       frame_review.py --listed       those, plus every listed channel, to catch a change
Output: data/raw/review_report.md. Nothing here changes what the site lists, so a bad
answer can't publish or remove anything. Only review.py does that.
Claude's only tool is Read, limited to the folder of sheets it's looking at.
"""
import datetime as dt
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPORT = ROOT / "data/raw/review_report.md"
MODEL = "claude-sonnet-5-5"
PER_RUN = 3  # Sheets per Claude session, which keeps each answer short enough to finish.


def parse_verdicts(reply):
    start, end = reply.find("["), reply.rfind("]")
    if start < 0 or end < start:
        raise ValueError("no JSON array in the reply")
    return [v for v in json.loads(reply[start:end + 1]) if isinstance(v, dict) and v.get("handle")]


def ask(sheet_dir, names):
    prompt = (ROOT / "pipeline/frame_review_prompt.md").read_text() + "\n\nRead these sheets: " + ", ".join(names)
    p = subprocess.run(["claude", "-p", "--model", MODEL, "--tools", "Read", "--allowedTools", "Read(./**)",
                        "--permission-mode", "dontAsk", "--strict-mcp-config", "--setting-sources", "",
                        "--no-session-persistence"],
                       input=prompt, capture_output=True, text=True, timeout=900, cwd=sheet_dir)
    if p.returncode:
        raise RuntimeError((p.stderr or p.stdout)[-300:])
    return parse_verdicts(p.stdout)


def section(title, rows, verdicts):
    lines = [f"## {title} ({len(rows)})", ""]
    for a in sorted(rows, key=lambda a: -(a.get("people") or 0)):
        v = verdicts.get(a["handle"].lower(), {"verdict": "not checked", "note": "No answer for this channel."})
        lines.append(f"- **{a['handle']}**, {a['name']}: {v.get('verdict')}. {v.get('note', '')} "
                     f"({a['people']} Reddit recommenders, {a.get('shared') or 0} shared fans, {a['videos']} videos, "
                     f"https://www.youtube.com/{a['handle']})")
    return lines + [""]


def main():
    audit = json.loads((ROOT / "data/audit.json").read_text())
    pending = [a for a in audit if a["status"] == "pending-review" and a["handle"]]
    listed = [a for a in audit if a["status"] == "kept" and a["handle"]] if "--listed" in sys.argv else []
    rows = pending + listed
    if not rows:
        print("nothing to review")
        return
    today = dt.date.today().isoformat()
    sheet_dir = ROOT / "data/raw/sheets" / f"review_{today}"
    subprocess.run([sys.executable, str(ROOT / "pipeline/contact_sheets.py"), "--out", str(sheet_dir)] + [a["handle"] for a in rows], check=True)
    sheets = sorted(p.name for p in sheet_dir.glob("*.jpg"))
    verdicts, failed = {}, 0
    for i in range(0, len(sheets), PER_RUN):
        try:
            for v in ask(sheet_dir, sheets[i:i + PER_RUN]):
                verdicts[v["handle"].lower()] = v
        except (ValueError, RuntimeError, subprocess.TimeoutExpired, json.JSONDecodeError) as e:
            failed += 1
            print(f"sheets {sheets[i:i + PER_RUN]} failed: {e}", flush=True)
    worrying = [a for a in listed if verdicts.get(a["handle"].lower(), {}).get("verdict") in ("generated", "mixed")]
    out = [f"# Channel review, {today}", "",
           "Advice from Claude after looking at video frames. It can't hear voices and it can be wrong.",
           f"Sheets: {sheet_dir}", "",
           "Decide with `python3 pipeline/review.py approve @handle [level]` or `reject @handle \"reason\"`.", ""]
    out += section("Candidates waiting for you", pending, verdicts)
    if listed:
        out += section("Listed channels that now look wrong", worrying, verdicts)
        out.append(f"{len(listed) - len(worrying)} other listed channels raised nothing.")
    REPORT.write_text("\n".join(out) + "\n")
    print(f"{len(rows)} channels, {len(verdicts)} verdicts, {failed} failed sheet groups, {len(worrying)} listed channels flagged")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
