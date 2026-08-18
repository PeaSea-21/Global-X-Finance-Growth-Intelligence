# Handoff

- 更新时间：2026-08-18 11:55:15 +08:00
- GitHub `origin/main` contains the complete BEN Radar P02 through Stock Workbench V0.1 chain at commit `af0f478`. Runtime databases, caches, screenshots, unrelated YouTube benchmark research, local skills, and credentials remain local only.
- BEN RADAR Step 4 Stock Workbench V0.1 is complete; V0.1 anomaly rules and thresholds were not changed.
- Dynamic route: `http://127.0.0.1:8765/stock-radar` when the local Flask process is running.
- Public read-only EOD snapshot: `https://ben-finance-radar.nels-sedhq.chatgpt.site` (Sites version 4).
- Both surfaces use the 2026-08-17 Anomaly Engine Replay and show 20 clickable stocks with actual volume, prior-20 median, RVOL, liquidity, Chinese rule labels, explanations, and streak context.
- Stock detail uses real unified EOD OHLCV; 1M/3M candles, volume bars, and prior-20/prior-40 high lines are implemented. The bounded store currently supplies about 50 sessions, so 3M shows all available history rather than inventing missing days.
- Early momentum and persistence are display-only and do not alter ranking. Missing MOPS Evidence is shown as unconfirmed rather than inferred.
- Desktop 1280px and mobile 390px passed with no horizontal overflow or page console errors. Full repository check passed 94 tests plus credential scan; public Sites tests passed 2/2.
- Public snapshot refresh remains manual. Dynamic cold render recomputes six Replay dates and can take roughly 15–20 seconds before the in-process cache is warm.
- Recommended next task only if explicitly requested: human finance/content review of the 20 stocks and chart workflow; do not change rules from page impressions alone.
