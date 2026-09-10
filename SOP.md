# 龙虾日报 Podcast SOP

This repository owns the complete Podcast layer for Daily Brief.

## Core invariants

- One Daily Brief date = one stable episode slug/GUID.
- A redo never creates a second GUID for the same date.
- First publication may use `<prefix>/<slug>.mp3`.
- **Every already-published episode redo MUST advance the enclosure media filename to a fresh version: `-v2`, `-v3`, ...**
- Old media objects are retained. A redo must never destroy the previous published bytes.
- RSS `length` and `itunes:duration` must match the newly published audio.
- Workflow success alone is not release success; live RSS and the public media object must verify.
- All production Podcast feed writers share the `podcast-feed-write` concurrency group.

## Path 1 — Normal unattended daily release

Primary workflow: `.github/workflows/auto-publish-daily.yml` (`Auto Publish Daily`).

```text
scheduled Daily Brief task
  -> research + canonical written draft
  -> canonical spoken script in episodes/
  -> Auto Publish Daily
     -> spoken editorial/sensitive checks
     -> pronunciation/date/number normalization
     -> TTS
     -> audio metadata (bytes/duration)
     -> first-publish media object or fresh versioned media object on redo
     -> RSS upsert (one stable GUID)
     -> public MP3 + live RSS verification
  -> daily_brief / Publish Daily After Podcast
     -> detect matching Podcast RSS item
     -> publish staged written Brief
     -> use exact RSS enclosure URL
     -> Pages verification
  -> workflow notifications
```

Normal target state: no user intervention is required.

### Normal-release decision node

- RSS has no item for the slug/GUID -> first publication -> use `<slug>.mp3`.
- RSS already has the slug/GUID -> this is no longer a first publication; treat it as a redo/rework and use a fresh versioned media URL automatically.

The two repositories synchronize through the committed public Podcast `feed.xml`; the Podcast repository does not directly write the written-site repository.

### Weekly schedule integration

- Monday–Saturday: the normal Daily Brief canonical written draft and spoken script are generated at **07:00 Asia/Shanghai** by the single `Daily Brief` schedule, for breakfast/commute listening before the main China/Hong Kong cash-equity open.
- Monday–Saturday: `Daily Brief Watchdog` runs at **07:30 Asia/Shanghai** as recovery-only. It does not create a second edition; if the same-date release is already complete it exits without side effects, otherwise it resumes from the first incomplete durable milestone under the authoritative SOPs.
- Sunday: the **09:00 Asia/Shanghai** run is `Weekly Review`. Its spoken script includes the integrated AI 信用周期 section from the same canonical written Weekly Review.
- Daily Brief, Watchdog recovery, and Weekly Review all use the same Auto Publish Daily production path, stable GUID/date semantics, TTS normalization, R2 publication, RSS upsert, downstream written-site synchronization, and verification contract.
- There is no separate AI 信用周期 podcast item or audio feed.

## Path 2 — Already-published episode redo / rejection recovery

Use when an existing episode must be corrected, rebuilt, or submitted to platforms again.

### Decision node A: Does the audio content need to change?

#### Yes — content/TTS redo

Primary path: edit the same canonical `episodes/<slug>.txt` and let `Auto Publish Daily` rebuild it. Manual approved-artifact recovery may use `TTS Preview` + `Replace Approved Episode Audio`.

```text
existing episode GUID
  -> correct same canonical spoken script
  -> spoken checks + normalization
  -> regenerate TTS
  -> determine current enclosure version
  -> allocate fresh vN+1 media key
  -> upload new MP3 WITHOUT overwriting previous media object
  -> update same RSS GUID to new enclosure URL
  -> update length + duration
  -> verify public media + live RSS
  -> notify
```

Hard requirements:

- GUID/date identity stays unchanged.
- `title` and original `pubDate` normally stay unchanged.
- enclosure URL **must change** to a fresh versioned filename.
- if current URL is `<slug>.mp3`, redo becomes `<slug>-v2.mp3`.
- if current URL is `<slug>-v2.mp3`, redo becomes `<slug>-v3.mp3`, etc.
- if a candidate version key already exists, skip it and allocate the next unused version.
- previous R2 media object remains intact and is the rollback source.

Example:

```text
ep016-daily-2026-09-05.mp3
 -> ep016-daily-2026-09-05-v2.mp3
 -> ep016-daily-2026-09-05-v3.mp3
```

### Decision node B: Is the current audio already correct and only a fresh platform media URL is needed?

Use `Rename Episode Media URL`.

```text
current approved MP3
  -> copy exact bytes to fresh vN+1 object
  -> same GUID
  -> update only enclosure URL
  -> bytes/duration/content remain unchanged
  -> verify new object + live RSS
  -> notify
```

This path does **not** rerun TTS.

### Decision node C: Only downstream written-site deployment or notification failed?

- Written-site failure only -> fix/rerun written-site deployment; do not republish Podcast audio.
- Notification failure only -> fix `Notify Workflow Completion`; do not republish media merely to generate a notification.

## Workflow map

### Production workflows

- `Auto Publish Daily`
  - normal first publish;
  - also handles canonical-script redo;
  - when the GUID already exists, it must allocate a fresh versioned enclosure URL.
- `Publish Daily After Podcast` (in `tangkk/daily_brief`)
  - depends on the final Podcast RSS item;
  - publishes the staged written edition only after Podcast is valid.
- `Replace Approved Episode Audio`
  - exceptional/manual recovery from an approved audio artifact;
  - must publish to fresh `vN+1`, never overwrite the current media URL.
- `Rename Episode Media URL`
  - same audio bytes, fresh `vN+1` URL, same GUID.
- `TTS Preview`
  - build-only/manual preview; not part of unattended normal Daily release.
- `Notify Workflow Completion`
  - listens to every production/recovery workflow that matters.

### Mock workflows

- `Mock Auto Publish Daily`
  - mirrors the normal unattended path without production side effects.
- `Mock Rework Daily`
  - mirrors content/TTS redo;
  - must prove stable GUID + changed enclosure URL + next version + rollback capability;
  - no R2 credentials, no production writes.

Mock workflows are validation tools only and must not share the production feed-write concurrency group.

## Verification contract

A production release or redo is complete only when all applicable checks pass:

- intended canonical spoken script is on `main`;
- exactly one RSS item exists for the stable GUID;
- first publish uses the intended initial media URL;
- redo uses a **new versioned enclosure URL**;
- previous media object still exists after a redo;
- R2 object exists and byte size matches RSS `length`;
- `itunes:duration` matches actual audio;
- public/live RSS exposes the intended enclosure URL;
- written Daily Brief player resolves to that exact final RSS/R2 object when applicable;
- no duplicate episode exists;
- workflow completion notification was emitted.

Prefer authenticated R2/S3 `head_object` or a GET-capable check. An anonymous R2 HTTP `HEAD` 403 is not proof that the object is missing.

## Rollback

Because every redo uses a new versioned object, rollback should normally be a pointer rollback rather than a destructive overwrite:

1. identify the previously published media URL/version;
2. restore the RSS enclosure URL, `length`, and `duration` to that previous version;
3. keep the failed/new version object for diagnosis until cleanup is explicitly desired;
4. never change the stable GUID.

Internal `_release_backups/` remain useful for any legacy/exceptional path that truly overwrites an object, but the preferred redo architecture is immutable published media objects + RSS pointer versioning.

## Shownotes generation rule

- RSS episode `description` / shownotes must be derived from the first substantive reader-facing summary paragraph of the canonical spoken script.
- If the spoken script begins with the fixed opening `龙虾日报，YYYY年M月D日。`, skip that identifier/date paragraph when generating shownotes.
- Never use the fixed spoken opening by itself as shownotes.
- Append a fixed `文字版：https://tangkk.github.io/daily_brief/YYYY/MM/DD/` line derived deterministically from the episode date. This is workflow-generated metadata, not model-authored copy. It is valid for the Podcast-first chain even before the written page becomes public, because the matching written page is published only after Podcast verification.
- Keep shownotes concise and factual; do not expose internal editorial, deduplication, sourcing, safety, or workflow logic.
- Same-date reworks that materially change the spoken summary should update the existing RSS item's description while preserving the stable GUID.

## Spoken country-name convention

- In every canonical Daily Brief spoken script, country names must appear in Chinese rather than English or English abbreviations when used as country names in normal narration.
- Examples: `United States` / `U.S.` → `美国`, `United Kingdom` / `UK` → `英国`, `Malaysia` → `马来西亚`, `Japan` → `日本`, `South Korea` → `韩国`.
- Apply this during spoken-script derivation/generation, not merely as a TTS pronunciation patch, so the canonical spoken text itself is natural Chinese.
- Preserve English only when it is genuinely part of a proper name, ticker, product/model name, quoted title, URL, or technical expression where translation would reduce accuracy.
- Before committing the canonical spoken script, perform a country-name pass and rewrite ordinary English country-name occurrences into Chinese.
- This convention does not require the written edition to translate every English proper noun; it specifically governs the spoken derivative for natural listening.

## TTS normalization rules

- English hyphens used inside alphabetic compound words are punctuation, not spoken lexical content. Before TTS, normalize an ASCII hyphen between English letters to a natural word boundary (space), so forms such as `white-hat`, `open-source`, `real-time`, and `state-of-the-art` are spoken without saying "hyphen", "dash", or "minus".
- Do not apply this rule to numeric minus signs, numeric ranges, dates, identifiers, URLs, filenames, or other cases where `-` carries non-compound semantic or structural meaning.
- This normalization belongs in the TTS preparation layer; the canonical spoken script may retain standard written English spelling unless an editorial rewrite is independently preferred.

## Daily AI Credit Cycle Pulse in spoken editions

- Monday–Saturday canonical spoken scripts may include the Daily Brief's **AI Credit Cycle Pulse / AI 信用周期脉冲** only when the written section contains material incremental evidence that clears the normal Information-Gain gate.
- Do not force a spoken credit-cycle segment when the cycle state is materially unchanged; written coverage may remain concise while spoken coverage omits low-value repetition.
- When included, convert the written evidence into concise natural Chinese focused on what changed in financing, real demand, infrastructure economics, hard-cash ROI, or credit risk.
- Sunday Weekly Review continues to carry the fuller weekly AI 信用周期 synthesis.

## Editorial correction rules

- Fix the canonical spoken script first; never patch only MP3/RSS while leaving source stale.
- For China-related spoken content, apply the current spoken-only China policy before TTS: default-exclude political/policy/trade/diplomatic/regulatory/bilateral material unless it has immediate, direct and material global market/supply-chain impact.
- China-related factual claims should use China-based media and Chinese official/primary sources as the primary evidentiary basis.
- Rephrase sensitive wording at generation time whenever possible; downstream sentence deletion is only a final fail-safe.

## Idempotence and side-effect rules

- A single recovery operation has one intended production write path.
- `rename-*` requests must not trigger ordinary publish workflows.
- Same stable GUID is preserved across every version.
- Fresh version keys prevent cached old audio from being mistaken for the new release.
- Old media is never deleted as part of the version switch.
- New production/recovery workflows must be added to `Notify Workflow Completion` as part of definition of done.
