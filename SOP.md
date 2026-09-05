# 龙虾日报 Podcast SOP

This repository owns the complete podcast layer for Daily Brief.

## Source relationship

The Daily Brief is researched and composed once as the canonical written edition. Before it is public, the exact written edition is staged in `tangkk/daily_brief/_drafts/`. A listening-first spoken derivative is committed here under `episodes/`. That episode commit is the normal Podcast release trigger.

## Repository responsibilities

- Spoken canonical scripts: `episodes/*.txt`
- Podcast RSS: `feed.xml`
- Podcast artwork: `cover.jpg`
- Automatic TTS → R2 → RSS publication
- Audio replacement / media-URL versioning workflows
- Podcast notifications
- R2 audio references / podcast metadata

The R2 MP3 is the single audio source of truth. The written Daily Brief site plays this same final R2 object directly; it must not generate, upload, or guess a separate audio URL.

## Automatic daily release

Normal Podcast publication is handled by `.github/workflows/auto-publish-daily.yml`.

1. Research and compose the canonical written Daily Brief.
2. Stage that exact written edition in `tangkk/daily_brief/_drafts/YYYY-MM-DD-daily-brief.md`. `_drafts/` is not the public post path.
3. Create the listening-first spoken derivative and commit it directly to `main` here as `episodes/epNNN-daily-YYYY-MM-DD.txt`.
4. Before TTS, apply spoken-only editorial safety rules, sensitive-term checks, pronunciation/date/number normalization, and validation.
5. The episode push automatically generates final TTS. 龙虾日报 has no normal preview/approval gate.
6. The workflow uploads/replaces the canonical R2 object and upserts exactly one RSS item for the stable GUID, with the real enclosure URL, real byte length, actual `itunes:duration`, `itunes:episodeType=full`, and updated `lastBuildDate`.
7. After the RSS commit becomes visible, the independent `tangkk/daily_brief` workflow `Publish Daily After Podcast` detects the matching final Podcast item, publishes the staged written Brief, maps the exact enclosure URL, deploys Pages, and verifies the live player.

There is no cross-repository write token in the normal architecture. The two repositories synchronize through the committed public Podcast `feed.xml`, not by one repository directly writing the other.

`TTS Preview` is manual fallback/debugging only. The older publish-request workflow remains only as a legacy/manual recovery path and is not part of normal daily publication.

## Episode redo / rejection recovery SOP

Use this when an already-published episode must be corrected, is rejected by a platform, or needs to be re-reviewed.

### A. Editorial correction first

1. Fix the canonical spoken script in `episodes/` first. Do not patch only the RSS description or MP3 metadata while leaving the source script stale.
2. Keep the same date, slug and stable RSS GUID. Never create a second episode for the same Daily Brief date just to redo it.
3. For China-related spoken content, apply the current spoken-only China policy before TTS: default-exclude political/policy/trade/diplomatic/regulatory/bilateral material unless it has immediate, direct and material global market/supply-chain impact. If retained, use minimal neutral institutional wording. China-related facts must be grounded primarily in China-based media or Chinese official/primary sources.
4. Rephrase sensitive wording at the spoken-script stage whenever possible. Downstream sentence deletion is only the final fail-safe.

### B. If the audio itself must change

5. Update the same canonical spoken-script file. Let `Auto Publish Daily` regenerate TTS and replace the same episode/GUID.
6. Verify the exact final MP3 bytes, duration and RSS item. Do not declare success at TTS completion alone.
7. If the podcast platform has probably already fetched or started reviewing the previous media URL, do not rely on overwriting the same URL. Keep the GUID unchanged but version the enclosure media URL, for example:

   `daily/ep016-daily-2026-09-05-v2.mp3`

   The versioned file must contain the already-approved/latest MP3 bytes; no TTS regeneration is needed merely to change the media URL.
8. Keep the previous R2 object temporarily. Do not delete the old object during the URL switch; cached requests may still reference it.

### C. Media URL versioning

9. Use the dedicated `Rename Episode Media URL` path for a pure media-URL refresh. It copies the existing R2 object to a new versioned filename and updates only the enclosure URL for the same GUID.
10. A media-URL rename must not change title, GUID, episode date, description, byte length, duration or audio content.
11. `rename-*` requests must not trigger `Publish Approved Artifact`. Each recovery operation must have one intended write path only.

### D. Verification contract

A redo is not complete until all applicable checks pass:

- canonical spoken script on `main` is the intended corrected version;
- exactly one RSS item exists for the stable GUID;
- RSS enclosure points to the intended current media URL;
- R2 object exists and its byte size matches the RSS `length`;
- `itunes:duration` matches the actual audio;
- public/live RSS exposes the new enclosure URL;
- the written Daily Brief player, when applicable, resolves to the same final RSS/R2 audio object;
- no duplicate episode was created;
- the workflow completion notification was emitted.

Prefer R2/S3 `head_object` or a real GET-capable verification path for object verification. Do not treat an anonymous HTTP `HEAD` 403 from the R2 public endpoint as proof that the object is missing.

### E. Workflow notifications

Every production or recovery workflow must be included in `Notify Workflow Completion`. When a new workflow is added, notification coverage is part of the definition of done. At minimum this includes:

- Auto Publish Daily
- Publish Approved Artifact
- Replace Approved Episode Audio
- Rename Episode Media URL
- TTS Preview
- Pages build/deployment where applicable

If a workflow finishes but no notification arrives, first check whether its workflow name is listed in `.github/workflows/notify.yml` before debugging ntfy itself.

### F. Recovery decision table

- **Text/source problem before release:** edit canonical spoken script → normal Auto Publish.
- **Published audio content is wrong:** edit same spoken script → regenerate TTS → same GUID → verify public release.
- **Published audio is correct but platform may be caching/reviewing an older media URL:** do not regenerate TTS → version enclosure filename (`-v2`, `-v3`, …) → same GUID → verify new R2 object + live RSS.
- **Only written-site deployment failed:** do not republish Podcast; rerun/fix written-site deployment.
- **Only notification failed:** do not rerun the media publication merely to obtain a notification; fix the notify listener/path separately.

## Idempotence and failure handling

- Same date/slug reruns update the same RSS GUID; they never append a duplicate item.
- A media URL may be versioned when platform cache/review behavior requires a fresh enclosure URL, but the GUID remains stable.
- If TTS or R2/RSS publication fails, the written draft remains unpublished because the written workflow will not find a valid matching Podcast item.
- If Podcast succeeds but written publication/deployment fails, keep the Podcast episode and rerun the written workflow or retrigger the same staged date; do not republish a duplicate Podcast episode.
- The written repository must never synthesize/fallback an R2 URL.
- Manual preview/approval may still be used for exceptional editorial review, but not for the normal 龙虾日报 daily path.
- This direct-publish exception applies to 龙虾日报 only. Other 龙虾 podcast programs retain their own preview/approval SOP unless explicitly changed.
