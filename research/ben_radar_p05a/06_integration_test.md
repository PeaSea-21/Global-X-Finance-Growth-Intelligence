# Integration test

## Real stored news samples

| source | status | content_id | audit_as_of | event_id |
|---|---|---|---|---|
| yahoo_tw | PASS | 466bd475-8d8b-435e-ac25-6a2d6822fc9e | 2026-08-16T06:49:00+00:00 | evt_fcda133ecbe38c96 |
| cnbc | PASS | 2583e183-5fdd-43c1-b4ed-29ac5b5c1f86 | 2026-08-15T20:48:29+00:00 | evt_237783fb3192cfca |
| investing | PASS | b90d0852-a359-47ed-a601-f6f4c662e819 | 2026-08-15T20:21:16+00:00 | evt_7c718e7540434137 |

- Current real X rows in 24h: **149**.
- Unified 24h quality: `{"raw_count": 151, "eligible_count": 101, "event_count": 88, "compression_rate": 0.1287, "multi_item_events": 3, "multi_publisher_events": 1, "cross_platform_events": 0, "singleton_events": 85}`.
- Natural news/X overlap audit across stored corpus: **NATURAL_OVERLAP_FOUND**.
- If no overlap exists, no synthetic cross-platform event is promoted to production output.
- Full project check: **80 passed**; credential scan: **PASS**.
- Public Sites rendered tests: **2/2 PASS**.
- Browser regression: desktop, 390px mobile, `/stock-radar`, `/ai-radar`, `/radar`, and the deployed public URL all rendered without page-level overflow; console warnings/errors: **0**.
- Public version 2 verification: 16 event cards, 1 current news event, 10 StockSignals, 7 publishers, Top-1 share 50%.
