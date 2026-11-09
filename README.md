# MandarinTube

A clean place to watch Mandarin listening videos that learners keep recommending.
Live at https://mandarintube.dqnotes.com/ in Vietnamese by default, with an English switch.

It's a static site on Cloudflare Workers, so there's no server to run. The data is built
on your Mac and uploaded. Likes and history stay in each visitor's browser.

## Refresh the data

```bash
./refresh.sh          # new videos and comments, then rebuild (does not deploy)
./refresh.sh deploy   # the same, then publish
```

It needs `yt-dlp`, `python3` and `npx`, plus a Cloudflare login (`npx wrangler login`).
No API keys. Monthly is plenty, since the point of the site isn't freshness.

Expect it to take hours. `disclosure.py` fetches watch pages one at a time because YouTube
answers 429 to anything faster. If it stops with exit code 3 it hit repeated rate limits:
wait a while and run `python3 pipeline/disclosure.py site` again, since it resumes. The
method page shows how many listed videos have been checked, so a partial run stays honest.

## Translate new titles

Vietnamese titles live in `data/titles_vi.json` by video ID, and a title with no translation
shows the original. `build.py` prints how many are missing. To fill them:

```bash
python3 pipeline/titles.py todo     # writes data/raw/titles/batch_NN.json
# translate each batch to out_NN.json following pipeline/titles_prompt.md (ask Claude Code)
python3 pipeline/titles.py merge    # checks them and adds what passes
python3 pipeline/build.py
```

## Change what's on the site

| To do this | Edit |
| --- | --- |
| Add a candidate channel | `data/channels.json`, plus its Reddit names in `ALIASES` in `pipeline/mentions.py` |
| Keep out, or bring back, a channel | `exclude` in `data/review.json` |
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

1. `corpus.py` downloads the Mandarin-learning subreddits from the Arctic Shift archive.
2. `mentions.py` finds each candidate channel's name in those comments.
3. `catalog.py` lists each channel's public videos with `yt-dlp`.
4. `signals.py` samples comments and captions. Commenter IDs are hashed.
5. `disclosure.py` reads YouTube's "How this was made" label and speech language on watch pages.
6. `build.py` scores everything and writes `site/data.json`.

`discover.py`, `candidates.py` and `reddit_harvest.py` found the first candidate list.
`contact_sheets.py` makes the frame sheets used for the by-eye AI review.
`data/raw/` holds the raw downloads and is never committed or published.

Local preview: `python3 pipeline/dev_server.py`, then open http://localhost:8787

## License

The code is under the [MIT License](LICENSE). That doesn't cover third-party material the site
points to or includes: video titles and thumbnails belong to their creators, Reddit quotes to
their authors, and the LXGW WenKai font is under the SIL Open Font License.
