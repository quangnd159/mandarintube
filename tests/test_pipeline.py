"""The rules that stand between an unattended job and the live site.

Run: python3 -m unittest discover tests
"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "pipeline"))

import frame_review  # noqa: E402
import mentions  # noqa: E402
import shortlist  # noqa: E402
import signals  # noqa: E402
import titles  # noqa: E402
import update  # noqa: E402
from build import inclusion  # noqa: E402

DAY = 86400


def channel(**kw):
    return {"excluded": None, "seed": False, "reviewed": True} | kw


def site(channels=3, videos=100, checked=None, untranslated=0):
    rows = [[f"v{i}", 0, "t", 100, 1, 1, 1, 1, 0.5, "" if i < untranslated else "vi"] for i in range(videos)]
    chans = [{"id": f"c{i}", "key": f"h{i}", "name": f"Channel {i}", "seed": False} for i in range(channels)]
    return {"channels": chans, "videos": rows, "stats": {"labelChecked": videos if checked is None else checked}}


class Inclusion(unittest.TestCase):
    def test_strong_evidence_alone_cannot_list_a_channel(self):
        status, _ = inclusion(channel(reviewed=False), people=500, shared=500, ai_disclosed=0)
        self.assertEqual(status, "pending-review")

    def test_reviewed_channel_with_evidence_is_listed(self):
        self.assertEqual(inclusion(channel(), 3, 0, 0)[0], "kept")
        self.assertEqual(inclusion(channel(), 0, 5, 0)[0], "kept")

    def test_review_does_not_override_evidence_or_the_ai_label(self):
        self.assertEqual(inclusion(channel(), 2, 4, 0)[0], "excluded-evidence")
        self.assertEqual(inclusion(channel(), 9, 9, 1)[0], "excluded-ai")

    def test_seed_needs_no_evidence_but_still_loses_to_the_ai_label(self):
        self.assertEqual(inclusion(channel(seed=True), 0, 0, 0)[0], "kept")
        self.assertEqual(inclusion(channel(seed=True), 0, 0, 1)[0], "excluded-ai")

    def test_exclusion_wins(self):
        c = channel(excluded={"kind": "ai", "reason": "x"})
        self.assertEqual(inclusion(c, 9, 9, 0)[0], "excluded-ai")


class SafetyCheck(unittest.TestCase):
    def test_ordinary_growth_passes(self):
        stops, notes = update.check_changes(site(), site(videos=110), set())
        self.assertEqual(stops, [])
        self.assertTrue(any("10 added" in n for n in notes))

    def test_large_video_drop_stops(self):
        self.assertTrue(update.check_changes(site(videos=100), site(videos=89), set())[0])
        self.assertFalse(update.check_changes(site(videos=100), site(videos=90), set())[0])

    def test_losing_many_channels_stops_but_one_is_only_reported(self):
        stops, notes = update.check_changes(site(channels=5), site(channels=4), set())
        self.assertEqual(stops, [])
        self.assertTrue(any("removed" in n for n in notes))
        self.assertTrue(update.check_changes(site(channels=5), site(channels=2), set())[0])

    def test_unreviewed_new_channel_stops(self):
        self.assertTrue(update.check_changes(site(channels=1), site(channels=2), set())[0])
        self.assertFalse(update.check_changes(site(channels=1), site(channels=2), {"@h1"})[0])

    def test_unchecked_labels_stop(self):
        self.assertTrue(update.check_changes(site(), site(checked=98), set())[0])
        self.assertFalse(update.check_changes(site(), site(checked=99), set())[0])

    def test_empty_build_stops(self):
        self.assertTrue(update.check_changes(site(), {"channels": [], "videos": []}, set())[0])


class Schedule(unittest.TestCase):
    NOW = 1_000 * DAY

    def test_first_tick_does_both(self):
        self.assertEqual(update.due({}, self.NOW), ["run", "discover"])

    def test_recent_success_means_nothing_due(self):
        state = {"last_success": self.NOW - DAY, "last_attempt": self.NOW - DAY, "last_discovery": self.NOW - DAY}
        self.assertEqual(update.due(state, self.NOW), [])

    def test_failure_retries_next_day_not_next_hour(self):
        state = {"last_success": self.NOW - 40 * DAY, "last_discovery": self.NOW - DAY}
        self.assertEqual(update.due(state | {"last_attempt": self.NOW - 3600}, self.NOW), [])
        self.assertEqual(update.due(state | {"last_attempt": self.NOW - DAY}, self.NOW), ["run"])

    def test_held_run_waits_for_a_person(self):
        state = {"held": True, "last_success": 0, "last_attempt": self.NOW - DAY, "last_discovery": self.NOW - DAY}
        self.assertEqual(update.due(state, self.NOW), [])


class Sampling(unittest.TestCase):
    videos = [{"id": f"v{i}", "duration": 200, "view_count": i, "timestamp": i} for i in range(40)]

    def test_full_sample_is_left_alone_when_new_videos_arrive(self):
        have = {"count": signals.SAMPLE, "ids": {"old"}}
        self.assertEqual(signals.still_needed(self.videos, have), [])

    def test_new_channel_gets_a_full_sample(self):
        self.assertEqual(len(signals.still_needed(self.videos, {"count": 0, "ids": set()})), signals.SAMPLE)

    def test_partial_sample_is_topped_up(self):
        have = {"count": signals.SAMPLE - 2, "ids": set()}
        self.assertEqual(len(signals.still_needed(self.videos, have)), 2)


class Shortlist(unittest.TestCase):
    def test_address_forms_match(self):
        self.assertEqual(shortlist.norm("https://www.youtube.com/@Foo/"), "foo")
        self.assertEqual(shortlist.norm("user/foo"), "foo")
        self.assertEqual(shortlist.norm("c/Foo"), "foo")
        self.assertEqual(shortlist.norm("channel/UCabc"), "ucabc")

    def test_known_and_weak_channels_are_skipped_and_people_outrank_search(self):
        links = [{"key": "@known", "authors": 9, "name": "K"}, {"key": "@weak", "authors": 2, "name": "W"},
                 {"key": "@liked", "authors": 4, "name": "L"}]
        search = [{"id": "UC1", "handle": "@found", "name": "F", "queries": ["a", "b", "c"]},
                  {"id": "UC2", "handle": "@rare", "name": "R", "queries": ["a"]}]
        got = shortlist.rank(links, search, {"known"})
        self.assertEqual([r["name"] for r in got], ["L", "F"])

    def test_same_channel_from_both_sources_merges(self):
        links = [{"key": "user/both", "authors": 3, "name": None}]
        search = [{"id": "UC1", "handle": "@both", "name": "Both", "queries": ["a", "b", "c"]}]
        got = shortlist.rank(links, search, set())
        self.assertEqual(len(got), 1)
        self.assertEqual((got[0]["name"], got[0]["people"], got[0]["queries"]), ("Both", 3, 3))


class Replies(unittest.TestCase):
    def test_title_reply_ignores_extra_text_and_ids_not_asked_for(self):
        reply = 'Here you go:\n```json\n{"a": "một", "z": "lạ"}\n```'
        self.assertEqual(titles.parse_reply(reply, {"a", "b"}), {"a": "một"})

    def test_bad_title_reply_raises(self):
        with self.assertRaises(ValueError):
            titles.parse_reply("sorry", {"a"})

    def test_verdict_reply(self):
        reply = 'Done.\n[{"handle": "@a", "verdict": "real", "note": "x"}, {"note": "no handle"}]'
        self.assertEqual([v["handle"] for v in frame_review.parse_verdicts(reply)], ["@a"])


class FallbackAliases(unittest.TestCase):
    def test_distinctive_name_is_used(self):
        self.assertEqual(mentions.fallback_aliases("Hancai Chinese"), ["Hancai Chinese"])

    def test_generic_or_single_word_names_are_not(self):
        self.assertEqual(mentions.fallback_aliases("Learn Chinese"), [])
        self.assertEqual(mentions.fallback_aliases("Chinese"), [])
        self.assertEqual(mentions.fallback_aliases("Hancai"), [])


if __name__ == "__main__":
    unittest.main()
