#!/usr/bin/env python3
"""Vietnamese video titles, translated once and stored by video ID.

Usage: titles.py todo [batch size]  write untranslated titles to data/raw/titles/batch_NN.json
       titles.py merge              check data/raw/titles/out_NN.json, keep what passes

Translate each batch following pipeline/titles_prompt.md into out_NN.json as {video_id: title}.
Output: data/titles_vi.json. Build falls back to the original title for anything missing.
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
STORE = ROOT / "data/titles_vi.json"
WORK = ROOT / "data/raw/titles"
VIETNAMESE = re.compile(r"[àáảãạăằắẳẵặâầấẩẫậèéẻẽẹêềếểễệìíỉĩịòóỏõọôồốổỗộơờớởỡợùúủũụưừứửữựỳýỷỹỵđ]", re.I)
LEFTOVER = re.compile(r"#[^\W\d]|\bcc\b|\bsubs?\b", re.I)
TOPIC_ONLY = re.compile(r"comprehensible|\btprs\b", re.I)  # Fine when it's the subject, so reported rather than rejected.
CJK = re.compile(r"[一-鿿]")


def store():
    return json.loads(STORE.read_text()) if STORE.exists() else {}


def listed():
    return {v[0]: v[2] for v in json.loads((ROOT / "site/data.json").read_text())["videos"]}


def todo(size):
    WORK.mkdir(parents=True, exist_ok=True)
    have = store()
    rows = [{"id": k, "t": t} for k, t in listed().items() if k not in have]
    for old in WORK.glob("batch_*.json"):
        old.unlink()
    for n, i in enumerate(range(0, len(rows), size)):
        (WORK / f"batch_{n:02d}.json").write_text(json.dumps(rows[i:i + size], ensure_ascii=False, indent=0))
    print(len(rows), "titles to translate")


def problems(source, vi):
    if not isinstance(vi, str) or not vi.strip():
        return "empty"
    if LEFTOVER.search(vi):
        return "leftover keyword"
    # A bare proper name, such as a game title, rightly stays as it is.
    squash = lambda x: re.sub(r"\s", "", x).lower()
    if not VIETNAMESE.search(vi) and not CJK.search(vi) and squash(vi) not in squash(source):
        return "no Vietnamese"
    if len(vi) > 130:
        return "too long"
    return None


def merge():
    have, src = store(), listed()
    bad, warn, topical, added = [], [], [], 0
    for f in sorted(WORK.glob("out_*.json")):
        for k, vi in json.loads(f.read_text()).items():
            if k not in src:
                bad.append((k, "unknown id", vi))
                continue
            p = problems(src[k], vi)
            if p:
                bad.append((k, p, f"{src[k]} => {vi}"))
                continue
            # Levels are dropped on purpose, and "EP01" may become "tập 1".
            head = re.sub(r"#[^\W\d]\S*|hsk\s*\d?[\d\s,/&+~–—-]*(?:hsk\s*\d+)*|\b[abc][12]\b", "", src[k], flags=re.I)
            kept = {n.lstrip("0") for n in re.findall(r"\d+", vi)}
            lost = [n for n in re.findall(r"\d+", head) if n.lstrip("0") and n.lstrip("0") not in kept]
            if lost:
                warn.append((k, lost, f"{src[k]} => {vi}"))
            if TOPIC_ONLY.search(vi):
                topical.append(f"{src[k]} => {vi}")
            added += k not in have
            have[k] = vi.strip()
    STORE.write_text(json.dumps(dict(sorted(have.items())), ensure_ascii=False, indent=0))
    print(f"stored {len(have)}, new {added}, rejected {len(bad)}, missing {len(set(src) - set(have))}, number warnings {len(warn)}")
    for row in bad[:40]:
        print("REJECT", *row)
    for row in warn[:40]:
        print("NUMBER", *row)
    for row in topical[:40]:
        print("CHECK", row)


if __name__ == "__main__":
    if sys.argv[1] == "todo":
        todo(int(sys.argv[2]) if len(sys.argv) > 2 else 280)
    else:
        merge()
