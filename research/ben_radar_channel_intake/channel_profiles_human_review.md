# ChannelProfile v0.1 DRAFT 业务审阅版

> 本文件是20频道草案，不是批准后的生产配置。`PROPOSED` 需要人工确认，`UNKNOWN` 不得自动补齐。

## 01. 個股顯微鏡

- ID：`ch-01-tw-stock-microscope`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`台股市場 / 基本面產業分析`；矩阵分类：`台股基本面`
- 原始矩阵行：台股基本面 | 個股顯微鏡 | 台股 | 基本面/白話分析 | 每週 1-2 集 | 5-8 分鐘
- 品牌家族：顯微鏡系列 / 台股單一公司的財務體質
- 市场/范围：`TW` / TWSE_COMMON_STOCK, TPEX_COMMON_STOCK
- 原始受众：台股中長期投資人、存股族、基本面研究者
- 原始频率：每週 1-2 集（每集 5-8 分鐘）
- 原始标签：#台股 #個股分析 #月營收 #法說會 #存股 #基本面
- 归纳 Topic：月營收; 法說會; 財報體質; 公司營運變化
- Why Channel：聚焦單一台股公司的營運與財務體質，不以盤面排行或跨公司輪動为主。
- 当前依赖：TWSE_TPEX_EOD; MOPS; MONTHLY_REVENUE_FINANCIALS_CALLS
- 主要缺口：月營收、完整財報、法說與 Guidance 未接入; 历史采用/拒绝样例未提供
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突

## 02. 收盤夜話

- ID：`ch-02-tw-close-night-talk`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`台股市場 / 基本面產業分析`；矩阵分类：`台股盤勢`
- 原始矩阵行：台股盤勢 | 收盤夜話 | 台股 | 盤後聊天/輕鬆 | 每交易日 | 15 分鐘
- 品牌家族：獨立品牌 / 下班後朋友聊盤的輕鬆氛圍
- 市场/范围：`TW` / TAIEX, TWSE_COMMON_STOCK, TPEX_COMMON_STOCK
- 原始受众：海外台人、白天無法盯盤的上班族、短線交易者
- 原始频率：每交易日（每集 15 分鐘）
- 原始标签：#台股收盤 #三大法人 #外資買賣超 #加權指數 #盤後分析
- 归纳 Topic：盤後結構; 法人買賣超; 融資券; 明日觀察
- Why Channel：面向无法盯盘的受众，用轻松口吻解释完整收盘结构；不做单股深度或长期产业报告。
- 当前依赖：TWSE_TPEX_EOD; MARKET_INDEX; INSTITUTIONAL_FLOW_MARGIN
- 主要缺口：三大法人、融資券、當沖比等完整盘后数据未验证; 频道近30天内容缺失
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突

## 03. 產業透視鏡

- ID：`ch-03-tw-industry-lens`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`台股市場 / 基本面產業分析`；矩阵分类：`台股產業`
- 原始矩阵行：台股產業 | 產業透視鏡 | 台股 | 產業深度/供應鏈 | 每週 1 集 | 5-10 分鐘
- 品牌家族：獨立品牌 / 穿透產業表面看底層邏輯
- 市场/范围：`TW` / TWSE_COMMON_STOCK, TPEX_COMMON_STOCK
- 原始受众：產業研究者、中階以上台股投資人、法人跟單者
- 原始频率：每週 1 集（每集 5-10 分鐘）
- 原始标签：#台股產業 #半導體 #AI伺服器 #供應鏈 #產能利用率
- 归纳 Topic：供應鏈; 產業月營收; 庫存週期; 產能利用率; 法人預期差
- Why Channel：以多公司上下游关系与产业基本面为核心，必须区分共现和已证实传导。
- 当前依赖：TWSE_TPEX_EOD; INDUSTRY_MAPPING; SUPPLY_CHAIN_DATA; CORPORATE_FUNDAMENTALS
- 主要缺口：Industry Mapping 未提交且未接 Topic; 供应链、BB值、库存与产能利用率未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance; excluded_topics
- 冲突：无已识别内部冲突

## 04. 權值旗艦

- ID：`ch-04-tw-weighted-flagship`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`台股市場 / 基本面產業分析`；矩阵分类：`台股大盤`
- 原始矩阵行：台股大盤 | 權值旗艦 | 台股 | 權值股/技術面 | 每週 2-3 集 | 5-8 分鐘
- 品牌家族：權衡系列 / 權值股對大盤的領跌領漲效應
- 市场/范围：`TW` / TAIEX, INDEX_FUTURES, WEIGHTED_STOCKS, ADR
- 原始受众：台指期交易者、權值股投資人、指數型 ETF 持有者
- 原始频率：每週 2-3 集（每集 5-8 分鐘）
- 原始标签：#台股大盤 #加權指數 #台積電 #權值股 #法人籌碼
- 归纳 Topic：大盤技術結構; 權值領漲領跌; 期現貨; 除權息
- Why Channel：以权值股对指数的贡献和期现货结构判断大盘，不做全市场聊天摘要。
- 当前依赖：TWSE_TPEX_EOD; MARKET_INDEX; FUTURES_INSTITUTIONAL; ADR
- 主要缺口：期货未平仓、ADR溢价与完整法人筹码未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance; excluded_topics
- 冲突：无已识别内部冲突

## 05. 資金雷達

- ID：`ch-05-tw-capital-radar`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`台股市場 / 基本面產業分析`；矩阵分类：`台股輪動`
- 原始矩阵行：台股輪動 | 資金雷達 | 台股 | 資金流向/短線 | 每交易日 | 3-5 分鐘
- 品牌家族：雷達系列 / 台股產業間的資金搬家方向
- 市场/范围：`TW` / TWSE_COMMON_STOCK, TPEX_COMMON_STOCK, INDUSTRY_INDEX
- 原始受众：短中期交易者、產業 ETF 投資人、板塊輪動策略使用者
- 原始频率：每交易日（每集 3-5 分鐘）
- 原始标签：#台股產業輪動 #資金流向 #半導體 #AI伺服器 #PCB
- 归纳 Topic：成交量異動; 產業輪動; 強弱切換; 事件驅動族群
- Why Channel：用日频价格/量能和产业分组捕捉轮动，必须把成交异动与真实资金净流入分开。
- 当前依赖：TWSE_TPEX_EOD; ANOMALY_ENGINE; INDUSTRY_MAPPING; INSTITUTIONAL_FLOW
- 主要缺口：Industry Mapping 未接 Topic; 现有 EOD 异常不等于法人或 ETF 资金净流入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance; excluded_topics
- 冲突：无已识别内部冲突

## 06. 那指火箭

- ID：`ch-06-us-nasdaq-rocket`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`美股市場 / 科技板塊期權`；矩阵分类：`美股科技`
- 原始矩阵行：美股科技 | 那指火箭 | 美股 | 科技股/成長 | 每週 2-3 集 | 5-8 分鐘
- 品牌家族：獨立品牌 / 科技股衝上雲端的動能感
- 市场/范围：`US` / NASDAQ_100, US_TECH_STOCKS, NASDAQ_ETF
- 原始受众：美股科技股投資人、成長股策略使用者、NASDAQ ETF 持有者
- 原始频率：每週 2-3 集（每集 5-8 分鐘）
- 原始标签：#納斯達克 #NASDAQ100 #科技股 #AI晶片 #FAANG #輝達
- 归纳 Topic：指數展望; 科技財報; 產品週期; 成分股排行
- Why Channel：聚焦 Nasdaq 100 与科技成长赛道，不覆盖全市场板块配置。
- 当前依赖：US_EOD; EARNINGS_CALENDAR; INTERNATIONAL_NEWS
- 主要缺口：美股 EOD 与财报日历未接入; 国际新闻使用权未确认
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance; excluded_topics
- 冲突：无已识别内部冲突

## 07. 板塊輪動儀

- ID：`ch-07-us-sector-rotator`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`美股市場 / 科技板塊期權`；矩阵分类：`美股板塊`
- 原始矩阵行：美股板塊 | 板塊輪動儀 | 美股 | ETF/資產配置 | 每週 1 集 | 5-8 分鐘
- 品牌家族：獨立品牌 / 美股產業板塊的結構性輪動
- 市场/范围：`US` / S&P_500_SECTORS, SECTOR_ETF
- 原始受众：美股 ETF 投資人、板塊輪動策略使用者、中長期資產配置者
- 原始频率：每週 1 集（每集 5-8 分鐘）
- 原始标签：#美股板塊 #板塊輪動 #標普500 #科技股 #能源股 #ETF
- 归纳 Topic：板塊相對強弱; ETF資金; 財報季差異; 政策敏感度
- Why Channel：比较十一大板块的结构性轮动与配置，不把单一科技股事件当主产品。
- 当前依赖：US_EOD; SECTOR_ETF_FLOW; EARNINGS_MACRO_CALENDAR
- 主要缺口：美股板块 EOD、ETF 流量与日历未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance; excluded_topics
- 冲突：无已识别内部冲突

## 08. 暗池雷達

- ID：`ch-08-us-dark-pool-radar`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`美股市場 / 科技板塊期權`；矩阵分类：`美股暗池`
- 原始矩阵行：美股暗池 | 暗池雷達 | 美股 | 籌碼/期權 | 每交易日開盤前 | 3-5 分鐘
- 品牌家族：雷達系列 / 美股暗池與期權的聰明錢動向
- 市场/范围：`US` / US_EQUITIES, US_OPTIONS, DARK_POOL
- 原始受众：期權交易者、短線波段客、希望追蹤主力資金走向的實戰派
- 原始频率：每交易日開盤前（每集 3-5 分鐘）
- 原始标签：#暗池交易 #期權異動 #主力資金 #華爾街 #聰明錢 #美股實戰
- 归纳 Topic：暗池大單; Option Sweeps; Gamma; 異常建倉
- Why Channel：追踪暗池/期权异常交易，而非宏观风险或长期基本面；必须避免把订单流直接解释成机构意图。
- 当前依赖：OPTIONS_DARK_POOL_FEED; US_EOD; US_SESSION_CLOCK
- 主要缺口：暗池与期权流数据均未接入; “聪明钱真实选择”需证据边界
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突

## 09. 期權守門人

- ID：`ch-09-us-options-gatekeeper`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`美股市場 / 科技板塊期權`；矩阵分类：`美股期權`
- 原始矩阵行：美股期權 | 期權守門人 | 美股 | 風險管理/賣方 | 每交易日開盤前 | 3 分鐘
- 品牌家族：守護系列 / 現貨持倉的下行風險與現金流
- 市场/范围：`US` / US_OPTIONS, US_EQUITY_HOLDINGS
- 原始受众：擁有美股現貨持倉、希望降低回撤或獲取額外現金流的理性交易者
- 原始频率：每交易日開盤前（每集約 3 分鐘）
- 原始标签：#美股期權 #期權策略 #波動率 #對沖風險 #現金流 #風險管理
- 归纳 Topic：波動率曲面; 賣方策略; 對沖; Covered Call; Cash-Secured Put
- Why Channel：风险管理与策略教育优先，不是方向下注或异常订单追踪。
- 当前依赖：OPTIONS_CHAIN_IV; US_EOD; RISK_MODEL
- 主要缺口：期权链、IV Rank、组合风险数据未接入; 策略适用性与风险披露规则未确认
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突

## 10. 財報獵人

- ID：`ch-10-us-earnings-hunter`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`美股市場 / 科技板塊期權`；矩阵分类：`美股財報`
- 原始矩阵行：美股財報 | 財報獵人 | 美股 | 基本面/SEC 原檔 | 財報季每日/非財報季每週 2 集 | 3 分鐘
- 品牌家族：獨立品牌 / 獵人般精準捕獲財報真相
- 市场/范围：`US` / US_LISTED_COMPANIES, SEC_FILINGS
- 原始受众：美股基本面派投資者、喜歡深挖企業核心財務數據的研究型股民
- 原始频率：財報季每日／非財報季每週 2 集（每集約 3 分鐘）
- 原始标签：#美股財報 #基本面分析 #10K拆解 #自由現金流 #科技巨頭 #財務分析
- 归纳 Topic：10-K; 10-Q; GAAP與Non-GAAP; 自由現金流; Guidance
- Why Channel：直接核对 SEC 原档与会计质量，不以新闻转述或股价异动代替财报分析。
- 当前依赖：SEC_FILINGS; EARNINGS_CALENDAR; US_EOD
- 主要缺口：SEC 与财报日历未接入; 美股 EOD 未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突

## 11. 宏觀天秤

- ID：`ch-11-global-macro-balance`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`全球宏觀 / 資金流向大宗商品`；矩阵分类：`全球宏觀`
- 原始矩阵行：全球宏觀 | 宏觀天秤 | 全球 | 宏觀/央行/利率 | 每週日晚間 | 5 分鐘
- 品牌家族：權衡系列 / 全球資產的相對價值與週期位置
- 市场/范围：`GLOBAL` / RATES, FX, BONDS, EQUITIES, GOLD, EM
- 原始受众：追求中長期穩健增值、希望建立全局宏觀視角的高階投資者
- 原始频率：每週日晚間發佈（約 5 分鐘）
- 原始标签：#宏觀經濟 #資產配置 #美債 #全球市場 #利率決議 #大類資產 #投資週期
- 归纳 Topic：央行決議; 利率路徑; CPI; PMI; NFP; 週期定位
- Why Channel：以央行、经济数据和跨资产周期构建应对方案，不做单日个股方向预测。
- 当前依赖：MACRO_CALENDAR; GLOBAL_MARKET_EOD; OFFICIAL_MACRO_DATA
- 主要缺口：宏观日历与全球资产数据未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突

## 12. 全球資金地圖

- ID：`ch-12-global-capital-map`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`全球宏觀 / 資金流向大宗商品`；矩阵分类：`全球資金`
- 原始矩阵行：全球資金 | 全球資金地圖 | 全球 | 資金流向/跨市場 | 每週 1-2 集 | 5-8 分鐘
- 品牌家族：獨立品牌 / 跨市場資金移動的全景地圖
- 市场/范围：`GLOBAL` / GLOBAL_ETF, BONDS, FX, GOLD, EM_EQUITIES
- 原始受众：全球資產配置者、宏觀對沖策略使用者、避險需求投資人
- 原始频率：每週 1-2 集（每集 5-8 分鐘）
- 原始标签：#全球資金流向 #ETF流量 #避險資產 #美債 #黃金 #日圓
- 归纳 Topic：ETF申贖; 殖利率曲線; 避險流向; 風險情緒
- Why Channel：核心是跨市场资金迁移路径，不等同于宏观周期叙事或单一美股情绪指标。
- 当前依赖：GLOBAL_ETF_FLOW; GLOBAL_EOD; FX_RATES
- 主要缺口：全球 ETF 申赎、债券、汇率与避险资产数据未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance; excluded_topics
- 冲突：无已识别内部冲突

## 13. 地緣炸藥庫

- ID：`ch-13-geopolitical-powder-keg`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`全球宏觀 / 資金流向大宗商品`；矩阵分类：`地緣大宗`
- 原始矩阵行：地緣大宗 | 地緣炸藥庫 | 全球 | 事件驅動/避險 | 事件觸發＋週日回顧 | 3-8 分鐘
- 品牌家族：獨立品牌 / 地緣事件一觸即發的緊張感
- 市场/范围：`GLOBAL` / OIL, GOLD, COPPER, NATURAL_GAS, GRAINS
- 原始受众：大宗商品交易者、避險需求投資人、地緣政治敏感型資產持有者
- 原始频率：事件觸發即發佈＋週日回顧（每集 3-8 分鐘）
- 原始标签：#地緣政治 #原油 #黃金 #大宗商品 #避險 #供應鏈
- 归纳 Topic：地緣事件; 制裁; 供應鏈中斷; 商品傳導
- Why Channel：只在重大地缘事件或商品异动时发布，强调传导路径而非日常商品周期。
- 当前依赖：AUTHORIZED_INTERNATIONAL_NEWS; COMMODITY_EOD; SUPPLY_CHAIN_EVIDENCE
- 主要缺口：国际新闻权利与大宗商品行情未接入; 事件触发频道不适合固定每日满额
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突

## 14. 週期航海家

- ID：`ch-14-commodity-cycle-navigator`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`全球宏觀 / 資金流向大宗商品`；矩阵分类：`週期商品`
- 原始矩阵行：週期商品 | 週期航海家 | 全球 | 大宗商品/週期 | 每週二、週五 | 2-5 分鐘
- 品牌家族：獨立品牌 / 大宗商品週期的風浪航行
- 市场/范围：`GLOBAL` / COMMODITY_FUTURES, RESOURCE_STOCKS, FREIGHT
- 原始受众：關注抗通脹資產、大宗商品期貨與資源類股票的週期投資者
- 原始频率：每週二、週五更新（每集 2-5 分鐘）
- 原始标签：#大宗商品 #黃金 #原油 #銅價 #週期投資 #通脹對沖 #資源股
- 归纳 Topic：供需庫存; 資源股映射; 金銀比; 油金比; 通脹對沖
- Why Channel：以库存、供需与资源股映射解释中期商品周期，不以突发地缘新闻为唯一驱动。
- 当前依赖：COMMODITY_EOD; LME_SHFE_INVENTORY; BDI; RESOURCE_FILINGS
- 主要缺口：商品、库存、运价与资源股数据未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance; excluded_topics
- 冲突：无已识别内部冲突

## 15. 鏈上顯微鏡

- ID：`ch-15-onchain-microscope`；状态：`DRAFT_WITH_CONFLICT`
- 原始分类：`鏈上數據 / 籌碼分析`；矩阵分类：`鏈上數據`
- 原始矩阵行：鏈上數據 | 鏈上顯微鏡 | 加密貨幣 | 鏈上/籌碼 | 每交易日 | 3-5 分鐘
- 品牌家族：顯微鏡系列 / 加密貨幣的鏈上籌碼流向
- 市场/范围：`CRYPTO` / CRYPTO_ASSETS, DERIVATIVES
- 原始受众：注重數據佐證、喜歡研究籌碼分佈與資金博弈的深度交易者
- 原始频率：每交易日收盤後（每集 3-5 分鐘）
- 原始标签：#籌碼分析 #鏈上數據 #資金流向 #主力動向 #衍生品 #交易系統 #數據驅動
- 归纳 Topic：鏈上轉帳; 籌碼成本; 清算; OI; 質押
- Why Channel：使用链上和衍生品数据解释筹码，不是股票暗池或传统市场资金流。
- 当前依赖：ONCHAIN_PROVIDER; DERIVATIVES_OI_LIQUIDATION; CRYPTO_CLOCK
- 主要缺口：链上、OI、清算与质押数据均未接入; 加密市场24/7但原文使用‘交易日收盘后’，时点需确认
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：加密市场为24/7，但资料使用‘每交易日收盘后’，业务截止时点不明确。

## 16. 中概風向球

- ID：`ch-16-china-adr-weather-vane`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`中概股 / 地緣政治`；矩阵分类：`中概股`
- 原始矩阵行：中概股 | 中概風向球 | 美股中概 | 地緣/流動性 | 每交易日 | 3-4 分鐘
- 品牌家族：獨立品牌 / 中概股與美元流動性的即時變化
- 市场/范围：`US_CHINA_ADR` / CHINA_ADR, US_TECH, FX, 13F
- 原始受众：關注美股、中概股及跨國資本流動的配置型投資者
- 原始频率：每交易日收盤後（每集 3-4 分鐘）
- 原始标签：#美股 #中概股 #美元指數 #離岸人民幣 #地緣政治 #半導體 #機構持倉
- 归纳 Topic：美元流動性; 機構持倉; 估值折溢價; 地緣政治
- Why Channel：专注中概资产在美元流动性和地缘框架下的定价，不等同于美股科技或全球ETF总览。
- 当前依赖：US_CHINA_ADR_EOD; FX; 13F; AUTHORIZED_NEWS
- 主要缺口：美股/中概行情、DXY/CNH、13F与新闻授权未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance; excluded_topics
- 冲突：无已识别内部冲突

## 17. 財商拆彈組

- ID：`ch-17-financial-literacy-bomb-squad`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`理財教育 / 定投策略`；矩阵分类：`理財教育`
- 原始矩阵行：理財教育 | 財商拆彈組 | 通用 | 小白科普/避坑 | 每日 18:00 | 3 分鐘
- 品牌家族：守護系列 / 小白投資人的血汗錢不被割韭菜
- 市场/范围：`GENERAL` / ETF, BONDS, FUNDS, RETAIL_PRODUCTS
- 原始受众：理財新手、職場小白、希望保護血汗錢並建立健康理財觀念的所有人
- 原始频率：每日 18:00 準時拆彈（每集 3 分鐘）
- 原始标签：#財商思維 #理財避坑 #理財入門 #小白理財 #防割韭菜 #金融科普 #財富增值
- 归纳 Topic：金融陷阱; 費用; 基礎科普; 防詐; 情緒風險
- Why Channel：以白话事实核查和避坑教育为主，不输出具体标的买卖建议。
- 当前依赖：OFFICIAL_REGULATOR; PRODUCT_TERMS; AUTHORIZED_CASES
- 主要缺口：消费者金融产品、监管与诈骗案例来源未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突

## 18. 半導體駭客

- ID：`ch-18-semiconductor-hacker`；状态：`DRAFT_WITH_CONFLICT`
- 原始分类：`理財教育 / 定投策略`；矩阵分类：`半導體`
- 原始矩阵行：半導體 | 半導體駭客 | 台股＋美股 | 硬核產業/技術 | 每週三、週五 | 3-5 分鐘
- 品牌家族：獨立品牌 / 硬核技術視角透視半導體供應鏈
- 市场/范围：`TW_US` / SEMICONDUCTOR_STOCKS, SUPPLY_CHAIN
- 原始受众：科技股投資者、半導體從業者、關注 AI 硬體底座的理智研究者
- 原始频率：每週三、週五（每集 3-5 分鐘）
- 原始标签：#半導體 #台積電 #AI晶片 #先進封裝 #光刻機 #科技股 #供應鏈 #硬體架構
- 归纳 Topic：技術路線; 良率; 產能; 設備材料; 供應鏈訂單
- Why Channel：跨台美与上下游解释技术壁垒，技术与订单事实必须可核验，不能由股价共现反推。
- 当前依赖：TWSE_TPEX_EOD; US_EOD; SUPPLY_CHAIN_MAPPING; TECHNICAL_SOURCES
- 主要缺口：美股 EOD 与技术/供应链来源未接入; 目录归为理财教育但矩阵归为半导体
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：目录/正文归类为‘理財教育 / 定投策略’，跨分类矩阵归类为‘半導體’。

## 19. 華爾街溫度計

- ID：`ch-19-wall-street-thermometer`；状态：`DRAFT_WITH_CONFLICT`
- 原始分类：`理財教育 / 定投策略`；矩阵分类：`美股資金`
- 原始矩阵行：美股資金 | 華爾街溫度計 | 美股 | 資金面/情緒指標 | 每週 2-3 集 | 3-5 分鐘
- 品牌家族：獨立品牌 / 市場貪婪與恐慌的真實溫度
- 市场/范围：`US` / US_ETF, US_OPTIONS, US_MARGIN
- 原始受众：美股短中期交易者、風險管理型投資人、ETF 操作者
- 原始频率：每週 2-3 集（每集 3-5 分鐘）
- 原始标签：#美股資金流向 #VIX #PutCall比率 #ETF流量 #機構持倉 #市場溫度
- 归纳 Topic：ETF流向; Put/Call; VIX; 13F; 融資餘額
- Why Channel：以美股资金面和风险情绪仪表为主，不把单一暗池订单或全球宏观周期当结论。
- 当前依赖：US_EOD; ETF_FLOW; OPTIONS_SENTIMENT; 13F_MARGIN
- 主要缺口：美股 EOD、ETF流量、VIX/PutCall、13F和融资数据未接入; 目录归为理财教育但矩阵归为美股资金
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：目录/正文归类为‘理財教育 / 定投策略’，跨分类矩阵归类为‘美股資金’。

## 20. 定投實驗室

- ID：`ch-20-dca-lab`；状态：`DRAFT_NEEDS_HUMAN_CONFIRMATION`
- 原始分类：`理財教育 / 定投策略`；矩阵分类：`定投策略`
- 原始矩阵行：定投策略 | 定投實驗室 | 通用 | 量化回測/長期 | 每週日上午 | 5-8 分鐘
- 品牌家族：獨立品牌 / 科學實驗精神驗證定投策略
- 市场/范围：`GENERAL` / BROAD_INDEX_ETF, SECTOR_ETF
- 原始受众：上班族、定期定額投資者、希望通過 ETF 實現無腦穩健增值的長線派
- 原始频率：每週日上午（每集 5-8 分鐘）
- 原始标签：#指數基金 #ETF定投 #標普500 #納斯達克 #複利效應 #資產積累 #量化回測 #長期投資
- 归纳 Topic：長期回測; 價值平均; 網格; 費率; 跟蹤誤差; 心理紀律
- Why Channel：用长周期可复现回测做策略教育，不把当日热点或短期收益外推成保证。
- 当前依赖：LONG_HISTORY; ETF_REFERENCE_DATA; BACKTEST_ENGINE
- 主要缺口：10-30年历史、ETF费率/跟踪误差与回测引擎未接入
- 提议 Evidence 政策：`FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE`
- 提议配额：主候选5、备选0-3；不足使用 `HONEST_SHORTAGE`
- 缺失字段：channel_owner; channel_priority; positive_examples; negative_examples; recent_30d_adopted_topics; do_not_repeat_patterns; approved_excluded_topics; approved_evidence_policy; approved_risk_tolerance
- 冲突：无已识别内部冲突
