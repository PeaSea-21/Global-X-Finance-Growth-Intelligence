# Source concentration audit

## Current full 24h event set

```json
{
  "evidence_count": 101,
  "unique_publishers": 9,
  "news_publishers": 1,
  "x_publishers": 8,
  "top1_share": 0.802,
  "top3_share": 0.8911,
  "publisher_counts": {
    "x:business": 81,
    "x:focus_taiwan": 5,
    "x:trendforce": 4,
    "x:testingcatalog": 3,
    "x:reutersbiz": 2,
    "yahoo": 2,
    "x:alibaba_qwen": 2,
    "x:polynoamial": 1,
    "x:ieobserve": 1
  },
  "status": "SOURCE_CONCENTRATION_WARNING",
  "warnings": [
    "TOP1_OVER_50_PERCENT",
    "TOP3_OVER_80_PERCENT"
  ],
  "thresholds": {
    "top1_share": 0.5,
    "top3_share": 0.8,
    "minimum_publishers": 5
  }
}
```

## Selected public snapshot

```json
{
  "evidence_count": 16,
  "unique_publishers": 7,
  "news_publishers": 1,
  "x_publishers": 6,
  "top1_share": 0.4375,
  "top3_share": 0.6875,
  "publisher_counts": {
    "x:business": 7,
    "x:reutersbiz": 2,
    "x:trendforce": 2,
    "yahoo": 2,
    "x:polynoamial": 1,
    "x:focus_taiwan": 1,
    "x:alibaba_qwen": 1
  },
  "status": "OK",
  "warnings": [],
  "thresholds": {
    "top1_share": 0.5,
    "top3_share": 0.8,
    "minimum_publishers": 5
  }
}
```

Warning policy: Top 1 > 50%, Top 3 > 80%, or fewer than 5 publishers. These thresholds flag
editorial fragility; they do not delete Bloomberg or force low-quality sources into the feed.
