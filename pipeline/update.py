#!/usr/bin/env python3
"""Keep the site current without supervision. refresh.sh and the schedule both call this.

Usage: update.py run [--deploy]   new videos and Reddit posts, checks, titles, rebuild
       update.py discover         find new candidate channels and write the review report
       update.py accept           publish a run that the safety check stopped, after looking at it
       update.py tick             what the schedule calls: does whichever job is due
       update.py status           when each job last ran and how it went

Every step resumes, so a failed run retries from where it stopped at the next tick.
Reports: data/raw/update_report.md and data/raw/logs/. State: data/raw/update_state.json.
"""
import datetime as dt
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
PIPE = ROOT / "pipeline"
SITE_DATA = ROOT / "site/data.json"
PUBLISHED = RAW / "published.json"  # A copy of what was last deployed, to compare against.
STATE = RAW / "update_state.json"
REPORT = RAW / "update_report.md"
LOCK = RAW / "update.lock"
LIVE_URL = "https://mandarintube.dqnotes.com/data.json"
WRANGLER = ["npx", "--yes", "wrangler@4.45.0", "deploy"]
COMMIT_PATHS = ["site/data.json", "data/titles_vi.json", "data/channels.json"]
KEYCHAIN_ITEM = "mandarintube-claude-token"

DAY = 86400
RUN_EVERY = 30 * DAY
DISCOVER_EVERY = 90 * DAY
RETRY_AFTER = 20 * 3600
MAX_VIDEO_DROP = 0.10
MAX_CHANNELS_LOST = 2
MAX_UNCHECKED = 0.01  # Share of listed videos allowed without a finished AI label check.
RATE_LIMITED = 3  # disclosure.py's exit code.


class StepFailed(Exception):
    pass


class RateLimited(Exception):
    pass


def log(message, stream=None):
    line = f"{time.strftime('%H:%M:%S')} {message}"
    print(line, flush=True)
    if stream:
        stream.write(line + "\n")
        stream.flush()


class Job:
    def __init__(self, name):
        (RAW / "logs").mkdir(parents=True, exist_ok=True)
        self.log = (RAW / "logs" / f"{dt.date.today().isoformat()}-{name}.log").open("a")

    def step(self, *args, required=True, ok_codes=(0,)):
        """Runs a pipeline script, streaming its output to the log. Returns the exit code."""
        cmd = [sys.executable, "-u", str(PIPE / args[0]), *args[1:]]
        log("▶ " + " ".join(args), self.log)
        p = subprocess.run(cmd, stdout=self.log, stderr=subprocess.STDOUT, cwd=ROOT)
        if p.returncode not in ok_codes and required:
            raise StepFailed(f"{args[0]} exited with code {p.returncode}")
        if p.returncode not in ok_codes:
            log(f"  {args[0]} exited with code {p.returncode}, carrying on", self.log)
        return p.returncode


def read_json(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def save_state(**changes):
    state = read_json(STATE, {}) | changes
    STATE.write_text(json.dumps(state, indent=1))
    return state


def notify(title, message):
    script = 'on run argv\ndisplay notification (item 2 of argv) with title (item 1 of argv)\nend run'
    subprocess.run(["osascript", "-e", script, title, message], capture_output=True)


def check_changes(old, new, reviewed, handles_of_new=None):
    """Compares a new build with what's live. Returns (reasons to stop, things to report)."""
    stops, notes = [], []
    old_ch = {c["id"]: c for c in old.get("channels", [])}
    new_ch = {c["id"]: c for c in new.get("channels", [])}
    old_ids = {v[0] for v in old.get("videos", [])}
    new_ids = {v[0] for v in new.get("videos", [])}
    if not new_ch or not new_ids:
        return ["The new build has no channels or no videos."], notes

    lost = [old_ch[c]["name"] for c in old_ch.keys() - new_ch.keys()]
    gained = [new_ch[c] for c in new_ch.keys() - old_ch.keys()]
    if lost:
        notes.append("Channels removed: " + ", ".join(sorted(lost)))
    if len(lost) > MAX_CHANNELS_LOST:
        stops.append(f"{len(lost)} channels would disappear: {', '.join(sorted(lost))}.")
    for c in gained:
        key = "@" + c["key"].lstrip("@")
        if not c.get("seed") and key.lower() not in reviewed:
            stops.append(f"{c['name']} would be listed without a review.")
    if gained:
        notes.append("Channels added: " + ", ".join(sorted(c["name"] for c in gained)))
    if old_ids and len(new_ids) < len(old_ids) * (1 - MAX_VIDEO_DROP):
        stops.append(f"Listed videos would fall from {len(old_ids)} to {len(new_ids)}.")
    stats = new.get("stats", {})
    unchecked = len(new_ids) - stats.get("labelChecked", 0)
    if unchecked > len(new_ids) * MAX_UNCHECKED:
        stops.append(f"{unchecked} of {len(new_ids)} listed videos haven't had their AI label checked.")
    untranslated = sum(1 for v in new.get("videos", []) if not v[9])
    if untranslated:
        notes.append(f"{untranslated} titles have no Vietnamese translation and show the original.")
    notes.append(f"Videos: {len(old_ids)} → {len(new_ids)} ({len(new_ids - old_ids)} added, {len(old_ids - new_ids)} removed). "
                 f"Channels: {len(old_ch)} → {len(new_ch)}.")
    return stops, notes


def reviewed_handles():
    review = read_json(ROOT / "data/review.json", {})
    return {k.lower() for k in review.get("reviewed", {})}


def baseline():
    return read_json(PUBLISHED, None) or read_json(SITE_DATA, {})


def write_report(heading, stops, notes, extra=()):
    lines = [f"# {heading}", "", f"{dt.datetime.now():%Y-%m-%d %H:%M}", ""]
    if stops:
        lines += ["## Stopped before publishing", ""] + [f"- {s}" for s in stops] + [
            "", "If this looks right, publish it with `python3 pipeline/update.py accept`.", ""]
    if notes:
        lines += ["## What changed", ""] + [f"- {n}" for n in notes] + [""]
    lines += list(extra)
    REPORT.write_text("\n".join(lines) + "\n")


def build_and_check_labels(job):
    """Removing a labelled video lets another in, so repeat until the list settles."""
    previous = None
    for _ in range(4):
        job.step("build.py")
        listed = {v[0] for v in read_json(SITE_DATA, {}).get("videos", [])}
        if listed == previous:
            return
        previous = listed
        if job.step("disclosure.py", "site", ok_codes=(0, RATE_LIMITED)) == RATE_LIMITED:
            job.step("build.py")
            raise RateLimited
    job.step("build.py")


def deploy(job):
    log("▶ deploy", job.log)
    p = subprocess.run(WRANGLER, stdout=job.log, stderr=subprocess.STDOUT, cwd=ROOT)
    if p.returncode:
        raise StepFailed(f"Deploying failed with code {p.returncode}")
    shutil.copyfile(SITE_DATA, PUBLISHED)
    return verify_live()


def verify_live():
    """Returns a warning if the live site doesn't serve what was just built."""
    want = read_json(SITE_DATA, {})
    req = urllib.request.Request(f"{LIVE_URL}?check={int(time.time())}", headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            got = json.load(r)
    except (OSError, ValueError) as e:
        return f"Couldn't read the live site back: {e!r}"
    if len(got.get("videos", [])) != len(want.get("videos", [])) or got.get("built") != want.get("built"):
        return "The live site doesn't match the new build yet. It may just be cached."
    return None


def commit(job, message):
    """Commits only the data files, on main, and never pushes."""
    git = lambda *a: subprocess.run(["git", *a], cwd=ROOT, capture_output=True, text=True, timeout=120)
    branch = git("branch", "--show-current").stdout.strip()
    if branch != "main":
        log(f"  on {branch or 'a detached HEAD'}, not main, so the data wasn't committed", job.log)
        return
    changed = git("status", "--porcelain", "--", *COMMIT_PATHS).stdout.strip()
    if not changed:
        return
    p = git("commit", "-m", message, "--", *COMMIT_PATHS)
    log(("  committed: " + message) if p.returncode == 0 else f"  commit failed: {p.stderr[-200:]}", job.log)


def run(publish):
    job = Job("run")
    old = baseline()
    job.step("catalog.py", "--force")
    job.step("corpus.py", "sync", required=False)  # The archive being down shouldn't block new videos.
    job.step("candidates.py", required=False)  # Resolves newly linked videos to their channels.
    job.step("signals.py")
    job.step("mentions.py")
    job.step("disclosure.py", "flagged", ok_codes=(0, RATE_LIMITED))
    build_and_check_labels(job)
    job.step("titles.py", "auto", required=False)
    job.step("build.py")

    new = read_json(SITE_DATA, {})
    stops, notes = check_changes(old, new, reviewed_handles())
    waiting = sum(a["status"] == "pending-review" for a in read_json(ROOT / "data/audit.json", []))
    if waiting:
        notes.append(f"{waiting} candidate channels are waiting for your review: see data/raw/review_report.md.")
    if stops:
        write_report("Update held for review", stops, notes)
        save_state(held=True, last_attempt=time.time(), last_result="held")
        notify("MandarinTube update held", stops[0])
        log("HELD: " + " ".join(stops), job.log)
        return 2
    warning = None
    if publish:
        warning = deploy(job)
        if warning:
            notes.append(warning)
        commit(job, f"Refresh the catalog, {new.get('built')}")
    write_report("Update published" if publish else "Update built, not published", [], notes)
    if publish:
        save_state(held=False, last_success=time.time(), last_attempt=time.time(), last_result="published")
        notify("MandarinTube updated", notes[-1] if not waiting else f"{waiting} channels are waiting for your review.")
    else:  # Nothing went live, so the next scheduled publish stays due.
        save_state(last_result="built, not published")
    log("done: " + " ".join(notes), job.log)
    return 0


def accept():
    job = Job("accept")
    warning = deploy(job)
    commit(job, f"Refresh the catalog, {read_json(SITE_DATA, {}).get('built')}")
    save_state(held=False, last_success=time.time(), last_attempt=time.time(), last_result="published")
    log("published" + (f", but: {warning}" if warning else ""), job.log)
    return 0


def discover():
    job = Job("discover")
    job.step("discover.py", required=False)
    job.step("candidates.py", required=False)
    job.step("shortlist.py")
    job.step("catalog.py")  # Only fetches channels not seen before.
    job.step("signals.py")
    job.step("mentions.py")
    job.step("disclosure.py", "flagged", ok_codes=(0, RATE_LIMITED))
    job.step("build.py")
    job.step("frame_review.py", "--listed", required=False)
    save_state(last_discovery=time.time())
    waiting = sum(a["status"] == "pending-review" for a in read_json(ROOT / "data/audit.json", []))
    notify("MandarinTube channel review ready", f"{waiting} candidates. See data/raw/review_report.md.")
    log(f"done: {waiting} candidates waiting", job.log)
    return 0


def online():
    try:
        urllib.request.urlopen(urllib.request.Request("https://www.youtube.com/", headers={"User-Agent": "Mozilla/5.0"}), timeout=20)
        return True
    except OSError:
        return False


def due(state, now):
    """Which jobs to do now. A held run waits for a person, and failures retry daily."""
    jobs = []
    if now - state.get("last_attempt", 0) < RETRY_AFTER:
        return jobs
    if not state.get("held") and now - state.get("last_success", 0) >= RUN_EVERY:
        jobs.append("run")
    if now - state.get("last_discovery", 0) >= DISCOVER_EVERY:
        jobs.append("discover")
    return jobs


def locked(fn):
    """One job at a time. The lock names its process, so a crash can't block later runs."""
    if LOCK.exists():
        try:
            os.kill(int(LOCK.read_text()), 0)
            log("another update is running")
            return 0
        except (ValueError, ProcessLookupError):
            pass
    LOCK.write_text(str(os.getpid()))
    try:
        return fn()
    finally:
        LOCK.unlink(missing_ok=True)


def guarded(name, fn):
    """Runs a job, turning its failure into a saved state and a notification."""
    try:
        return fn()
    except RateLimited:
        save_state(last_attempt=time.time(), last_result="rate limited")
        log(f"{name}: YouTube is rate limiting. It will carry on at the next tick.")
        return 3
    except Exception as e:  # An unattended job has to report anything that goes wrong.
        save_state(last_attempt=time.time(), last_result=f"failed: {e}")
        notify("MandarinTube update failed", str(e)[:180])
        log(f"{name} failed: {e!r}")
        return 1


def tick():
    state = read_json(STATE, {})
    jobs = due(state, time.time())
    if not jobs:
        log("nothing due")
        return 0
    if not online():
        log("offline, trying later")
        return 0
    code = 0
    if "run" in jobs:
        code = guarded("update", lambda: run(publish=True))
    if "discover" in jobs and code == 0:
        code = guarded("discovery", discover)
    return code


def status():
    state = read_json(STATE, {})
    for key in ("last_success", "last_attempt", "last_discovery"):
        print(f"{key}: {dt.datetime.fromtimestamp(state[key]):%Y-%m-%d %H:%M}" if key in state else f"{key}: never")
    print("last_result:", state.get("last_result", "none"))
    print("held for review:", bool(state.get("held")))
    print("report:", REPORT if REPORT.exists() else "none yet")
    return 0


def load_claude_token():
    """A long-lived token from the Keychain, since an ordinary sign-in expires within days.
    Without one, `claude -p` uses the sign-in, and a failure leaves titles untranslated."""
    if os.environ.get("CLAUDE_CODE_OAUTH_TOKEN"):
        return
    p = subprocess.run(["security", "find-generic-password", "-s", KEYCHAIN_ITEM, "-w"], capture_output=True, text=True)
    if p.returncode == 0 and p.stdout.strip():
        os.environ["CLAUDE_CODE_OAUTH_TOKEN"] = p.stdout.strip()


def main():
    args = sys.argv[1:]
    command = args[0] if args else ""
    load_claude_token()
    if command == "status":
        return status()
    if command == "tick":
        return locked(tick)
    if command == "run":
        return locked(lambda: guarded("update", lambda: run("--deploy" in args)))
    if command == "discover":
        return locked(lambda: guarded("discovery", discover))
    if command == "accept":
        return locked(lambda: guarded("publish", accept))
    sys.exit(__doc__)


if __name__ == "__main__":
    sys.exit(main())
