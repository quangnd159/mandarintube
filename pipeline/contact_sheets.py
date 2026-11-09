#!/usr/bin/env python3
"""Audit aid: a sheet of real mid-video frames per channel, for the by-eye AI check.

Usage: contact_sheets.py [--out DIR] [@handle ...]    all channels when none are named
"""
import concurrent.futures as cf
import io
import json
import pathlib
import sys
import urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "data/raw/sheets"
TW, TH, COLS, PER_SHEET = 200, 112, 6, 9
FONT = ImageFont.truetype("/Library/Fonts/Arial Unicode.ttf", 15)


def frame(vid):
    try:
        with urllib.request.urlopen(f"https://i.ytimg.com/vi/{vid}/hq2.jpg", timeout=20) as r:
            im = Image.open(io.BytesIO(r.read())).convert("RGB")
        w, h = im.size
        ch = int(w * 9 / 16)
        im = im.crop((0, (h - ch) // 2, w, (h + ch) // 2))
        return im.resize((TW, TH))
    except Exception:
        return Image.new("RGB", (TW, TH), (90, 90, 90))


def pick(videos):
    pub = [v for v in videos if not v.get("availability") and (v.get("duration") or 0) >= 90]
    recent = sorted(pub, key=lambda v: -(v.get("timestamp") or 0))[:4]
    ids = {v["id"] for v in recent}
    pop = [v for v in sorted(pub, key=lambda v: -(v.get("view_count") or 0)) if v["id"] not in ids][:2]
    return recent + pop


def main():
    args = sys.argv[1:]
    out = pathlib.Path(args.pop(args.index("--out") + 1)) if "--out" in args else OUT
    handles = {a.lower() for a in args if a != "--out"}
    out.mkdir(parents=True, exist_ok=True)
    cats = [json.loads(p.read_text()) for p in sorted((ROOT / "data/raw/catalog").glob("*.json"))]
    if handles:
        cats = [c for c in cats if (c.get("handle") or "").lower() in handles]
    index = []
    with cf.ThreadPoolExecutor(12) as ex:
        for s in range(0, len(cats), PER_SHEET):
            group = cats[s: s + PER_SHEET]
            sheet = Image.new("RGB", (TW * COLS, (TH + 22) * len(group)), "white")
            draw = ImageDraw.Draw(sheet)
            for row, c in enumerate(group):
                y = row * (TH + 22)
                draw.text((4, y + 1), f"{c['name']}  {c['handle']}  {len(c['videos'])}v", fill="black", font=FONT)
                for col, im in enumerate(ex.map(frame, [v["id"] for v in pick(c["videos"])])):
                    sheet.paste(im, (col * TW, y + 22))
                index.append(c["name"])
            sheet.save(out / f"sheet{s // PER_SHEET:02d}.jpg", quality=80)
    print(len(cats), "channels,", len(list(out.glob("*.jpg"))), "sheets")


if __name__ == "__main__":
    main()
