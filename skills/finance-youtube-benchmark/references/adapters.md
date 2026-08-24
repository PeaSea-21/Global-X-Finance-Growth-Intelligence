# Adapter contract

## Common response

Every adapter returns:

```json
{
  "adapter": "local_text|public_youtube_feed|transcriptapi",
  "backend_status": "AVAILABLE|DEGRADED|DISABLED|UNAVAILABLE",
  "actual_run_status": "SUCCESS|PARTIAL|FAILED|NOT_RUN",
  "endpoint_verified": "VERIFIED|UNVERIFIED|UNAVAILABLE|NOT_RUN",
  "extraction_method_verified": "VERIFIED|UNVERIFIED|DISABLED|NOT_RUN",
  "terms_status": "APPROVED|UNKNOWN|BLOCKED",
  "commercial_use_status": "APPROVED|UNKNOWN|BLOCKED",
  "cache_hit": false,
  "external_calls": 0,
  "estimated_cost_usd": 0.0,
  "limitations": []
}
```

## `local_text`

Permanent fallback. Accept a user-supplied transcript, summary, article, outline, or notes. Read locally, compute features and a SHA-256 hash, and do not persist the body in outputs. Status may be `VERIFIED/SUCCESS` without network.

## `public_youtube_feed`

Optional bounded metadata adapter for YouTube's public Atom channel feed. It returns recent video IDs, titles, publication times, and channel identity fields; it does not return views, thumbnail text, or transcripts. Cache the raw response outside permanent deliverables and reuse it before any request. A successful request proves endpoint reachability only; keep `terms_status` and `commercial_use_status` separate.

## `transcriptapi`

Optional adapter. In this MVP it exposes status only and remains `DISABLED/NOT_RUN` when no separately supplied secret exists. Never register an account, request an OTP, purchase credits, print a key, write a key, or infer verification without a real call.

## Unsupported methods

Do not use `yt-dlp`, undocumented InnerTube endpoints, browser scraping, login cookies, or YouTube account OAuth in this MVP.
