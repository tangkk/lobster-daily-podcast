# 龙虾日报 Podcast SOP

This repository owns the complete podcast layer for Daily Brief.

## Source relationship

The Daily Brief is researched and composed once as the canonical written edition. Before that written edition is made public, create its listening-first podcast derivative and finish the podcast audio publication. The canonical written post is then published to `tangkk/daily_brief` and references the exact final R2 audio object already published by the podcast layer.

## Repository responsibilities

- Spoken canonical scripts: `episodes/*.txt`
- Podcast RSS: `feed.xml`
- Podcast artwork: `cover.jpg`
- TTS generation and publication workflow
- Audio replacement workflow
- Podcast notifications
- R2 audio references / podcast metadata handled by the podcast workflow

The R2 MP3 is the single audio source of truth. The written Daily Brief site plays this same final R2 object directly; it must not generate, upload, or guess a separate audio URL.

## RSS requirements

Every published episode item in `feed.xml` must contain valid podcast metadata, including:

- a stable `guid`
- an MP3 `enclosure` with the real byte length and `type="audio/mpeg"`
- `itunes:duration` populated from the actual generated MP3 duration before publication
- `itunes:episodeType` set to `full`
- `itunes:explicit` set appropriately
- the written-edition link should point to `https://tangkk.github.io/daily_brief/YYYY/MM/DD/`, not to the retired `/spoken/` pages

Never publish an episode with a missing or placeholder duration. Audio replacement must update both enclosure byte length and `itunes:duration` from the replacement file.

## Daily order

1. Research and compose the canonical Daily Brief text, but do **not** publish the written site yet.
2. Create a Chinese listening-first spoken derivative, normally 8–15 minutes on an ordinary day.
3. Store the spoken canonical text in this repository under `episodes/` using the existing `epNNN-daily-YYYY-MM-DD.txt` naming convention.
4. Generate TTS in this podcast repository.
5. **龙虾日报 does not require a preview/approval gate.** Once TTS succeeds, publish the final MP3 directly to R2.
6. Update and verify `feed.xml` using the exact final R2 enclosure URL, real MP3 byte length, and actual `itunes:duration`. Podcast publication is not successful until this step succeeds.
7. Only after R2 + Podcast RSS are verified, publish the canonical written Daily Brief to `tangkk/daily_brief` and record the exact same final R2 enclosure URL in the written site's audio mapping. The written page must never display a guessed/not-yet-existing audio URL.
8. Verify that the public written page's audio player loads the final R2 MP3, then send the configured publication notification.

## Exception handling

- If TTS, R2 upload, or RSS publication fails, do not publish that day's written site yet. Fix/resume the failed podcast path first.
- If the written-site publication fails after Podcast publication succeeded, keep the already-published Podcast episode and retry only the written-site step.
- Re-runs must be idempotent for the same date and episode number and must never append duplicate RSS episodes.
- Manual preview/approval may still be used for debugging or exceptional editorial review, but it is not part of the normal 龙虾日报 daily SOP.
- This direct-publish exception applies to 龙虾日报 only. Other 龙虾 podcast programs keep their own preview/approval SOP unless explicitly changed.

The written site and podcast remain independent publishing layers; they share only the final R2 audio object for playback.
