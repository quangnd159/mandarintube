# MandarinTube

A clean place to watch Mandarin listening videos that learners keep recommending.
Live at https://mandarintube.dqnotes.com/ in Vietnamese by default, with an English switch.

It's a static site on Cloudflare Workers, so there's no server to run. The data is built
on your Mac and uploaded. Likes and history stay in each visitor's browser.

See other stuff by Quang at [dqnotes.com](https://www.dqnotes.com/).

## Make this for another language

Give [PROMPT.md](PROMPT.md) to an AI coding agent, and fill in the square brackets.

## Refresh the data

```bash
./refresh.sh            # new videos and Reddit posts, checks, titles, rebuild. Doesn't publish.
./refresh.sh deploy     # the same, then publish if the safety check passes
./refresh.sh discover   # find new candidate channels and write the review report
./refresh.sh accept     # publish a run the safety check stopped, after looking at it
./refresh.sh status     # when each job last ran
```

It needs `yt-dlp`, `python3`, `npx` and the `claude` CLI, plus a Cloudflare login
(`npx wrangler login`). There are no API keys. Each step resumes, and YouTube's rate limits
just mean carrying on later. Results are in `data/raw/update_report.md`, with full logs in
`data/raw/logs/`.

## The schedule

`deploy/install-schedule.sh` installs a launchd job, and `deploy/install-schedule.sh remove`
takes it out. It checks daily and whenever a drive is mounted, then does whatever is due:

| Every | Job | Publishes? |
| --- | --- | --- |
| 30 days | Refresh existing channels, then translate new titles | Yes, if the safety check passes |
| 90 days | Find new candidates and re-check listed channels' frames | No, it only writes a report |

A missed run happens at the next chance, and a failed one retries the next day. You get a
notification when something is published, stopped or broken. Commits stay local, so push them
when you like. While the drive is unplugged the job can't start, and nothing warns you.

Claude's ordinary sign-in expires within days, so give the job a long-lived token. Run
`claude setup-token`, then:

```bash
security add-generic-password -U -s mandarintube-claude-token -a "$USER" -w
```

If it fails anyway, the site still publishes, new titles show in their original language, and
the report says how many. The next run translates them.

The safety check stops publishing if more than 2 channels or 10% of videos would disappear, if
more than 1% of listed videos lack an AI label check, or if a channel would appear unreviewed.

## Add a channel

A channel in `data/channels.json` can't reach the site until it's approved, however strong its
evidence. `./refresh.sh discover` adds the 10 strongest new candidates and writes
`data/raw/review_report.md` with their evidence and Claude's advice on their frames. Then:

```bash
python3 pipeline/review.py list
python3 pipeline/review.py approve @handle 3      # the level is optional, from 1 to 4
python3 pipeline/review.py reject @handle "Generated hosts in recent videos."
```

To suggest one yourself, add it to `data/channels.json`, with `"aliases": ["Its Reddit name"]`
if people call it something other than its channel name, then run `./refresh.sh discover`.

## Translate new titles

Vietnamese titles live in `data/titles_vi.json` by video ID, and a title with no translation
shows the original. Refreshing fills them with `python3 pipeline/titles.py auto`. To do it by
hand, use `todo`, translate each batch to `out_NN.json` following
`pipeline/titles_prompt.md`, then `merge`.

## Change what's on the site

| To do this | Edit |
| --- | --- |
| Approve or reject a channel | `python3 pipeline/review.py` |
| Change a channel's Reddit names | `aliases` in `data/channels.json`, or `ALIASES` in `pipeline/mentions.py` |
| Set a channel's level | `levels` in `data/review.json` |
| Change the quotes on a channel page | `data/quotes.json` |
| Change the listening filter | `NEVER_LISTENING` and `MAYBE_NOT` in `pipeline/build.py` |
| Keep only some of a mixed channel | `only_titles` in `data/review.json` |
| Change the interface wording | `T.vi` and `T.en` in `site/app.js` |
| Change the method page wording | `data/method.json`, which has both languages |

After editing, run `python3 pipeline/build.py`. It also writes `data/audit.json`, which lists
every candidate with its evidence and why it was kept or left out. That file quotes viewer
comments, so it stays local, as do the review notes in `data/raw/review_notes.json`. Being in
`exclude` isn't a claim about a channel: it can mean the channel isn't listening content, or
that its videos couldn't be confirmed as suitable.

## How the pipeline works

1. `corpus.py` downloads the Mandarin-learning subreddits from the Arctic Shift archive, and
   `corpus.py sync` adds what's new.
2. `mentions.py` finds each candidate channel's name in those comments.
3. `catalog.py` lists each channel's public videos with `yt-dlp`.
4. `signals.py` samples comments and captions. Commenter IDs are hashed.
5. `disclosure.py` reads YouTube's "How this was made" label and speech language on watch pages.
6. `build.py` scores everything and writes `site/data.json`.

`discover.py` and `candidates.py` find channels in YouTube search and Reddit, and `shortlist.py`
adds the strongest as candidates. `contact_sheets.py` makes the frame sheets, and
`frame_review.py` asks Claude about them. `update.py` runs it all.
`data/raw/` holds the raw downloads and is never committed or published.

Local preview: `python3 pipeline/dev_server.py`, then open http://localhost:8787

Tests: `python3 -m unittest discover tests`

## License

The code is under the [MIT License](LICENSE). That doesn't cover third-party material the site
points to or includes: video titles and thumbnails belong to their creators, Reddit quotes to
their authors, and the LXGW WenKai font is under the SIL Open Font License.
