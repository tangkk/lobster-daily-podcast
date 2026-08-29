# 龙虾日报 Podcast SOP

This repository owns the complete podcast layer for Daily Brief.

## Source relationship

The canonical written Daily Brief is published separately in `tangkk/daily_brief`.
The podcast script is a listening-first derivative of that written edition.

## Repository responsibilities

- Spoken canonical scripts: `episodes/*.txt`
- Podcast RSS: `feed.xml`
- Podcast artwork: `cover.jpg`
- TTS generation and publication workflow
- Audio replacement workflow
- Podcast notifications
- R2 audio references / podcast metadata handled by the podcast workflow

The R2 MP3 is the single audio source of truth. The written Daily Brief site may play this same R2 object directly, but it must not generate or upload a separate copy.

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

1. Finish and publish the canonical written Daily Brief to `tangkk/daily_brief`.
2. Create a Chinese listening-first spoken derivative, normally 8–15 minutes on an ordinary day.
3. Store the spoken canonical text in this repository under `episodes/` using the existing `epNNN-daily-YYYY-MM-DD.txt` naming convention.
4. Generate TTS in this podcast repository.
5. **Daily Brief does not require a preview/approval gate.** Once TTS succeeds, publish the final MP3 directly to R2 and update `feed.xml` in the same daily run.
6. Before the RSS update is considered successful, derive and write the real MP3 byte length and actual `itunes:duration`; never use placeholders.
7. Send the configured workflow notification after publication so success or failure is visible immediately.
8. The written site plays that same R2 MP3; do not create a second audio object for it.

## Exception handling

- A failed TTS/upload/RSS step is a failed daily publication; fix the cause and resume/re-run the failed publication path rather than creating a duplicate episode.
- Re-runs must be idempotent for the same date and episode number: replace/update the existing R2 object and RSS item rather than appending duplicates.
- Manual preview/approval may still be used for debugging or exceptional editorial review, but it is not part of the normal 龙虾日报 daily SOP.
- This direct-publish exception applies to 龙虾日报 only. Other 龙虾 podcast programs keep their own preview/approval SOP unless explicitly changed.

The written site and podcast remain independent publishing layers; they share only the final R2 audio object for playback.
