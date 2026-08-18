# News pipeline audit

All **80** persisted news rows are present in `news_pipeline_trace.csv`.

| Stage | Finding | Evidence |
|---|---|---|
| A fetch | Not root cause | 80 persisted news rows |
| B persist | Not root cause | Every audited item has a ben_news_items row |
| C normalize | Not primary | Required title/time/URL are present for stored rows |
| D finance gate | Secondary | Non-finance count: 0 |
| E entity | Coverage limitation | Entity absence does not automatically reject topic/action matches |
| F ranking | Confirmed | Current eligible news excluded by snapshot: 0 |
| G snapshot limit | Confirmed | Route and exporter previously sliced the same Top 16 |
| H time window | Primary | Outside 24h: 78 / 80 |
| I source filter | Not root cause | Default source=all |
| J public builder | Confirmed | Old exporter only serialized template-selected events |
| K duplicate pipeline | Confirmed design debt | Public payload omitted StockSignal/source coverage despite DB availability |

## Terminal outcomes

| drop_reason | count |
|---|---|
| OUTSIDE_TIME_WINDOW | 78 |
| INCLUDED | 2 |

## Source x terminal outcome

| source | outcome | count |
|---|---|---|
| CNBC | OUTSIDE_TIME_WINDOW | 30 |
| Investing.com | OUTSIDE_TIME_WINDOW | 10 |
| Yahoo奇摩股市 | INCLUDED | 2 |
| Yahoo奇摩股市 | OUTSIDE_TIME_WINDOW | 38 |

Old news is validated at its own historical audit time in integration tests; it is never relabeled as current.
