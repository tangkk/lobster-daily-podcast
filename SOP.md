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

No podcast-specific artifact should be written back into `tangkk/daily_brief`.

## Daily order

1. Finish and publish the canonical written Daily Brief to `tangkk/daily_brief`.
2. Create a Chinese listening-first spoken derivative, normally 8–15 minutes on an ordinary day.
3. Store the spoken canonical text in this repository under `episodes/` using the existing `epNNN-daily-YYYY-MM-DD.txt` naming convention.
4. TTS preview is generated from the podcast repository.
5. After approval, publish/update the podcast RSS and audio using this repository's existing workflow.

The written site and podcast are independent publishing layers; the podcast may link back to the written edition, but it must not depend on podcast files living in `tangkk/daily_brief`.
