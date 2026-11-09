#!/usr/bin/env python3
"""Step 6: combine all evidence into site/data.json and data/audit.json.

Channel score = learners who keep recommending it (Reddit)
              + fans shared with the starting channels (YouTube comments)
              + commenters who come back to several videos (YouTube comments)
Nothing personal is published: the output holds aggregates and links only.
"""
import collections
import datetime as dt
import json
import math
import pathlib
import re
import statistics as st
import time
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw"
TODAY = dt.date.today().isoformat()
NOW = dt.datetime.now(dt.timezone.utc).timestamp()

SELF = re.compile(r"\b(my|our) (own )?(youtube |yt )?(channel|video|videos|podcast|lesson|lessons)\b"
                  r"|\bi (made|created|started|uploaded|run|teach)\b|\bwe (made|created|started|run)\b"
                  r"|\bsubscribe to (my|our)\b|\bi'm the (creator|teacher|host)\b", re.I)
AI_TALK = re.compile(r"\b(ai[- ]generated|ai[- ]voice|ai voices|robot(ic)? voice|text[- ]to[- ]speech|tts voice|synthetic voice|sounds? like (an? )?(ai|robot)|is this ai|ai slop)\b"
                     r"|ai生成|人工智能生成|机器人的声音|机器人声音", re.I)
PRAISE = re.compile(r"\b(recommend|love|great|awesome|amazing|excellent|helpful|favou?rite|best|fantastic|really good|so good|wonderful|underrated|perfect)\b", re.I)
FILLERS = re.compile(r"嗯|呃|啊|那个|就是|对吧|然后|其实|怎么说|哈哈|对对|是吧|这个这个")
VIDEO_LINK = re.compile(r"(?:youtube\.com/(?:watch\?(?:[^\s)\]]*&)?v=|embed/|live/|shorts/)|youtu\.be/)([\w-]{11})")
HANDLE_LINK = re.compile(r"youtube\.com/@([\w.\-%]+)")
CHANNEL_LINK = re.compile(r"youtube\.com/channel/(UC[\w-]{22})")


def measure_caption(text, duration):
    """Speaking rate and spoken-filler rate. Used for the speed shown to learners and
    the AI audit, not for levels: cross-validated against teacher labels on unseen
    channels, transcript vocabulary predicted level no better than a constant guess."""
    cjk = len(re.findall(r"[\u4e00-\u9fff]", text))
    if cjk < 120 or not duration:
        return None
    return {"cpm": cjk / duration * 60, "fillers": len(FILLERS.findall(text)) / cjk * 1000, "chars": cjk}


def hsk_to_band(h):
    return 1 if h <= 2.5 else 2 if h <= 3.5 else 3 if h <= 5.5 else 4


def title_level(title):
    """The teacher's own label. Returns (band, is_explicit_hsk_or_cefr) or None."""
    t = title.lower()
    m = re.search(r"hsk\s*(\d)(?:\s*[-–—~/+&到至]+\s*(?:hsk\s*)?(\d))?", t)
    if m:
        a, b = int(m[1]), int(m[2] or m[1])
        if 1 <= a <= 9 and 1 <= b <= 9:
            return hsk_to_band((a + b) / 2), True
    m = re.search(r"\b([abc][12])\b", t)
    if m:
        return {"a1": 1, "a2": 1, "b1": 2, "b2": 3, "c1": 4, "c2": 4}[m[1]], True
    if re.search(r"upper[- ]?intermediate|中高级", t):
        return 3, False
    if re.search(r"advanced[- ]?beginner|high[- ]?beginner|lower[- ]?intermediate|beginner[- /]+intermediate|pre[- ]?intermediate|初中级", t):
        return 2, False
    if re.search(r"(?<!upper )(?<!lower )intermediate|中级", t):
        return 3, False
    if re.search(r"\badvanced\b|高级", t):
        return 4, False
    if re.search(r"beginner|elementary|零基础|初级|入门|from scratch", t):
        return 1, False
    return None


def norm(s):
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def pct_ranks(values):
    """value -> 0..1 share of channels it beats. Ties share a rank."""
    ordered = sorted(values)
    n = max(1, len(ordered) - 1)
    return {v: (sum(1 for x in ordered if x < v)) / n for v in set(values)}


def load_channels():
    review = json.loads((ROOT / "data/review.json").read_text())
    seeds = {e["url"].split("youtube.com/")[-1].lower() for e in json.loads((ROOT / "data/channels.json").read_text()) if e.get("seed")}
    # Reasons and verification notes stay local. Without them a channel is simply left out.
    notes_path = RAW / "review_notes.json"
    notes = json.loads(notes_path.read_text()) if notes_path.exists() else {}
    reasons = {k.lower(): v for k, v in notes.get("exclude", {}).items()}
    verify = {k.lower(): v for k, v in notes.get("verify", {}).items()}
    excl = {k.lower(): reasons.get(k.lower(), {"kind": "other", "reason": "Left out after review."}) for k in review["exclude"]}
    out = {}
    for f in sorted((RAW / "catalog").glob("*.json")):
        d = json.loads(f.read_text())
        d["seed"] = (d.get("handle") or "").lower() in seeds
        d["excluded"] = excl.get((d.get("handle") or "").lower())
        d["verify"] = verify.get((d.get("handle") or "").lower())
        out[d["channel_id"]] = d
    return out


def reddit_evidence(channels):
    """Per channel: distinct people and threads recommending it, without self-promotion."""
    handle_to_id = {(c.get("handle") or "").lower().lstrip("@"): cid for cid, c in channels.items()}
    oembed = json.loads((RAW / "oembed.json").read_text()) if (RAW / "oembed.json").exists() else {}
    hits = collections.defaultdict(dict)
    # Named mentions
    for f in (RAW / "mentions").glob("*.json"):
        d = json.loads(f.read_text())
        if d["channel_id"] in channels:
            for r in d["hits"]:
                hits[d["channel_id"]][r["id"]] = r
    # Links in the broad harvest
    if (RAW / "reddit.jsonl").exists():
        for line in (RAW / "reddit.jsonl").open():
            r = json.loads(line)
            text = " ".join(str(r.get(k) or "") for k in ("body", "selftext", "title", "url"))
            targets = set()
            for v in VIDEO_LINK.findall(text):
                url = (oembed.get(v) or {}).get("url") or ""
                targets.add(handle_to_id.get(url.split("youtube.com/")[-1].lower().lstrip("@")))
            for h in HANDLE_LINK.findall(text):
                targets.add(handle_to_id.get(urllib.parse.unquote(h).lower()))
            for cid in CHANNEL_LINK.findall(text):
                targets.add(cid if cid in channels else None)
            for cid in targets - {None}:
                hits[cid].setdefault(r["id"], r)

    # Someone repeatedly plugging one channel from many threads is treated as promotion.
    per_author = collections.defaultdict(lambda: collections.defaultdict(set))
    for cid, rows in hits.items():
        for r in rows.values():
            per_author[r.get("author")][cid].add(r.get("link_id") or r["id"])

    result = {}
    for cid, c in channels.items():
        people, threads, years, quotes, dropped = set(), set(), [], [], collections.Counter()
        names = {norm(c.get("name")), norm(c.get("handle"))}
        for r in hits.get(cid, {}).values():
            author = r.get("author") or "[deleted]"
            text = " ".join(str(r.get(k) or "") for k in ("body", "title", "selftext"))
            na = norm(author)
            if author in ("[deleted]", "AutoModerator"):
                dropped["deleted"] += 1; continue
            if (r.get("score") or 0) < 1:
                dropped["downvoted"] += 1; continue
            if SELF.search(text):
                dropped["self"] += 1; continue
            if len(na) >= 4 and any(na in n or (n and n in na) for n in names):
                dropped["owner"] += 1; continue
            if r["kind"] == "post" and "youtu" in (r.get("url") or ""):
                dropped["link_post"] += 1; continue
            if len(per_author[author][cid]) >= 6:
                dropped["promoter"] += 1; continue
            people.add(author)
            threads.add(r.get("link_id") or r["id"])
            year = dt.datetime.fromtimestamp(int(r["created_utc"]), dt.timezone.utc).year
            years.append(year)
            body = (r.get("body") or "").strip()
            if r["kind"] == "comment" and 40 <= len(body) <= 300 and PRAISE.search(body) and r.get("permalink"):
                quotes.append({"text": re.sub(r"\s+", " ", re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", body)),
                               "url": "https://www.reddit.com" + r["permalink"], "year": year, "score": r.get("score") or 0})
        quotes.sort(key=lambda q: -q["score"])
        result[cid] = {"people": len(people), "threads": len(threads), "years": len(set(years)),
                       "first": min(years) if years else None, "last": max(years) if years else None,
                       "quotes": quotes[:6], "dropped": dict(dropped), "authors": people}
    return result


def youtube_evidence(channels):
    """Commenters, shared fans, loyalty, captions and AI markers from the sampled videos."""
    sigs = collections.defaultdict(list)
    for f in (RAW / "signals").glob("*.json"):
        d = json.loads(f.read_text())
        if d.get("channel") in channels:
            sigs[d["channel"]].append(d)
    commenters = {}
    out = {}
    for cid, videos in sigs.items():
        seen = collections.Counter()
        for v in videos:
            for a in {c["a"] for c in v["comments"] if not c["u"]}:
                seen[a] += 1
        commenters[cid] = seen
    seed_ids = [cid for cid, c in channels.items() if c["seed"]]
    for cid, videos in sigs.items():
        seen = commenters[cid]
        others = set().union(*[set(commenters.get(s, {})) for s in seed_ids if s != cid]) if seed_ids else set()
        shared = len(set(seen) & others)
        measures, ai_talk = [], []
        for v in videos:
            cap = RAW / "captions" / f"{v['id']}.txt"
            if cap.exists():
                m = measure_caption(cap.read_text(), v.get("duration") or 0)
                if m:
                    m.update(id=v["id"], manual=v.get("manual_captions"))
                    measures.append(m)
            ai_talk += [c["t"][:200] for c in v["comments"] if not c["u"] and AI_TALK.search(c["t"])]
        out[cid] = {
            "sampled": len(videos), "commenters": len(seen), "shared": shared,
            "fanShare": shared / (len(seen) + 20),  # The +20 stops tiny samples scoring as certainties.
            "loyal": sum(1 for n in seen.values() if n >= 2) / (len(seen) + 20),
            "ai_disclosed": sum(1 for v in videos if is_ai_label(DISCLOSURE.get(v["id"]))),
            "ai_talk": ai_talk[:8],
            "embed_blocked": sum(1 for v in videos if v.get("playable_embed") is False),
            "likes_per_k": st.median([v["likes"] / v["views"] * 1000 for v in videos if v.get("likes") and v.get("views")] or [0]),
            "measures": measures,
            "cpm": st.median([m["cpm"] for m in measures]) if measures else None,
            "fillers": st.median([m["fillers"] for m in measures]) if measures else None,
        }
    return out


# This is a listening library. Drills and lessons about Mandarin in English don't belong,
# even from a good channel, because they aren't time spent hearing the language.
NEVER_LISTENING = re.compile(
    r"vocabulary (quick )?(review|course|builder|building)|new words lesson|words? (&|and) sentence|flashcard|"
    r"\bmock test\b|\bpractice test\b|\bhsk\b.*\btest\b|\btest\b.*\bhsk\b|test[- ]?hsk|introduction to hsk|hskk|hsk.*(listening|reading|writing) part|\bkaraoke\b|\bktv\b|"
    r"\btrailer\b|announcement|channel update|giveaway|live ?stream", re.I)
MAYBE_NOT = re.compile(
    r"pronunciation|pinyin|alphabet|\btones?\b|initials|finals|vocab(ulary)?\b|\bgrammar\b|characters? (lesson|writing)|stroke|"
    r"how to (learn|study|improve|say|use)|\btips\b|mistakes|\bexam\b|\bsong\b|\bmusic\b", re.I)
# A title that also says it's a story, podcast or similar is talking in Mandarin after all.
IS_LISTENING = re.compile(r"comprehensible|\bci\b|\btprs\b|stor(y|ies)|podcast|vlog|conversation|interview|immersion|slow chinese|listening|shadowing", re.I)


def is_listening(title):
    if NEVER_LISTENING.search(title):
        return False
    return not MAYBE_NOT.search(title) or bool(IS_LISTENING.search(title))


def is_ai_label(label):
    """YouTube's generated-content label. "Audio tracks ... automatically generated" is
    only auto-dubbing into other languages, and says nothing about the original video."""
    return bool(label) and "altered or fully generated" in label


DISCLOSURE = json.loads((RAW / "disclosure.json").read_text()) if (RAW / "disclosure.json").exists() else {}


def english_spoken():
    """Videos whose only auto-caption track is English, which means YouTube heard English."""
    out = set()
    if (RAW / "speech.json").exists():
        out |= {k for k, v in json.loads((RAW / "speech.json").read_text()).items() if len(v) == 1 and v[0].startswith("en")}
    for f in (RAW / "signals").glob("*.json"):
        d = json.loads(f.read_text())
        orig = d.get("auto_orig") or []
        if len(orig) == 1 and orig[0].startswith("en"):
            out.add(d["id"])
    return out


ENGLISH = english_spoken()
TITLES_VI = json.loads((ROOT / "data/titles_vi.json").read_text()) if (ROOT / "data/titles_vi.json").exists() else {}


def video_pool(c):
    return [v for v in c["videos"] if not v.get("availability") and (v.get("duration") or 0) >= 90
            and is_listening(v.get("title") or "") and not is_ai_label(DISCLOSURE.get(v["id"])) and v["id"] not in ENGLISH]


def age_adjusted(videos):
    """How far each video's views sit above what its age predicts, within its channel."""
    pts = [(math.log1p(max(1, (NOW - v["timestamp"]) / 86400)), math.log1p(v["view_count"]), v["id"])
           for v in videos if v.get("view_count") and v.get("timestamp")]
    if len(pts) < 5:
        return {p[2]: 0.0 for p in pts}
    mx, my = st.mean(p[0] for p in pts), st.mean(p[1] for p in pts)
    den = sum((p[0] - mx) ** 2 for p in pts) or 1
    slope = sum((p[0] - mx) * (p[1] - my) for p in pts) / den
    res = {p[2]: p[1] - (my + slope * (p[0] - mx)) for p in pts}
    sd = st.pstdev(res.values()) or 1
    return {k: max(-2.5, min(2.5, r / sd)) for k, r in res.items()}


def quotes_for(c):
    """Only quotes that were read and picked: data/quotes.json, chosen from audit.json."""
    path = ROOT / "data/quotes.json"
    all_quotes = json.loads(path.read_text()) if path.exists() else {}
    return all_quotes.get((c.get("handle") or "").lower(), [])


def main():
    channels = load_channels()
    reddit = reddit_evidence(channels)
    yt = youtube_evidence(channels)

    rows = []
    for cid, c in channels.items():
        r, y = reddit[cid], yt.get(cid, {})
        recommend = math.log1p(r["people"]) * (1 + 0.12 * min(r["years"], 6)) + 0.25 * math.log1p(r["threads"])
        rows.append({"cid": cid, "c": c, "r": r, "y": y, "recommend": recommend,
                     "fan": y.get("fanShare", 0.0), "loyal": y.get("loyal", 0.0)})

    # Scored against eligible channels only, so excluded ones can't distort the scale.
    eligible = [x for x in rows if not x["c"]["excluded"]]
    pr, pf, pl = (pct_ranks([x[k] for x in eligible]) for k in ("recommend", "fan", "loyal"))
    for x in eligible:
        x["score"] = 0.5 * pr[x["recommend"]] + 0.35 * pf[x["fan"]] + 0.15 * pl[x["loyal"]]
        # Starting channels define the taste being matched, so evidence can't sink them.
        if x["c"]["seed"]:
            x["score"] = max(x["score"], 0.6)

    # Inclusion: start from what the user loves, otherwise demand independent evidence.
    audit = []
    keep = []
    for x in sorted(rows, key=lambda x: -x.get("score", -1)):
        c, r, y = x["c"], x["r"], x["y"]
        status, why = "kept", ""
        if c["excluded"]:
            status, why = "excluded-" + c["excluded"]["kind"], c["excluded"]["reason"]
        elif not c["seed"] and not (r["people"] >= 3 or y.get("shared", 0) >= 5):
            status, why = "excluded-evidence", f"{r['people']} Reddit recommenders, {y.get('shared', 0)} shared fans."
        elif y.get("ai_disclosed", 0) > 0:
            status, why = "excluded-ai", f"YouTube's AI disclosure label on {y['ai_disclosed']} sampled videos."
        audit.append({"name": c["name"], "handle": c["handle"], "id": x["cid"], "status": status, "why": why, "verify": c.get("verify"),
                      "score": round(x.get("score", 0), 3), "people": r["people"], "threads": r["threads"], "first": r["first"], "last": r["last"],
                      "years": r["years"], "dropped": r["dropped"], "sampled": y.get("sampled"), "commenters": y.get("commenters"), "shared": y.get("shared"),
                      "fanShare": round(y.get("fanShare", 0), 3), "loyal": round(y.get("loyal", 0), 3), "cpm": y.get("cpm"),
                      "fillers": y.get("fillers"), "captions": len(y.get("measures", [])), "ai_talk": y.get("ai_talk", []),
                      "ai_disclosed": y.get("ai_disclosed"), "embed_blocked": y.get("embed_blocked"), "followers": c.get("followers"), "videos": len(c["videos"]),
                      "first_video": dt.date.fromtimestamp(min((v["timestamp"] for v in c["videos"] if v.get("timestamp")), default=NOW)).isoformat(),
                      "last_year_uploads": sum(1 for v in c["videos"] if v.get("timestamp") and NOW - v["timestamp"] < 365 * 86400),
                      "quotes": r["quotes"]})
        if status == "kept":
            keep.append(x)
    (ROOT / "data/audit.json").write_text(json.dumps(audit, ensure_ascii=False, indent=1))

    # Level per video: the teacher's label in the title, else the channel's most common
    # label, else a published level from data/review.json. Unknown stays unknown.
    review = json.loads((ROOT / "data/review.json").read_text())
    hand_levels = {k.lower(): v for k, v in review.get("levels", {}).items()}
    only_titles = {k.lower(): v for k, v in review.get("only_titles", {}).items()}
    videos_out, channels_out = [], []
    for rank, x in enumerate(keep):
        c, r, y = x["c"], x["r"], x["y"]
        pool = video_pool(c)
        only = only_titles.get((c.get("handle") or "").lower())
        if only:
            pool = [v for v in pool if re.search(only, v.get("title") or "", re.I)]
        labelled = [title_level(v["title"] or "") for v in c["videos"]]
        labelled = collections.Counter(lab[0] for lab in labelled if lab)
        if sum(labelled.values()) >= 5:
            channel_band = labelled.most_common(1)[0][0]
        else:
            channel_band = hand_levels.get((c.get("handle") or "").lower())
        adj = age_adjusted(pool)
        cap = max(40, min(160, int(160 * (x["score"] ** 1.3)))) if not c["seed"] else 200
        ranked = sorted(pool, key=lambda v: -adj.get(v["id"], 0))[:cap]
        bands = collections.Counter()
        for v in ranked:
            lab = title_level(v["title"] or "")
            band, src = (lab[0], 1) if lab else (channel_band or 0, 0)
            bands[band] += 1
            # Blend the channel's standing with this video's standing inside its channel.
            s = 0.65 * x["score"] + 0.35 * (adj.get(v["id"], 0) + 2.5) / 5
            videos_out.append([v["id"], rank, v["title"], int(v["duration"]), v.get("view_count") or 0,
                               int(v.get("timestamp") or 0), band, src, round(s, 4), TITLES_VI.get(v["id"], "")])
        channels_out.append({
            "id": x["cid"], "key": (c.get("handle") or x["cid"]).lstrip("@"), "name": c["name"], "seed": c["seed"],
            "people": r["people"], "threads": r["threads"], "first": r["first"], "last": r["last"],
            "fanShare": None if c["seed"] or not y.get("commenters") else round(y["shared"] / max(1, y["commenters"]), 3),
            "count": len(ranked), "mainLevel": max((b for b in bands if b), key=lambda b: bands[b], default=None),
            "cpm": round(y["cpm"], -1) if y.get("cpm") else None, "quotes": quotes_for(c),
        })
    corpus = json.loads((RAW / "corpus_stats.json").read_text()) if (RAW / "corpus_stats.json").exists() else {"rows": 0, "first": None}
    total_rows = corpus["rows"]
    excluded_ai = sum(1 for a in audit if a["status"] == "excluded-ai")
    seed_names = ", ".join(c["name"].split(" - ")[0] for c in (x["c"] for x in keep) if c["seed"])
    data = {
        "built": TODAY,
        "stats": {"videos": len(videos_out), "people": len(set().union(*[x["r"]["authors"] for x in keep])), "redditRows": total_rows,
                  "redditFirst": time.gmtime(corpus["first"]).tm_year if corpus["first"] else None, "candidates": len(channels), "excludedAi": excluded_ai,
                  "labelChecked": sum(v[0] in DISCLOSURE for v in videos_out)},
        "method": json.loads((ROOT / "data/method.json").read_text()) | {"seedNames": seed_names},
        "channels": channels_out, "videos": videos_out,
    }
    (ROOT / "site/data.json").write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")))
    print(f"{len(channels_out)} channels, {len(videos_out)} videos, {len(json.dumps(data, ensure_ascii=False)) // 1024} KB")
    print("titles without a Vietnamese translation:", sum(not v[9] for v in videos_out))
    print(collections.Counter(a["status"] for a in audit))
    print("levels", sorted(collections.Counter(v[6] for v in videos_out).items()), "labelled", sum(v[7] for v in videos_out))
    for a in audit:
        print(f"{a['status'][:12]:12} {a['score']:.2f} p{a['people']:<4} t{a['threads']:<4} {a['first'] or '':<5} sh{a['shared'] or 0:<4}/{a['commenters'] or 0:<5} f{a['fanShare']:.2f} l{a['loyal']:.2f} cpm{int(a['cpm'] or 0):<4} fl{(a['fillers'] or 0):<5.1f} c{a['captions']} ai{len(a['ai_talk'])} {a['name'][:34]}")


if __name__ == "__main__":
    main()
