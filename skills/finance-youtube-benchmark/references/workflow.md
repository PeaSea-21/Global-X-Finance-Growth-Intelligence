# Benchmark workflow

## Channel discovery and identity

Start from user candidates, public channel pages, official websites, and attributable media/company pages. Record at least two identity signals when possible: official channel URL/ID plus an official website or linked public profile. Select for topical role, evidence behavior, language, active publication, usable samples, and format diversity—not subscriber count alone.

For the three-channel pilot, cover:

1. Taiwan market/stock analysis.
2. Semiconductor or technology supply chain.
3. Global macro/US-to-Taiwan linkage.

## Video sampling

Separate long video, Shorts, livestream, and clip formats. Select one recent, one high-performance candidate, and one typical/ordinary video per channel.

Use age-adjusted within-channel evidence only when enough comparable view data exists. Otherwise retain `view_count=UNKNOWN`, label the high-performance item `CANDIDATE`, document the public/manual evidence, and do not calculate a synthetic outlier score. Popularity is never a truth or quality signal.

## Text ingestion

Allow one transcript request attempt per video. Prefer supplied text. When no approved transcript method succeeds, set `transcript_status=UNAVAILABLE` and perform only metadata/description-level analysis with low confidence. Never imply the first 30 seconds were observed when they were not.

## Analysis and profiles

Create one card per video, then aggregate three cards into a `PROVISIONAL` channel profile. Compare the three profiles and extract a narrative template library. Keep all observations traceable to video IDs and distinguish observed, inferred, and unavailable fields.

## Generation

Create one shared verified FactPack. Hold its facts constant across three drafts while varying only hook type, evidence order, pacing, and chapter mechanics. Generate a YouTube spoken-outline and X post package for each style. Run originality checks against any ephemeral source text and across generated variants.

## Acceptance

Run the commands and criteria in `templates/acceptance_manifest.json`. Output `P03 BENCHMARK MVP READY` only if all required checks pass and real-sample limitations are accurately represented; otherwise output `P03 BENCHMARK MVP BLOCKED` with blockers.
