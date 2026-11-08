#!/usr/bin/env python3
"""Read YouTube's "How this was made" label and speech language from watch pages.

Usage: disclosure.py flagged   re-check videos the sampling step flagged
       disclosure.py site      check every video in site/data.json
Output: data/raw/disclosure.json  {video_id: label text, or null when there is no label}
        data/raw/speech.json      {video_id: [auto-caption languages]}
A failed fetch records nothing, so a re-run retries it rather than assuming "no label".

YouTube answers 429 if pages are fetched quickly, so this is deliberately slow: one page
at a time with a pause, waiting longer after each 429 and stopping after repeated ones.
Everything is saved as it goes, so a re-run continues where the last one stopped.
"""
import json
import pathlib
import random
import re
import sys
import time
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data/raw/disclosure.json"
SPEECH = ROOT / "data/raw/speech.json"
PAUSE = (2.5, 4.5)
BACKOFF = 600  # Seconds to wait after the first 429, doubling after each one in a row.
MAX_BACKOFFS = 5
# The bare class name also appears in a generic renderer list on some pages, so require
# the section object itself and read its body text.
SECTION = re.compile(r'"howThisWasMadeSectionViewModel":\{.{0,300}?"bodyText":\{"content":"([^"]+)"', re.S)
ASR = re.compile(r'"vssId":"a\.([\w-]+)"')


class RateLimited(Exception):
    pass


def check(video_id):
    """Returns (label, speech languages), or None when the page said nothing either way."""
    req = urllib.request.Request(f"https://www.youtube.com/watch?v={video_id}",
                                 headers={"User-Agent": "Mozilla/5.0", "Accept-Language": "en"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", "ignore")
    except urllib.error.HTTPError as e:
        if e.code == 429:
            raise RateLimited from e
        return None
    except OSError:
        return None
    if "ytInitialData" not in html:  # A consent or bot page says nothing either way.
        return None
    m = SECTION.search(html)
    return (m.group(1) if m else None), sorted(set(ASR.findall(html)))


def main():
    done = json.loads(OUT.read_text()) if OUT.exists() else {}
    speech = json.loads(SPEECH.read_text()) if SPEECH.exists() else {}
    if sys.argv[1] == "flagged":
        rows = [json.loads(f.read_text()) for f in (ROOT / "data/raw/signals").glob("*.json")]
        ids = [d["id"] for d in rows if d.get("ai_disclosed")]
    else:
        ids = [v[0] for v in json.loads((ROOT / "site/data.json").read_text())["videos"]]
    todo = [i for i in ids if i not in done or i not in speech]
    print(len(todo), "to check", flush=True)

    def save():
        OUT.write_text(json.dumps(done))
        SPEECH.write_text(json.dumps(speech))

    failed = checked = limited = 0
    i = 0
    while i < len(todo):
        try:
            result = check(todo[i])
        except RateLimited:
            limited += 1
            if limited > MAX_BACKOFFS:
                save()
                print(f"stopping after {limited} rate limits; {checked} checked, re-run to continue", flush=True)
                sys.exit(3)
            wait = BACKOFF * 2 ** (limited - 1)
            print(f"rate limited, waiting {wait}s", flush=True)
            save()
            time.sleep(wait)
            continue
        limited = 0
        if result is None:
            failed += 1
        else:
            done[todo[i]], speech[todo[i]] = result
            checked += 1
        i += 1
        if i % 25 == 0:
            save()
            print(i, "checked", failed, "failed", flush=True)
        time.sleep(random.uniform(*PAUSE))
    save()
    print("done, failed:", failed, flush=True)


if __name__ == "__main__":
    main()
