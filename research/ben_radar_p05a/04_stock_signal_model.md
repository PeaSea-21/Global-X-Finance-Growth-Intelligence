# Stock signal model

- Universe actually available in `ben_stock_history`: **30** securities.
- Valid prior-20-session baselines on the latest official date: **30**.
- Produced signals: **30**; abnormal: **10**.
- Market IDs are qualified (`TWSE:2330` != `NYSE:TSM`).
- Relationships are carried from event Evidence (`DIRECT`, `SUPPLY_CHAIN`, `SECTOR`, `MACRO`, `POSSIBLE`).
- Missing price/turnover/baseline fields remain null and lower `data_quality`; they are never converted to zero.

Outputs: `hot_stocks.json`, `abnormal_stocks.json`, and one `stock_detail_*.json` payload.
