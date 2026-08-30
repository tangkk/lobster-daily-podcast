# 龙虾日报 Podcast SOP

This repository owns the complete podcast layer for Daily Brief.

## Source relationship

The Daily Brief is researched and composed once as the canonical written edition. Before it is public, the canonical written post is staged in `tangkk/daily_brief/_drafts/`. A listening-first spoken derivative is committed here under `episodes/`. That episode commit is the normal release trigger.

## Repository responsibilities

- Spoken canonical scripts: `episodes/*.txt`
- Podcast RSS: `feed.xml`
- Podcast artwork: `cover.jpg`
- Automatic TTS → R2 → RSS publication
- Audio replacement workflow
- Podcast notifications
- R2 audio references / podcast metadata

The R2 MP3 is the single audio source of truth. The written Daily Brief site plays this same final R2 object directly; it must not generate, upload, or guess a separate audio URL.

## Automatic daily release

Normal daily publication is handled by `.github/workflows/auto-publish-daily.yml`.

1. Research and compose the canonical written Daily Brief.
2. Stage that exact written edition in `tangkk/daily_brief/_drafts/YYYY-MM-DD-daily-brief.md`. `_drafts/` is not public.
3. Create the listening-first spoken derivative and commit it directly to `main` here as `episodes/epNNN-daily-YYYY-MM-DD.txt`.
4. The episode push automatically generates final TTS. 龙虾日报 has no normal preview/approval gate.
5. The workflow uploads/replaces the one canonical R2 object `daily/<slug>.mp3`.
6. The workflow upserts exactly one RSS item for the stable GUID, with the real enclosure URL, real byte length, actual `itunes:duration`, `itunes:episodeType=full`, and updated `lastBuildDate`.
7. Only after Podcast verification succeeds, the workflow checks out `tangkk/daily_brief`, moves the staged draft to `_posts/`, and writes the exact Podcast enclosure URL into `_data/audio.json`.
8. The workflow waits for the public written page and verifies both the Daily Brief title and exact audio URL before it succeeds. Notification is sent from workflow completion.

`TTS Preview` is manual fallback/debugging only. The older publish-request workflow remains only as a legacy/manual recovery path and is not part of normal daily publication.

## Idempotence and failure handling

- Same date/slug reruns replace the same R2 object and update the same RSS GUID; they never append a duplicate item.
- If TTS or R2/RSS publication fails, the written draft remains unpublished.
- If Podcast succeeds but written publication fails, keep the Podcast episode; rerunning the same episode safely retries the written step.
- If a written `_posts/` file already exists, the automatic workflow keeps it and only ensures the exact audio mapping, unless a staged `_drafts/` copy exists; a staged draft is authoritative and replaces the same dated post.
- The written repository must never synthesize/fallback an R2 URL.
- Manual preview/approval may still be used for exceptional editorial review, but not for the normal 龙虾日报 daily path.
- This direct-publish exception applies to 龙虾日报 only. Other 龙虾 podcast programs retain their own preview/approval SOP unless explicitly changed.

## Required secret for cross-repository publication

The podcast repository needs `DAILY_BRIEF_TOKEN`, a GitHub token with permission to read and write `tangkk/daily_brief`. The automatic workflow validates this secret before starting TTS so a missing cross-repo credential cannot leave a half-started daily release.
