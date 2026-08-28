# 龙虾日报 Podcast SOP

This repository owns the complete podcast layer for Daily Brief.

## Source relationship

The canonical written Daily Brief is published separately in `tangkk/daily_brief`.
The podcast script is a listening-first derivative of that written edition.

## Repository responsibilities

- Spoken canonical scripts: `episodes/*.txt`
- Podcast RSS: `feed.xml`
- Podcast artwork: `cover.jpg`
- TTS preview workflow
- Approved publish workflow
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
4. Generate the TTS preview from the podcast repository.
5. After approval, publish the final MP3 to R2 and update `feed.xml` with its real byte length and actual `itunes:duration`.
6. The written site plays that same R2 MP3; do not create a second audio object for it.

The written site and podcast remain independent publishing layers; they share only the final R2 audio object for playback.
