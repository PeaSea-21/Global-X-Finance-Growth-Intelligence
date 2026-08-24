# Governance gates

## Source states

Keep these claims independent for every channel, endpoint, and backend:

- `identity_verified`: `VERIFIED | NEEDS_VERIFICATION | BLOCKED`
- `endpoint_verified`: `VERIFIED | UNVERIFIED | UNAVAILABLE | NOT_RUN`
- `extraction_method_verified`: `VERIFIED | UNVERIFIED | DISABLED | NOT_RUN`
- `terms_status`: `APPROVED | UNKNOWN | BLOCKED`
- `commercial_use_status`: `APPROVED | UNKNOWN | BLOCKED`
- `backend_status`: `AVAILABLE | DEGRADED | DISABLED | UNAVAILABLE`
- `actual_run_status`: `SUCCESS | PARTIAL | FAILED | NOT_RUN`

Technical success never upgrades terms or commercial-use status. `UNKNOWN` is not approval.

## Hard stops

Stop the affected operation when it would require a new API key, payment, login, account interaction, bypass, full transcript persistence, automatic publishing, or access to another project/P02 system.

Treat creator videos as `CREATOR_OPINION`. They may support style observations but cannot populate FactPack facts.

## Copyright and style

- Keep complete transcripts in memory or an ephemeral input file only; delete temporary copies after feature extraction.
- Persist hashes, counts, timestamps, labels, and high-level paraphrases, not transcript bodies.
- Default to zero verbatim quotations.
- Do not reproduce signature phrases, unique metaphors, personal stories, fixed intros, or a named creator persona.
- Build composite styles from at least three creators; no creator may supply more than 40% of the parameters.

## Finance evidence

Prefer official regulators, exchanges, statistics agencies, central banks, and company filings/IR. Label every generated statement as `FACT`, `INFERENCE`, or `OPINION`. Every important `FACT` must map to a FactPack `fact_id` and authoritative URL. Reject stale, conflicting, or unsupported facts.

## Cost and call controls

Use cache before network. Record provider, endpoint class, timestamp, cache hit, external-call count, estimated cost, response status, and limitations. This MVP allows at most three channels, nine analyzed videos, and one transcript request per video.
