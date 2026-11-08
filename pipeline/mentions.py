#!/usr/bin/env python3
"""Step 5: find each candidate channel's name in the downloaded Reddit corpus.

Most recommendations name a channel without linking it, so links alone undercount.
Matching is local, exact and case-sensitive, so re-running is instant.
Output: data/raw/mentions/<channel_id>.json, data/raw/corpus_stats.json
"""
import collections
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
CATALOG = ROOT / "data/raw/catalog"
OUT = ROOT / "data/raw/mentions"
CORPUS = ROOT / "data/raw/corpus"

# Reddit shorthand for channels, keyed by handle. Names that are also common phrases
# ("Everyday Chinese") are matched case-sensitively in main() to limit false hits.
ALIASES = {
    "@TeaTimeChinese": ["TeaTime Chinese", "Tea Time Chinese", "TeaTimeChinese"],
    "@maomichinese3683": ["Maomi Chinese", "MaoMi Chinese", "MaomiChinese"],
    "@convochinese6115": ["Convo Chinese", "瞎扯学中文"],
    "@TalkTaiwaneseMandarin": ["Talk Taiwanese Mandarin"],
    "@RitaChinese": ["Rita Mandarin Chinese", "Rita Mandarin"],
    "@coffeebreakchinese": ["Coffee Break Chinese"],
    "@goeastmandarinchinese": ["GoEast Mandarin"],
    "@chinesewithben": ["Chinese with Ben"],
    "@comprehensiblemandarin": ["Comprehensible Mandarin"],
    "@ChocolateChineseCI": ["Chocolate Chinese"],
    "@chinesekk": ["Chinese KK", "ChineseKK"],
    "@eazymandarin": ["Eazy Mandarin", "EazyMandarin"],
    "@acupofchinese": ["A Cup of Chinese", "Cup of Chinese"],
    "@danichinese": ["Dani Chinese", "DaniChinese"],
    "@chinesewithsihan": ["Chinese with Sihan"],
    "@mumuchinesepodcast": ["Mumu Chinese", "Mumu's Chinese"],
    "@annieluo1307": ["Story Learning Chinese with Annie", "Learning Chinese with Annie", "Chinese with Annie"],
    "@Lazy-Chinese": ["Lazy Chinese"],
    "@xiaoguachinese": ["Xiaogua Chinese", "XiaoguaChinese", "Xiao Gua Chinese"],
    "@Xiao_Min": ["Chinese with Min"],
    "@MandarinClick": ["Mandarin Click", "MandarinClick"],
    "@DianeNeubauer": ["Diane Neubauer"],
    "@immersivechinese": ["Slow & Clear Chinese", "Slow and Clear Chinese"],
    "@blablachinese7526": ["Blabla Chinese", "BlaBla Chinese", "Bla Bla Chinese"],
    "@shianguuhsieh2107": ["Shianguu Hsieh", "Shianguu"],
    "@Stickynote.Chinese": ["Stickynote Chinese", "Sticky Note Chinese"],
    "@alisonmandarin1729": ["Alison Mandarin", "Alison's Mandarin"],
    "@CrazieLaoshi": ["Crazie Laoshi", "Crazy Laoshi"],
    "@acquiremandarin": ["Acquire Mandarin", "AcquireMandarin"],
    "@chinesemandarincherry": ["Mandarin Cherry", "Chinese Mandarin Cherry"],
    "@chinese9339": ["Speak Chinese With Da Peng", "Speak Chinese with Da Peng", "大鹏说中文", "Da Peng"],
    "@unconventionalchinese": ["Unconventional Chinese"],
    "@MandarinCorner2": ["Mandarin Corner", "MandarinCorner"],
    "@willhartmandarin": ["Will Hart"],
    "@dashumandarin": ["Dashu Mandarin", "大叔中文", "Dashu"],
    "@chloechinesecoach": ["Chloe Chinese", "Chloe Chinese Class"],
    "@ChinesePodcastWithShenglan": ["Shenglan"],
    "@comprehensiblechinese": ["Comprehensible Chinese", "Tingting Comprehensible"],
    "@speakyourchinese": ["Speak Your Chinese"],
    "@thinkinginchinese": ["Thinking in Chinese"],
    "@LalaChinese": ["Lala Chinese"],
    "@DadaMandarinChinese": ["Dada Mandarin", "大大 Mandarin"],
    "@ZhangkaiChinese": ["Zhangkai Chinese", "Zhang Kai Chinese"],
    "@JohnnyChinese": ["Johnny Chinese"],
    "@stellatuan.Chinese": ["Nail Chinese", "Stella Chinese"],
    "@chinese-at-dawn": ["Chinese at Dawn"],
    "@talkinChinese_redred": ["talkinchinese", "TalkinChinese"],
    "@bitesize.chinese": ["Bitesize Chinese"],
    "@EasyChineseClub": ["Easy Chinese Club"],
    "@sysmandarin": ["SyS Mandarin", "SYS Mandarin"],
    "@jiayouchinese2023": ["jiayouchinese", "Jiayou Chinese"],
    "@ShuoshuoChinese": ["Shuoshuo Chinese", "ShuoshuoChinese"],
    "@ChineseDailyPodcast": ["Chinese Daily Podcast"],
    "@LearnChineseThroughPodcast": ["Learn Chinese Through Podcast"],
    "@ChillingChinese": ["Chilling Chinese"],
    "@DANLIAOFreeToLearnChinese": ["Free To Learn Chinese", "每日中文课"],
    "@SayMandarin": ["Say Mandarin"],
    "@LearnChinesePodcast2011": ["Chinese Podcast For Learning"],
    "@EverydayChinese": ["Everyday Chinese"],
    "@AskAndy": ["Andy and Sarah", "Andy & Sarah"],
    "@MandarinHeroes": ["Mandarin Hero"],
    "@LearnChineseWithPipo": ["Chinese with Pipo"],
    "@竹子zhuzi": ["Talking China Learning Chinese", "说中国学中文"],
    "@chinese.with.xiaonita": ["Chinese with Xiaonita", "Xiaonita"],
    "@superchillchinese": ["Chill Chinese"],
    "@MandarinwithGisele": ["Mandarin with Gisele"],
    "@easytalkchinesewithJin": ["EasyTalk Chinese", "Easy Talk Chinese"],
    "@ChinesewithEmily": ["Emily Chinese", "Chinese with Emily"],
    "@mandarinwithnicole": ["Chinese with Nicole"],
    "@StorytimeinChinese": ["Storytime in Chinese"],
    "@BaoBaoMandarin": ["BaoBao Mandarin"],
    "@LinguaFlowChinese": ["LinguaFlow Chinese"],
    "@yoyochinese": ["Yoyo Chinese", "YoYo Chinese", "YoyoChinese"],
    "@chinesezerotohero": ["Chinese Zero to Hero", "Chinese Zero To Hero"],
    "@learnchinesenow": ["Learn Chinese Now"],
    "@GraceMandarinChinese": ["Grace Mandarin"],
    "@ChineseForUsOfficial": ["ChineseFor.Us", "ChineseForUs", "Chinese For Us"],
    "@LittleFoxChinese": ["Little Fox Chinese"],
    "@EasyMandarin": ["Easy Mandarin"],
    "@chinesecorner": ["ChineseCorner"],
    "@testvcn": ["TESTV"],
    "@kevininshanghai": ["Kevin in Shanghai"],
}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    lookup = {k.lower(): v for k, v in ALIASES.items()}
    patterns = []  # (compiled alias, channel_id)
    names = {}
    for f in sorted(CATALOG.glob("*.json")):
        d = json.loads(f.read_text())
        names[d["channel_id"]] = d["name"]
        aliases = lookup.get((d["handle"] or "").lower())
        if not aliases:
            print("no alias, skipped:", d["name"], d["handle"], flush=True)
            continue
        for a in aliases:
            patterns.append((a, d["channel_id"]))
    alias_to_cids = collections.defaultdict(list)
    for a, cid in patterns:
        alias_to_cids[a].append(cid)
    big = re.compile(r"(?<![\w])(" + "|".join(re.escape(a) for a in sorted(alias_to_cids, key=len, reverse=True)) + r")(?![\w])")

    hits = collections.defaultdict(dict)
    stats = {"rows": 0, "first": None, "last": None, "streams": {}}
    for path in sorted(CORPUS.glob("*.jsonl")):
        count, low, high = 0, None, None
        with path.open() as f:
            for line in f:
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue  # A line still being written by the downloader.
                count += 1
                t = int(r["created_utc"])
                low, high = t if low is None else min(low, t), t if high is None else max(high, t)
                text = " ".join(str(r.get(k) or "") for k in ("body", "title", "selftext"))
                for alias in set(big.findall(text)):
                    for cid in alias_to_cids[alias]:
                        hits[cid][r["id"]] = r
        stats["rows"] += count
        stats["streams"][path.stem] = {"rows": count, "from": low, "to": high, "complete": path.with_suffix(".done").exists()}
        if low:
            stats["first"] = low if stats["first"] is None else min(stats["first"], low)
            stats["last"] = high if stats["last"] is None else max(stats["last"], high)
    for cid in names:
        (OUT / f"{cid}.json").write_text(json.dumps({"channel_id": cid, "name": names[cid], "hits": list(hits[cid].values())}, ensure_ascii=False))
    (ROOT / "data/raw/corpus_stats.json").write_text(json.dumps(stats, indent=1))
    print(json.dumps(stats))
    for cid in sorted(names, key=lambda c: -len(hits[c]))[:70]:
        print(len(hits[cid]), len({h.get("author") for h in hits[cid].values()}), names[cid])


if __name__ == "__main__":
    main()
