from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path(
    r"C:\Users\yinen\.codex\attachments\7d3e19f0-9589-41cc-a0f2-1e586a952303\pasted-text.txt"
)
OUT = ROOT / "research" / "ben_radar_channel_intake"
DELIVERABLE = ROOT / "deliverables" / "BEN_RADAR_20频道画像与三频道试点建议_P06A.md"

PROVENANCE = {
    "SUPPLIED",
    "DERIVED_FROM_SUPPLIED",
    "PROPOSED",
    "UNKNOWN",
    "CONFLICT",
}
CAPABILITY_STATES = {
    "AVAILABLE_VERIFIED",
    "AVAILABLE_BUT_PROTOTYPE",
    "PARTIAL",
    "UNKNOWN",
    "BLOCKED_RIGHTS",
    "NOT_IMPLEMENTED",
}

GLOBAL_RISK = (
    "本頻道所有內容僅為資訊分享與學術研討，不構成任何具體買賣建議。"
    "市場有風險，投資需謹慎。請根據自身財務狀況與風險承受能力，"
    "獨立評估並做出投資決策。"
)


def c(
    name: str,
    slug: str,
    directory_category: str,
    matrix_category: str,
    primary_market: str,
    secondary_markets: list[str],
    security_scope: list[str],
    sectors: list[str],
    entities: list[str],
    topic_types: list[str],
    depth: str,
    session: list[str],
    max_age: str,
    closest: list[str],
    distinction: str,
    same_event_probability: str,
    collision_risk: str,
    dependencies: list[str],
    gaps: list[str],
    feasibility: str,
    excluded: list[str] | None = None,
    category_conflict: bool = False,
) -> dict:
    return locals()


CHANNELS = [
    c("個股顯微鏡", "tw-stock-microscope", "台股市場 / 基本面產業分析", "台股基本面", "TW", [], ["TWSE_COMMON_STOCK", "TPEX_COMMON_STOCK"], [], ["台股上市櫃公司"], ["月營收", "法說會", "財報體質", "公司營運變化"], "DEEP_COMPANY", ["WEEKLY", "POST_DISCLOSURE"], "UNTIL_NEXT_MATERIAL_UPDATE", ["財報獵人", "產業透視鏡", "權值旗艦"], "聚焦單一台股公司的營運與財務體質，不以盤面排行或跨公司輪動为主。", "MEDIUM", "MEDIUM", ["TWSE_TPEX_EOD", "MOPS", "MONTHLY_REVENUE_FINANCIALS_CALLS"], ["月營收、完整財報、法說與 Guidance 未接入", "历史采用/拒绝样例未提供"], "MEDIUM", ["盤面雜訊", "無公司營運證據的短線題材"]),
    c("收盤夜話", "tw-close-night-talk", "台股市場 / 基本面產業分析", "台股盤勢", "TW", [], ["TAIEX", "TWSE_COMMON_STOCK", "TPEX_COMMON_STOCK"], ["大盤", "類股"], ["加權指數", "三大法人"], ["盤後結構", "法人買賣超", "融資券", "明日觀察"], "DAILY_SUMMARY", ["TW_CLOSE"], "SAME_TRADING_DAY", ["權值旗艦", "資金雷達"], "面向无法盯盘的受众，用轻松口吻解释完整收盘结构；不做单股深度或长期产业报告。", "HIGH", "HIGH", ["TWSE_TPEX_EOD", "MARKET_INDEX", "INSTITUTIONAL_FLOW_MARGIN"], ["三大法人、融資券、當沖比等完整盘后数据未验证", "频道近30天内容缺失"], "MEDIUM", ["複雜總經理論"]),
    c("產業透視鏡", "tw-industry-lens", "台股市場 / 基本面產業分析", "台股產業", "TW", [], ["TWSE_COMMON_STOCK", "TPEX_COMMON_STOCK"], ["半導體", "AI伺服器", "PCB", "散熱", "電子零組件"], ["台股產業鏈上下游"], ["供應鏈", "產業月營收", "庫存週期", "產能利用率", "法人預期差"], "DEEP_CROSS_ENTITY", ["WEEKLY", "POST_INDUSTRY_EVENT"], "ONE_WEEK_OR_NEXT_MATERIAL_UPDATE", ["半導體駭客", "資金雷達", "個股顯微鏡"], "以多公司上下游关系与产业基本面为核心，必须区分共现和已证实传导。", "HIGH", "HIGH", ["TWSE_TPEX_EOD", "INDUSTRY_MAPPING", "SUPPLY_CHAIN_DATA", "CORPORATE_FUNDAMENTALS"], ["Industry Mapping 未提交且未接 Topic", "供应链、BB值、库存与产能利用率未接入"], "MEDIUM"),
    c("權值旗艦", "tw-weighted-flagship", "台股市場 / 基本面產業分析", "台股大盤", "TW", ["US"], ["TAIEX", "INDEX_FUTURES", "WEIGHTED_STOCKS", "ADR"], ["權值股", "半導體", "金融"], ["台積電", "聯發科", "鴻海"], ["大盤技術結構", "權值領漲領跌", "期現貨", "除權息"], "MARKET_STRUCTURE", ["WEEKLY_2_3", "POST_CLOSE"], "SAME_TRADING_WEEK", ["收盤夜話", "那指火箭", "資金雷達"], "以权值股对指数的贡献和期现货结构判断大盘，不做全市场聊天摘要。", "HIGH", "HIGH", ["TWSE_TPEX_EOD", "MARKET_INDEX", "FUTURES_INSTITUTIONAL", "ADR"], ["期货未平仓、ADR溢价与完整法人筹码未接入"], "MEDIUM"),
    c("資金雷達", "tw-capital-radar", "台股市場 / 基本面產業分析", "台股輪動", "TW", [], ["TWSE_COMMON_STOCK", "TPEX_COMMON_STOCK", "INDUSTRY_INDEX"], ["22大產業", "半導體", "AI伺服器", "散熱", "PCB", "生技"], ["台股產業群組"], ["成交量異動", "產業輪動", "強弱切換", "事件驅動族群"], "FAST_SIGNAL", ["TW_EOD_EACH_TRADING_DAY"], "SAME_TRADING_DAY", ["產業透視鏡", "收盤夜話", "華爾街溫度計"], "用日频价格/量能和产业分组捕捉轮动，必须把成交异动与真实资金净流入分开。", "HIGH", "HIGH", ["TWSE_TPEX_EOD", "ANOMALY_ENGINE", "INDUSTRY_MAPPING", "INSTITUTIONAL_FLOW"], ["Industry Mapping 未接 Topic", "现有 EOD 异常不等于法人或 ETF 资金净流入"], "HIGH"),
    c("那指火箭", "us-nasdaq-rocket", "美股市場 / 科技板塊期權", "美股科技", "US", [], ["NASDAQ_100", "US_TECH_STOCKS", "NASDAQ_ETF"], ["科技", "AI晶片", "雲端"], ["Meta", "Apple", "Amazon", "Netflix", "Google", "NVIDIA", "AMD", "Broadcom", "Microsoft"], ["指數展望", "科技財報", "產品週期", "成分股排行"], "GROWTH_TECH", ["US_WEEKLY_2_3", "ASIA_AFTER_US_CLOSE"], "ONE_US_TRADING_WEEK", ["半導體駭客", "板塊輪動儀", "財報獵人"], "聚焦 Nasdaq 100 与科技成长赛道，不覆盖全市场板块配置。", "HIGH", "HIGH", ["US_EOD", "EARNINGS_CALENDAR", "INTERNATIONAL_NEWS"], ["美股 EOD 与财报日历未接入", "国际新闻使用权未确认"], "LOW"),
    c("板塊輪動儀", "us-sector-rotator", "美股市場 / 科技板塊期權", "美股板塊", "US", [], ["S&P_500_SECTORS", "SECTOR_ETF"], ["科技", "能源", "金融", "生技", "醫療"], ["XLK", "XLF", "XLE", "XLV"], ["板塊相對強弱", "ETF資金", "財報季差異", "政策敏感度"], "ASSET_ALLOCATION", ["US_WEEKLY", "ASIA_AFTER_US_CLOSE"], "ONE_US_TRADING_WEEK", ["華爾街溫度計", "全球資金地圖", "那指火箭"], "比较十一大板块的结构性轮动与配置，不把单一科技股事件当主产品。", "HIGH", "HIGH", ["US_EOD", "SECTOR_ETF_FLOW", "EARNINGS_MACRO_CALENDAR"], ["美股板块 EOD、ETF 流量与日历未接入"], "LOW"),
    c("暗池雷達", "us-dark-pool-radar", "美股市場 / 科技板塊期權", "美股暗池", "US", [], ["US_EQUITIES", "US_OPTIONS", "DARK_POOL"], [], ["美股機構交易"], ["暗池大單", "Option Sweeps", "Gamma", "異常建倉"], "TACTICAL_DERIVATIVES", ["US_PREMARKET_EACH_TRADING_DAY"], "PREVIOUS_US_SESSION", ["期權守門人", "華爾街溫度計"], "追踪暗池/期权异常交易，而非宏观风险或长期基本面；必须避免把订单流直接解释成机构意图。", "MEDIUM", "HIGH", ["OPTIONS_DARK_POOL_FEED", "US_EOD", "US_SESSION_CLOCK"], ["暗池与期权流数据均未接入", "“聪明钱真实选择”需证据边界"], "NOT_FEASIBLE", ["盤後念新聞", "無數據的方向猜測"]),
    c("期權守門人", "us-options-gatekeeper", "美股市場 / 科技板塊期權", "美股期權", "US", [], ["US_OPTIONS", "US_EQUITY_HOLDINGS"], [], ["US options chains"], ["波動率曲面", "賣方策略", "對沖", "Covered Call", "Cash-Secured Put"], "RISK_EDUCATION", ["US_PREMARKET_EACH_TRADING_DAY"], "PREVIOUS_US_SESSION", ["暗池雷達", "財商拆彈組", "華爾街溫度計"], "风险管理与策略教育优先，不是方向下注或异常订单追踪。", "MEDIUM", "MEDIUM", ["OPTIONS_CHAIN_IV", "US_EOD", "RISK_MODEL"], ["期权链、IV Rank、组合风险数据未接入", "策略适用性与风险披露规则未确认"], "NOT_FEASIBLE", ["單邊方向狂熱賭博"]),
    c("財報獵人", "us-earnings-hunter", "美股市場 / 科技板塊期權", "美股財報", "US", [], ["US_LISTED_COMPANIES", "SEC_FILINGS"], ["科技", "消費"], ["美股科技與消費巨頭"], ["10-K", "10-Q", "GAAP與Non-GAAP", "自由現金流", "Guidance"], "DEEP_FINANCIAL", ["EARNINGS_SEASON_DAILY", "OFF_SEASON_TWICE_WEEKLY"], "UNTIL_NEXT_FILING", ["個股顯微鏡", "那指火箭"], "直接核对 SEC 原档与会计质量，不以新闻转述或股价异动代替财报分析。", "MEDIUM", "MEDIUM", ["SEC_FILINGS", "EARNINGS_CALENDAR", "US_EOD"], ["SEC 与财报日历未接入", "美股 EOD 未接入"], "LOW", ["只看二手新聞稿", "無原檔的會計結論"]),
    c("宏觀天秤", "global-macro-balance", "全球宏觀 / 資金流向大宗商品", "全球宏觀", "GLOBAL", [], ["RATES", "FX", "BONDS", "EQUITIES", "GOLD", "EM"], ["大類資產"], ["Fed", "ECB", "BOJ"], ["央行決議", "利率路徑", "CPI", "PMI", "NFP", "週期定位"], "MACRO_STRATEGY", ["WEEKLY_SUNDAY"], "ONE_WEEK_OR_NEXT_RELEASE", ["全球資金地圖", "週期航海家", "地緣炸藥庫"], "以央行、经济数据和跨资产周期构建应对方案，不做单日个股方向预测。", "HIGH", "MEDIUM", ["MACRO_CALENDAR", "GLOBAL_MARKET_EOD", "OFFICIAL_MACRO_DATA"], ["宏观日历与全球资产数据未接入"], "LOW", ["單一市場微觀雜訊", "無情境的市場預測"]),
    c("全球資金地圖", "global-capital-map", "全球宏觀 / 資金流向大宗商品", "全球資金", "GLOBAL", ["TW", "US"], ["GLOBAL_ETF", "BONDS", "FX", "GOLD", "EM_EQUITIES"], ["跨資產"], ["美股ETF", "美債", "日圓", "黃金", "新興市場"], ["ETF申贖", "殖利率曲線", "避險流向", "風險情緒"], "CROSS_ASSET_FLOW", ["WEEKLY_1_2"], "ONE_WEEK", ["宏觀天秤", "華爾街溫度計", "板塊輪動儀"], "核心是跨市场资金迁移路径，不等同于宏观周期叙事或单一美股情绪指标。", "HIGH", "HIGH", ["GLOBAL_ETF_FLOW", "GLOBAL_EOD", "FX_RATES"], ["全球 ETF 申赎、债券、汇率与避险资产数据未接入"], "LOW"),
    c("地緣炸藥庫", "geopolitical-powder-keg", "全球宏觀 / 資金流向大宗商品", "地緣大宗", "GLOBAL", [], ["OIL", "GOLD", "COPPER", "NATURAL_GAS", "GRAINS"], ["能源", "金屬", "農產品"], ["中東", "俄烏", "台海", "荷姆茲海峽"], ["地緣事件", "制裁", "供應鏈中斷", "商品傳導"], "EVENT_DRIVEN", ["EVENT_TRIGGER", "WEEKLY_SUNDAY_REVIEW"], "EVENT_DEPENDENT", ["週期航海家", "宏觀天秤"], "只在重大地缘事件或商品异动时发布，强调传导路径而非日常商品周期。", "MEDIUM", "MEDIUM", ["AUTHORIZED_INTERNATIONAL_NEWS", "COMMODITY_EOD", "SUPPLY_CHAIN_EVIDENCE"], ["国际新闻权利与大宗商品行情未接入", "事件触发频道不适合固定每日满额"], "LOW", ["平時常態個股分析"]),
    c("週期航海家", "commodity-cycle-navigator", "全球宏觀 / 資金流向大宗商品", "週期商品", "GLOBAL", [], ["COMMODITY_FUTURES", "RESOURCE_STOCKS", "FREIGHT"], ["黃金", "原油", "銅", "鐵礦石"], ["LME", "SHFE", "BDI", "礦業公司"], ["供需庫存", "資源股映射", "金銀比", "油金比", "通脹對沖"], "COMMODITY_CYCLE", ["WEEKLY_TUE_FRI"], "HALF_WEEK", ["地緣炸藥庫", "宏觀天秤", "全球資金地圖"], "以库存、供需与资源股映射解释中期商品周期，不以突发地缘新闻为唯一驱动。", "HIGH", "MEDIUM", ["COMMODITY_EOD", "LME_SHFE_INVENTORY", "BDI", "RESOURCE_FILINGS"], ["商品、库存、运价与资源股数据未接入"], "LOW"),
    c("鏈上顯微鏡", "onchain-microscope", "鏈上數據 / 籌碼分析", "鏈上數據", "CRYPTO", [], ["CRYPTO_ASSETS", "DERIVATIVES"], ["加密貨幣"], ["巨鯨地址", "交易所", "質押合約"], ["鏈上轉帳", "籌碼成本", "清算", "OI", "質押"], "ONCHAIN_TACTICAL", ["DAILY_AFTER_DEFINED_CUTOFF"], "ONE_CRYPTO_BUSINESS_CUTOFF", ["暗池雷達", "華爾街溫度計"], "使用链上和衍生品数据解释筹码，不是股票暗池或传统市场资金流。", "LOW", "LOW", ["ONCHAIN_PROVIDER", "DERIVATIVES_OI_LIQUIDATION", "CRYPTO_CLOCK"], ["链上、OI、清算与质押数据均未接入", "加密市场24/7但原文使用‘交易日收盘后’，时点需确认"], "NOT_FEASIBLE", ["無鏈上證據的主力意圖推測"]),
    c("中概風向球", "china-adr-weather-vane", "中概股 / 地緣政治", "中概股", "US_CHINA_ADR", ["US", "CN", "HK"], ["CHINA_ADR", "US_TECH", "FX", "13F"], ["中概股", "半導體", "硬科技"], ["中國ADR", "DXY", "CNH", "13F機構"], ["美元流動性", "機構持倉", "估值折溢價", "地緣政治"], "CROSS_BORDER_EQUITY", ["EACH_US_TRADING_DAY_AFTER_CLOSE"], "PREVIOUS_US_SESSION", ["那指火箭", "全球資金地圖", "半導體駭客"], "专注中概资产在美元流动性和地缘框架下的定价，不等同于美股科技或全球ETF总览。", "HIGH", "HIGH", ["US_CHINA_ADR_EOD", "FX", "13F", "AUTHORIZED_NEWS"], ["美股/中概行情、DXY/CNH、13F与新闻授权未接入"], "NOT_FEASIBLE"),
    c("財商拆彈組", "financial-literacy-bomb-squad", "理財教育 / 定投策略", "理財教育", "GENERAL", [], ["ETF", "BONDS", "FUNDS", "RETAIL_PRODUCTS"], ["理財教育"], ["理財新手"], ["金融陷阱", "費用", "基礎科普", "防詐", "情緒風險"], "BEGINNER_EDUCATION", ["DAILY_1800"], "CURRENT_POLICY_OR_PRODUCT_TERMS", ["期權守門人", "定投實驗室"], "以白话事实核查和避坑教育为主，不输出具体标的买卖建议。", "LOW", "LOW", ["OFFICIAL_REGULATOR", "PRODUCT_TERMS", "AUTHORIZED_CASES"], ["消费者金融产品、监管与诈骗案例来源未接入"], "LOW", ["具體買賣建議", "高收益承諾"]),
    c("半導體駭客", "semiconductor-hacker", "理財教育 / 定投策略", "半導體", "TW_US", ["TW", "US", "KR", "EU"], ["SEMICONDUCTOR_STOCKS", "SUPPLY_CHAIN"], ["晶圓代工", "先進封裝", "設備材料", "AI晶片", "HBM"], ["台積電", "三星", "英特爾", "ASML", "應用材料"], ["技術路線", "良率", "產能", "設備材料", "供應鏈訂單"], "TECHNICAL_CROSS_ENTITY", ["WEEKLY_WED_FRI"], "HALF_WEEK_OR_NEXT_TECH_EVENT", ["產業透視鏡", "那指火箭", "中概風向球"], "跨台美与上下游解释技术壁垒，技术与订单事实必须可核验，不能由股价共现反推。", "HIGH", "HIGH", ["TWSE_TPEX_EOD", "US_EOD", "SUPPLY_CHAIN_MAPPING", "TECHNICAL_SOURCES"], ["美股 EOD 与技术/供应链来源未接入", "目录归为理财教育但矩阵归为半导体"], "LOW", ["無證據的概念炒作"], True),
    c("華爾街溫度計", "wall-street-thermometer", "理財教育 / 定投策略", "美股資金", "US", [], ["US_ETF", "US_OPTIONS", "US_MARGIN"], ["美股資金面"], ["SPY", "QQQ", "IWM", "VIX"], ["ETF流向", "Put/Call", "VIX", "13F", "融資餘額"], "MARKET_SENTIMENT", ["US_WEEKLY_2_3", "ASIA_AFTER_US_CLOSE"], "ONE_US_TRADING_WEEK", ["板塊輪動儀", "全球資金地圖", "暗池雷達"], "以美股资金面和风险情绪仪表为主，不把单一暗池订单或全球宏观周期当结论。", "HIGH", "HIGH", ["US_EOD", "ETF_FLOW", "OPTIONS_SENTIMENT", "13F_MARGIN"], ["美股 EOD、ETF流量、VIX/PutCall、13F和融资数据未接入", "目录归为理财教育但矩阵归为美股资金"], "NOT_FEASIBLE", ["無數據的漲跌猜測"], True),
    c("定投實驗室", "dca-lab", "理財教育 / 定投策略", "定投策略", "GENERAL", ["TW", "US"], ["BROAD_INDEX_ETF", "SECTOR_ETF"], ["寬基指數", "行業ETF"], ["S&P 500", "NASDAQ 100", "台灣50"], ["長期回測", "價值平均", "網格", "費率", "跟蹤誤差", "心理紀律"], "LONG_HORIZON_QUANT_EDU", ["WEEKLY_SUNDAY"], "UNTIL_MODEL_OR_DATA_VERSION_CHANGES", ["財商拆彈組", "板塊輪動儀"], "用长周期可复现回测做策略教育，不把当日热点或短期收益外推成保证。", "LOW", "LOW", ["LONG_HISTORY", "ETF_REFERENCE_DATA", "BACKTEST_ENGINE"], ["10-30年历史、ETF费率/跟踪误差与回测引擎未接入"], "LOW", ["收益保證", "短期择时承诺"]),
]


MATRIX_RAW = {
    "個股顯微鏡": ("台股基本面", "台股", "基本面/白話分析", "每週 1-2 集", "5-8 分鐘"),
    "收盤夜話": ("台股盤勢", "台股", "盤後聊天/輕鬆", "每交易日", "15 分鐘"),
    "產業透視鏡": ("台股產業", "台股", "產業深度/供應鏈", "每週 1 集", "5-10 分鐘"),
    "權值旗艦": ("台股大盤", "台股", "權值股/技術面", "每週 2-3 集", "5-8 分鐘"),
    "資金雷達": ("台股輪動", "台股", "資金流向/短線", "每交易日", "3-5 分鐘"),
    "那指火箭": ("美股科技", "美股", "科技股/成長", "每週 2-3 集", "5-8 分鐘"),
    "板塊輪動儀": ("美股板塊", "美股", "ETF/資產配置", "每週 1 集", "5-8 分鐘"),
    "暗池雷達": ("美股暗池", "美股", "籌碼/期權", "每交易日開盤前", "3-5 分鐘"),
    "期權守門人": ("美股期權", "美股", "風險管理/賣方", "每交易日開盤前", "3 分鐘"),
    "財報獵人": ("美股財報", "美股", "基本面/SEC 原檔", "財報季每日/非財報季每週 2 集", "3 分鐘"),
    "宏觀天秤": ("全球宏觀", "全球", "宏觀/央行/利率", "每週日晚間", "5 分鐘"),
    "全球資金地圖": ("全球資金", "全球", "資金流向/跨市場", "每週 1-2 集", "5-8 分鐘"),
    "地緣炸藥庫": ("地緣大宗", "全球", "事件驅動/避險", "事件觸發＋週日回顧", "3-8 分鐘"),
    "週期航海家": ("週期商品", "全球", "大宗商品/週期", "每週二、週五", "2-5 分鐘"),
    "鏈上顯微鏡": ("鏈上數據", "加密貨幣", "鏈上/籌碼", "每交易日", "3-5 分鐘"),
    "中概風向球": ("中概股", "美股中概", "地緣/流動性", "每交易日", "3-4 分鐘"),
    "財商拆彈組": ("理財教育", "通用", "小白科普/避坑", "每日 18:00", "3 分鐘"),
    "半導體駭客": ("半導體", "台股＋美股", "硬核產業/技術", "每週三、週五", "3-5 分鐘"),
    "華爾街溫度計": ("美股資金", "美股", "資金面/情緒指標", "每週 2-3 集", "3-5 分鐘"),
    "定投實驗室": ("定投策略", "通用", "量化回測/長期", "每週日上午", "5-8 分鐘"),
}


BRAND_RAW = {
    "個股顯微鏡": ("顯微鏡系列", "台股單一公司的財務體質"),
    "鏈上顯微鏡": ("顯微鏡系列", "加密貨幣的鏈上籌碼流向"),
    "資金雷達": ("雷達系列", "台股產業間的資金搬家方向"),
    "暗池雷達": ("雷達系列", "美股暗池與期權的聰明錢動向"),
    "權值旗艦": ("權衡系列", "權值股對大盤的領跌領漲效應"),
    "宏觀天秤": ("權衡系列", "全球資產的相對價值與週期位置"),
    "期權守門人": ("守護系列", "現貨持倉的下行風險與現金流"),
    "財商拆彈組": ("守護系列", "小白投資人的血汗錢不被割韭菜"),
    "那指火箭": ("獨立品牌", "科技股衝上雲端的動能感"),
    "板塊輪動儀": ("獨立品牌", "美股產業板塊的結構性輪動"),
    "財報獵人": ("獨立品牌", "獵人般精準捕獲財報真相"),
    "全球資金地圖": ("獨立品牌", "跨市場資金移動的全景地圖"),
    "地緣炸藥庫": ("獨立品牌", "地緣事件一觸即發的緊張感"),
    "週期航海家": ("獨立品牌", "大宗商品週期的風浪航行"),
    "中概風向球": ("獨立品牌", "中概股與美元流動性的即時變化"),
    "半導體駭客": ("獨立品牌", "硬核技術視角透視半導體供應鏈"),
    "華爾街溫度計": ("獨立品牌", "市場貪婪與恐慌的真實溫度"),
    "定投實驗室": ("獨立品牌", "科學實驗精神驗證定投策略"),
    "收盤夜話": ("獨立品牌", "下班後朋友聊盤的輕鬆氛圍"),
    "產業透視鏡": ("獨立品牌", "穿透產業表面看底層邏輯"),
}


PILOTS = [
    {
        "channel_name": "資金雷達",
        "channel_id": "ch-05-tw-capital-radar",
        "pilot_type": "SIGNAL_HEAVY",
        "status": "RECOMMENDED_PENDING_APPROVAL",
        "why": [
            "现有 TWSE/TPEx EOD 和 Anomaly Engine 最接近其每日扫描节奏。",
            "可直接验证 Market Signal 是否能变成有 Why Now/Why Channel 的 Topic。",
            "能够暴露成交异动与真正资金流数据之间的边界。",
        ],
        "objections": [
            "现有 EOD 量价异常不是法人、ETF 或产业指数的净资金流。",
            "Industry Mapping 仅有未提交实现，数据库与 Topic 流程尚未接入。",
        ],
        "p06b_prerequisites": [
            "业务确认首版允许使用‘量价/成交异动’而不是声称‘资金净流入’。",
            "行业映射在独立审阅后才可成为试点输入。",
        ],
        "alternative": "收盤夜話；若业务更重视大盘盘后摘要，可替换，但三大法人/融资券仍是缺口。",
    },
    {
        "channel_name": "個股顯微鏡",
        "channel_id": "ch-01-tw-stock-microscope",
        "pilot_type": "EVENT_HEAVY",
        "status": "RECOMMENDED_PENDING_APPROVAL",
        "why": [
            "现有有限 MOPS 重大讯息可以与 EOD 异动组成公司事件包。",
            "可验证官方披露 Event 与市场变化在不臆测因果时如何形成选题。",
            "与资金雷达的快速扫描、产业透视镜的多公司视角差异明确。",
        ],
        "objections": [
            "频道核心还包括月营收、财报、法说与 Guidance，当前均未完整接入。",
            "频道原定每周1-2集，与每日5个候选的默认目标是否一致尚未确认。",
        ],
        "p06b_prerequisites": [
            "确认试点可以先以 MOPS 重大讯息 + EOD 为窄范围。",
            "允许合格候选不足5条时显示 HONEST_SHORTAGE。",
        ],
        "alternative": "財報獵人；但 SEC、财报日历和美股 EOD 均未接入，现阶段缺口更大。",
    },
    {
        "channel_name": "產業透視鏡",
        "channel_id": "ch-03-tw-industry-lens",
        "pilot_type": "CROSS_ENTITY",
        "status": "RECOMMENDED_PENDING_APPROVAL",
        "why": [
            "可验证同一 Event/Signal 如何分配到多公司产业频道，而不是复制单股标题。",
            "能检验 SAME_EVENT、RELATED_BUT_DISTINCT 与仅共现不等于因果的边界。",
            "以台股为主，避免第一轮被美股数据与来源授权完全阻断。",
        ],
        "objections": [
            "官方行业码不等于供应链关系；BB值、库存、产能利用率等尚未接入。",
            "Industry Mapping 未提交且未进入当前数据库/Topic 流程。",
        ],
        "p06b_prerequisites": [
            "首版只将官方行业分组用于候选召回，不宣称上下游传导已确认。",
            "所有产业催化剂必须有独立 Evidence，否则标为 UNKNOWN。",
        ],
        "alternative": "半導體駭客；其跨台美特征更强，但美股 EOD 和技术/供应链来源尚未接入。",
    },
]


OPEN_QUESTIONS = [
    ("Q01", "CADENCE", "全部20频道", "‘每日5个候选’是每个频道每个业务日都生成，还是只在该频道计划发布/事件触发日生成？", "原始频道频率从每日到每周、事件触发不等；答案会改变 DailyBrief 触发、短缺判断和试点验收。", "A=每日都生成；B=仅计划生产日；C=每日监控但只在生产日要求5条", "NEEDS_CONFIRMATION"),
    ("Q02", "TAXONOMY", "半導體駭客;華爾街溫度計", "这两个频道应继续归在‘理财教育/定投策略’，还是按矩阵分别归为‘半导体’和‘美股资金’？", "目录六类计数为18、正文/矩阵为20；归类会影响导航、依赖与撞题规则。", "A=按矩阵单列；B=保留理财教育；C=建立跨分类主/次分类", "CONFLICT"),
    ("Q03", "PILOT_SCOPE", "資金雷達", "首版是否允许把官方 EOD 量价异常称为‘资金关注/成交异动’，并明确不等同于法人或 ETF 净流入？", "若必须是真实资金净流入，现有数据不足，SIGNAL_HEAVY 试点需改选或先补数据。", "A=允许窄定义；B=必须真实资金流；C=改选收盘夜话", "NEEDS_CONFIRMATION"),
    ("Q04", "PILOT_SCOPE", "個股顯微鏡", "EVENT_HEAVY 试点是否接受先只用 MOPS 重大讯息 + EOD，还是必须先补月营收/财报/法说？", "决定该频道能否立即进入 P06B，以及候选不足是否属于预期。", "A=先做窄试点；B=先补月营收；C=先补完整公司数据", "NEEDS_CONFIRMATION"),
    ("Q05", "MAPPING", "產業透視鏡;資金雷達", "是否批准在独立审阅后，把当前未提交的官方行业码映射作为 P06B 的候选召回输入？", "不批准则两个试点都不能稳定按行业分组；批准也不代表供应链关系已确认。", "A=审阅后使用；B=暂不使用；C=先提供业务自有行业/供应链表", "NEEDS_CONFIRMATION"),
    ("Q06", "EDITORIAL_BOUNDARY", "全部20频道", "请补充每个频道明确不能讲的题、标题红线和风险容忍度；是否统一禁止个股买卖导向？", "多数频道只给了‘常讲什么’，缺少负例和排除边界，硬门槛无法定稿。", "A=统一红线+频道补充；B=逐频道提供；C=先只为3个试点提供", "UNKNOWN"),
    ("Q07", "GOLD_SET", "三个试点", "能否为每个试点提供至少3条过去‘值得讲’和3条‘不值得讲’的真实选题？", "没有业务 Gold set，只能审结构，无法校准 Channel Fit、Precision@5 与漏题。", "A=提供历史样例；B=用未来5日人工记录建立；C=两者都做", "UNKNOWN"),
]


def extract_channels(source_text: str) -> list[dict]:
    normalized = source_text.replace("\r\n", "\n")
    main = normalized.split("\n七、跨分類頻道矩陣總表", 1)[0]
    matches = []
    cursor = 0
    for row in CHANNELS:
        match = re.search(rf"(?m)^{re.escape(row['name'])}\s*$", main[cursor:])
        if not match:
            raise RuntimeError(f"Cannot find channel heading: {row['name']}")
        start = cursor + match.start()
        end = cursor + match.end()
        matches.append((start, end))
        cursor = end

    extracted = []
    markers = [
        "每集內容形式：",
        "核心拆解板塊：",
        "航海圖譜包含：",
        "每日深度觀察：",
        "風向球核心觀測：",
        "拆彈小分隊每日拆解：",
        "產業拆解維度：",
        "實驗室數據報告：",
    ]
    for index, row in enumerate(CHANNELS):
        body_start = matches[index][1]
        body_end = matches[index + 1][0] if index + 1 < len(matches) else len(main)
        body = main[body_start:body_end].strip()
        marker_hits = [(body.find(marker), marker) for marker in markers if marker in body]
        content_pos, content_marker = min(marker_hits) if marker_hits else (body.find("適合對象："), "")
        summary_raw = body[:content_pos].strip() if content_pos >= 0 else body
        audience_match = re.search(r"(?m)^適合對象：\s*(.+)$", body)
        frequency_match = re.search(r"(?m)^更新頻率：\s*(.+)$", body)
        tags_match = re.search(r"(?m)^關鍵標籤：\s*(.+)$", body)
        seo_match = re.search(r"SEO 關鍵詞：\s*(.*)$", body, re.S)
        content_raw = ""
        if content_marker:
            content_raw = body[body.find(content_marker) + len(content_marker):]
            content_raw = content_raw.split("適合對象：", 1)[0].strip()
        formats = []
        for line in content_raw.splitlines():
            cleaned = line.strip()
            if not cleaned:
                continue
            label = re.split(r"（| - ", cleaned, maxsplit=1)[0].strip()
            if label and label not in formats:
                formats.append(label)
        seo_raw = seo_match.group(1).strip() if seo_match else ""
        extracted.append(
            {
                "source_index": index + 1,
                "raw_channel_block": f"{row['name']}\n{body}",
                "channel_summary_raw": summary_raw,
                "content_blocks_raw": content_raw,
                "preferred_formats_raw": formats,
                "target_audience_raw": audience_match.group(1).strip() if audience_match else "UNKNOWN",
                "update_frequency_raw": frequency_match.group(1).strip() if frequency_match else "UNKNOWN",
                "tags_raw": tags_match.group(1).strip() if tags_match else "UNKNOWN",
                "seo_keywords_raw": seo_raw or "UNKNOWN",
            }
        )
    return extracted


def proposed_source_classes(row: dict) -> list[str]:
    classes = []
    deps = set(row["dependencies"])
    if "TWSE_TPEX_EOD" in deps or "ANOMALY_ENGINE" in deps:
        classes.append("OFFICIAL_MARKET")
    if "MOPS" in deps or "MONTHLY_REVENUE_FINANCIALS_CALLS" in deps:
        classes.extend(["OFFICIAL_DISCLOSURE", "COMPANY_IR"])
    if row["primary_market"] in {"US", "GLOBAL", "US_CHINA_ADR", "TW_US", "CRYPTO"}:
        classes.append("LICENSED_OR_AUTHORIZED_DATA")
    if "AUTHORIZED_INTERNATIONAL_NEWS" in deps or "AUTHORIZED_NEWS" in deps:
        classes.append("LICENSED_MEDIA")
    if row["matrix_category"] == "理財教育":
        classes.append("OFFICIAL_REGULATOR")
    return list(dict.fromkeys(classes)) or ["NEEDS_CONFIRMATION"]


def make_profile(row: dict, raw: dict, index: int) -> dict:
    channel_id = f"ch-{index:02d}-{row['slug']}"
    conflicts = []
    if row["category_conflict"]:
        conflicts.append(
            f"目录/正文归类为‘{row['directory_category']}’，跨分类矩阵归类为‘{row['matrix_category']}’。"
        )
    if row["name"] == "鏈上顯微鏡":
        conflicts.append("加密市场为24/7，但资料使用‘每交易日收盘后’，业务截止时点不明确。")

    missing = [
        "channel_owner",
        "channel_priority",
        "positive_examples",
        "negative_examples",
        "recent_30d_adopted_topics",
        "do_not_repeat_patterns",
        "approved_excluded_topics",
        "approved_evidence_policy",
        "approved_risk_tolerance",
    ]
    if not row["excluded"]:
        missing.append("excluded_topics")

    proposed_fields = [
        "channel_id",
        "allowed_source_classes",
        "minimum_evidence_policy",
        "opinion_usage_policy",
        "maximum_data_age",
        "title_intensity",
        "risk_tolerance",
        "daily_primary_target",
        "daily_backup_target_range",
        "shortage_policy",
        "recent_duplicate_window_days",
    ]
    matrix_category, matrix_market, matrix_theme, matrix_frequency, matrix_duration = MATRIX_RAW[row["name"]]
    brand_family, brand_meaning = BRAND_RAW[row["name"]]
    profile = {
        "channel_id": channel_id,
        "channel_name": row["name"],
        "source_index": index,
        "source_fields_raw": {
            **raw,
            "directory_category_raw": row["directory_category"],
            "matrix_category_raw": matrix_category,
            "matrix_market_raw": matrix_market,
            "matrix_theme_raw": matrix_theme,
            "matrix_update_frequency_raw": matrix_frequency,
            "matrix_duration_raw": matrix_duration,
            "matrix_row_raw": f"{matrix_category} | {row['name']} | {matrix_market} | {matrix_theme} | {matrix_frequency} | {matrix_duration}",
            "brand_family_raw": brand_family,
            "brand_meaning_raw": brand_meaning,
            "global_risk_template_raw": GLOBAL_RISK,
        },
        "profile_version": "0.1-draft",
        "profile_status": "DRAFT_WITH_CONFLICT" if conflicts else "DRAFT_NEEDS_HUMAN_CONFIRMATION",
        "source_category_directory": row["directory_category"],
        "source_category_matrix": row["matrix_category"],
        "channel_summary": raw["channel_summary_raw"],
        "target_audience": raw["target_audience_raw"],
        "primary_market": row["primary_market"],
        "secondary_markets": row["secondary_markets"],
        "security_scope": row["security_scope"],
        "preferred_sectors": row["sectors"],
        "preferred_entities": row["entities"],
        "preferred_topic_types": row["topic_types"],
        "excluded_topics": row["excluded"] or [],
        "prohibited_claims": ["具体买卖建议", "收益保证", "将 UNKNOWN 或 OPINION 写成 FACT"],
        "allowed_source_classes": proposed_source_classes(row),
        "minimum_evidence_policy": "FACTS_TRACEABLE; CAUSAL_CLAIMS_REQUIRE_QUALIFIED_EVIDENCE",
        "opinion_usage_policy": "OPINION_AS_LEAD_ONLY; NEVER_UPGRADE_TO_FACT",
        "maximum_data_age": row["max_age"],
        "market_session_preferences": row["session"],
        "preferred_formats": raw["preferred_formats_raw"],
        "content_depth": row["depth"],
        "title_intensity": "MODERATE; NO_CERTAINTY_OR_BUY_SELL_LANGUAGE",
        "risk_tolerance": "NEEDS_CONFIRMATION",
        "required_disclosures": ["统一风险提示模板", "数据时点/市场时段", "UNKNOWN/OPINION/SOURCE_CONFLICT"],
        "daily_primary_target": 5,
        "daily_backup_target_range": [0, 3],
        "shortage_policy": "HONEST_SHORTAGE",
        "recent_duplicate_window_days": 30,
        "positive_examples": [],
        "negative_examples": [],
        "missing_fields": missing,
        "conflicts": conflicts,
        "proposed_fields": proposed_fields,
    }
    profile["field_provenance"] = {
        "channel_id": "PROPOSED",
        "channel_name": "SUPPLIED",
        "source_index": "DERIVED_FROM_SUPPLIED",
        "source_fields_raw": "SUPPLIED",
        "profile_version": "PROPOSED",
        "profile_status": "DERIVED_FROM_SUPPLIED",
        "source_category_directory": "SUPPLIED",
        "source_category_matrix": "CONFLICT" if conflicts and row["category_conflict"] else "SUPPLIED",
        "channel_summary": "SUPPLIED",
        "target_audience": "SUPPLIED",
        "primary_market": "SUPPLIED",
        "secondary_markets": "DERIVED_FROM_SUPPLIED",
        "security_scope": "DERIVED_FROM_SUPPLIED",
        "preferred_sectors": "DERIVED_FROM_SUPPLIED",
        "preferred_entities": "DERIVED_FROM_SUPPLIED",
        "preferred_topic_types": "DERIVED_FROM_SUPPLIED",
        "excluded_topics": "DERIVED_FROM_SUPPLIED" if row["excluded"] else "UNKNOWN",
        "prohibited_claims": "DERIVED_FROM_SUPPLIED",
        "allowed_source_classes": "PROPOSED",
        "minimum_evidence_policy": "PROPOSED",
        "opinion_usage_policy": "PROPOSED",
        "maximum_data_age": "PROPOSED",
        "market_session_preferences": "DERIVED_FROM_SUPPLIED",
        "preferred_formats": "SUPPLIED",
        "content_depth": "DERIVED_FROM_SUPPLIED",
        "title_intensity": "PROPOSED",
        "risk_tolerance": "UNKNOWN",
        "required_disclosures": "DERIVED_FROM_SUPPLIED",
        "daily_primary_target": "PROPOSED",
        "daily_backup_target_range": "PROPOSED",
        "shortage_policy": "PROPOSED",
        "recent_duplicate_window_days": "PROPOSED",
        "positive_examples": "UNKNOWN",
        "negative_examples": "UNKNOWN",
        "missing_fields": "DERIVED_FROM_SUPPLIED",
        "conflicts": "CONFLICT" if conflicts else "DERIVED_FROM_SUPPLIED",
        "proposed_fields": "PROPOSED",
        "field_provenance": "PROPOSED",
    }
    assert set(profile["field_provenance"].values()) <= PROVENANCE
    return profile


def write_json(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def topic_example(
    channel_id: str,
    title: str,
    readiness: str,
    what_happened: str,
    what_changed: str,
    why_now: str,
    why_channel: str,
    verified: list[str],
    derived: list[str],
    unknowns: list[str],
    angles: list[str],
    titles: list[str],
    risks: list[str],
    multi_entity: bool = False,
) -> dict:
    return {
        "data_label": "SCHEMA_EXAMPLE_NOT_REAL_TOPIC",
        "channel_id": channel_id,
        "topic_title": title,
        "readiness": readiness,
        "what_happened": what_happened,
        "what_changed": what_changed,
        "why_now": why_now,
        "why_channel": why_channel,
        "related_market_qualified_security_ids": [
            "<TWSE_OR_TPEX:SECURITY_ID_A>",
            "<TWSE_OR_TPEX:SECURITY_ID_B>",
        ] if multi_entity else ["<TWSE_OR_TPEX:SECURITY_ID>"],
        "market_session_date": "<YYYY-MM-DD>",
        "session_state": "EOD_COMPLETE",
        "data_as_of": "<ISO-8601_TIMESTAMP>",
        "verified_facts": [
            {"claim": fact, "source_class": "OFFICIAL_MARKET_OR_DISCLOSURE", "epistemic_state": "FACT"}
            for fact in verified
        ],
        "derived_findings": [
            {"claim": finding, "source_class": "OFFICIAL_INPUT", "epistemic_state": "DERIVED"}
            for finding in derived
        ],
        "opinions": [],
        "unknowns": unknowns,
        "source_conflicts": [],
        "evidence_ids": ["<RAW_EVIDENCE_ID>"],
        "independent_publisher_groups": ["<OFFICIAL_PUBLISHER_GROUP>"],
        "suggested_angles": angles,
        "working_titles": titles,
        "risk_flags": risks,
    }


def build_examples() -> dict:
    radar = "ch-05-tw-capital-radar"
    stock = "ch-01-tw-stock-microscope"
    industry = "ch-03-tw-industry-lens"
    examples = {
        radar: [
            topic_example(radar, "[结构示例] 某产业多股同步放量，催化剂仍待核验", "NEEDS_RESEARCH", "同一官方行业组内多只证券出现量能异常。", "相对各自 prior-20 基线明显变化。", "完整 EOD 已提交，变化可回放。", "适合每日轮动扫描，但不能把共现写成净资金流。", ["EOD 成交量与收盘价已完成"], ["多证券同时命中异常规则"], ["共同催化剂未知", "法人净流入未知"], ["量价共现与真实资金流的区别", "行业内领涨/跟随结构"], ["某产业为何同时放量？先确认共现，再找原因", "不是净流入：这组量价异动真正说明什么"], ["CATALYST_UNKNOWN", "NOT_FUND_FLOW"], True),
            topic_example(radar, "[结构示例] 低基期个股量比突出，但绝对流动性偏低", "WATCH_ONLY", "某证券命中相对量能异常。", "相对自身历史强，但同市场绝对成交量分位低。", "适合在收盘后作为风险案例。", "用于提醒轮动榜的低基期噪声。", ["当日与 prior-20 成交量可核验"], ["RVOL 高且流动性等级低"], ["是否有事件驱动未知"], ["解释高 RVOL 不等于高可交易性", "低流动性异动的筛选边界"], ["量比很高，为什么仍不该直接追？", "低基期放量：热点还是噪声"], ["LOW_LIQUIDITY", "NO_INVESTMENT_ADVICE"]),
            topic_example(radar, "[结构示例] 强势行业出现领涨扩散", "READY_TO_PITCH", "行业组从少数领涨扩展为多证券同步变化。", "命中证券数量与规则广度较前一完整交易日增加。", "连续 Replay 可确认扩散，而非单日截图。", "对应产业轮动与领涨扩散，而不是公司深度分析。", ["两个完整 EOD 日的规则命中"], ["行业内异常广度增加"], ["资金来源与催化剂未必已确认"], ["从个股领涨到行业扩散", "连续两日与单日噪声的差异"], ["强势从一只扩到一组：轮动进入哪一步", "行业广度扩大，但原因仍需证据"], ["INDUSTRY_MAPPING_PENDING_REVIEW"], True),
            topic_example(radar, "[结构示例] 昨日热门行业今日量能降温", "READY_TO_PITCH", "上一日多股异常的行业组在本日明显减少。", "异常数量和相对量能同时回落。", "收盘后可判断轮动是否延续。", "符合资金雷达的撤退/降温观察，但不声称资金净流出。", ["连续两个 EOD 日可回放"], ["异常广度与 RVOL 中位数下降"], ["卖方主体未知"], ["热点退潮的可观察信号", "避免把成交降温写成机构撤资"], ["昨日还热，今日为何快速降温", "轮动退潮：成交异动告诉我们什么"], ["NOT_NET_OUTFLOW"]),
            topic_example(radar, "[结构示例] 量价突破与行业事件同日出现", "NEEDS_RESEARCH", "行业内证券命中价量突破，且事件池出现相关行业事件。", "市场 Signal 与 Event 时间接近。", "同一业务日具备进一步核验价值。", "可测试 Signal→Event→Topic，但只有 SAME_EVENT 或明确关联才可写因果。", ["EOD 价量规则命中", "事件发布时间可核验"], ["时间与行业相关性成立"], ["是否为同一因果事件未知"], ["先验证事件关系再写轮动原因", "同日出现不等于因果"], ["价量突破撞上产业事件：能否连成同一题", "同步发生，还是同一原因？"], ["CAUSALITY_UNVERIFIED"], True),
        ],
        stock: [
            topic_example(stock, "[结构示例] MOPS 重大讯息后出现量价变化", "READY_TO_PITCH", "公司发布可映射的重大讯息。", "公告后首个完整交易日的量价相对历史基线变化。", "公告与完整 EOD 已可核验。", "聚焦单一公司的经营事件与市场反应。", ["MOPS 公告主题/时间", "完整 EOD OHLCV"], ["公告后相对量能与价格变化"], ["市场变化是否由公告导致未知"], ["公告事实与市场反应分开讲", "投资人还需核对哪些细节"], ["公告说了什么，市场又怎么反应", "一家公司发生变化：事实、反应与未知"], ["CAUSALITY_UNVERIFIED"]),
            topic_example(stock, "[结构示例] 月营收同比转折", "NEEDS_RESEARCH", "公司发布新一期月营收。", "同比/环比方向与过去趋势出现转折。", "数据发布后进入频道候选。", "符合公司营运追踪，但当前仓库尚无月营收连接。", ["<公司月营收官方数据待接入>"], ["同比与环比变化待计算"], ["当前能力 NOT_IMPLEMENTED"], ["转折是否来自基期", "营收变化与订单能见度的证据边界"], ["月营收转折，先看基期还是需求", "数字变了，公司体质真的变了吗"], ["MISSING_CORPORATE_DATA"]),
            topic_example(stock, "[结构示例] 法说 Guidance 与此前口径变化", "NEEDS_RESEARCH", "公司在法说更新 Guidance。", "新口径相对前次指引发生变化。", "法说原档发布后才进入候选。", "频道强调法说和公司体质，必须直连原始资料。", ["<法说原档待接入>"], ["前后指引差异待结构化"], ["法说资料当前 NOT_IMPLEMENTED"], ["管理层改口的具体字段", "市场预期与公司指引分离"], ["管理层改了哪一句，影响有多大", "法说不是新闻摘要：真正变化在哪里"], ["MISSING_COMPANY_IR"]),
            topic_example(stock, "[结构示例] 毛利率改善但现金流未同步", "NEEDS_RESEARCH", "最新财报显示利润率与现金流方向分化。", "毛利率上升但自由现金流未同步。", "财报发布形成可解释反差。", "适合体质分析，不能只看单一利润指标。", ["<官方财报原档待接入>"], ["利润率与现金流方向分化"], ["完整财报能力 NOT_IMPLEMENTED"], ["利润质量", "营运资本变化"], ["毛利率变好，现金为何没跟上", "财报里的两种答案：利润与现金"], ["MISSING_FINANCIAL_STATEMENTS"]),
            topic_example(stock, "[结构示例] 异常放量但没有公司事件", "WATCH_ONLY", "单一公司出现 EOD 异常。", "量能相对 prior-20 明显，但未找到合格公司事件。", "可作为继续观察，而非硬凑基本面故事。", "本频道需要公司营运证据，只有盘面 Signal 不够。", ["EOD 量价异常"], ["相对历史变化"], ["公司催化剂未知"], ["为什么暂不进入主选题", "需补哪些公司证据"], ["放量了，但公司发生了什么仍不知道", "没有催化剂时，显微镜该停在哪里"], ["CATALYST_UNKNOWN", "WATCH_ONLY"]),
        ],
        industry: [
            topic_example(industry, "[结构示例] 同一官方行业多股共振，原因未确认", "NEEDS_RESEARCH", "行业组内多证券同时命中异常规则。", "异常广度相对前一完整交易日增加。", "EOD Replay 可复核共现。", "适合产业视角，但共现只能召回研究，不可直接生成供应链因果。", ["多证券 EOD 规则命中"], ["官方行业分组下出现共现"], ["共同催化剂未知", "上下游关系未知"], ["行业共现与产业因果的边界", "从哪些 Evidence 开始补证"], ["同一行业一起动了，原因还不能下结论", "共振已确认，产业故事仍待核验"], ["INDUSTRY_MAPPING_PENDING_REVIEW", "CAUSALITY_UNKNOWN"], True),
            topic_example(industry, "[结构示例] 上下游营收趋势出现分化", "NEEDS_RESEARCH", "同一供应链上下游公司发布月度数据。", "上游与下游增长方向分化。", "同一发布窗口具备产业解释价值。", "频道需要跨公司比较，而不是两篇单股稿。", ["<多公司月营收待接入>"], ["上下游趋势分化待计算"], ["供应链映射与月营收未接入"], ["分化来自库存还是终端需求", "避免由相关性推断订单转移"], ["同一条链，为何上下游给出相反信号", "营收分化背后的库存问题"], ["MISSING_SUPPLY_CHAIN_DATA"], True),
            topic_example(industry, "[结构示例] 库存天数连续改善", "NEEDS_RESEARCH", "行业内多家公司库存指标连续变化。", "库存天数相对历史下降且覆盖多家公司。", "财报窗口后可做产业复盘。", "符合产业周期深度内容，而不是即时资金扫描。", ["<公司财报库存字段待接入>"], ["多公司库存趋势待计算"], ["财报与供应链数据未接入"], ["去库存是否结束", "不同环节的节奏差"], ["库存一起下降，产业周期到哪一步", "去库存结束了吗？先看链上不同环节"], ["MISSING_FINANCIAL_DATA"], True),
            topic_example(industry, "[结构示例] 产业事件只影响部分环节", "NEEDS_RESEARCH", "事件池出现行业事件，相关公司反应分化。", "同一行业中仅特定环节出现量价异常。", "事件与 EOD 已位于同一可核验窗口。", "可解释产业链受益/受损分化，但关系需 Evidence。", ["事件发布时间", "各证券完整 EOD"], ["行业内反应分化"], ["哪些公司属于直接/间接关系未知"], ["事件传导路径", "直接、供应链、板块和可能关系分层"], ["同一产业，为什么只有一段供应链在动", "事件来了，受影响的并不是所有公司"], ["RELATION_TYPE_UNVERIFIED"], True),
            topic_example(industry, "[结构示例] 台美半导体事件映射到台股供应链", "WATCH_ONLY", "美国公司事件可能关联台湾供应链。", "事件发生在美国时段，台股尚未形成完整下一交易日数据。", "亚洲早间只能标记隔夜线索。", "符合产业透视，但首版缺美股 EOD 与已验证供应链映射。", ["<公司事件 Evidence 待授权/接入>"], ["可能的跨市场关系仅为候选"], ["美股 EOD 未接入", "供应链关系未确认"], ["隔夜事件如何进入台股盘前观察", "何时从 WATCH_ONLY 升级"], ["隔夜半导体事件，台股供应链先观察什么", "跨市场映射：线索不是结论"], ["US_EOD_NOT_IMPLEMENTED", "SUPPLY_CHAIN_UNKNOWN"], True),
        ],
    }
    return {
        "artifact_status": "SCHEMA_ACCEPTANCE_EXAMPLES_ONLY",
        "warning": "全部15条均为结构样例，不是2026-08-18真实热点，不得对外当作事实或投资建议。",
        "pilots": [
            {
                "channel_id": pilot["channel_id"],
                "channel_name": pilot["channel_name"],
                "pilot_type": pilot["pilot_type"],
                "examples": examples[pilot["channel_id"]],
            }
            for pilot in PILOTS
        ],
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    source_bytes = SOURCE.read_bytes()
    source_text = source_bytes.decode("utf-8")
    raw_channels = extract_channels(source_text)
    profiles = [
        make_profile(row, raw, index)
        for index, (row, raw) in enumerate(zip(CHANNELS, raw_channels, strict=True), start=1)
    ]
    profile_ids = [profile["channel_id"] for profile in profiles]
    assert len(profiles) == len(set(profile_ids)) == 20

    profile_document = {
        "artifact": "BEN Radar ChannelProfile v0.1 DRAFT",
        "artifact_status": "DRAFT_NEEDS_HUMAN_CONFIRMATION",
        "generated_from_sha256": hashlib.sha256(source_bytes).hexdigest().upper(),
        "actual_channel_count": len(profiles),
        "profiles": profiles,
    }
    write_json(OUT / "channel_profiles_v0.1.json", profile_document)

    inventory = f"""# P06A 频道输入盘点

## 结论

- 输入文件：`{SOURCE}`
- SHA-256：`{hashlib.sha256(source_bytes).hexdigest().upper()}`
- 输入行数：{len(source_text.splitlines())}
- 实际识别频道：**20**
- 唯一频道名：**20**；重复：**0**；无法识别：**0**；缺失：**0**
- 输入状态：`COMPLETE_COUNT_WITH_TAXONOMY_CONFLICT`
- 原文最后更新：`2026-08-12`（来自附件正文，不代表本仓库数据时点）

## 文件范围

本次用户明确表示频道资料只有这一份附件。本审计没有把当前 Top20 股票、29 个 X 账号、23 条实时来源或既有 Style Pack 当作输出频道。

## 对账问题

1. 目录六大分类声称 `5 + 5 + 4 + 1 + 1 + 2 = 18` 个频道，但正文与跨分类矩阵实际各有20个唯一频道。
2. `半導體駭客` 与 `華爾街溫度計` 位于正文“理财教育/定投策略”段下，但跨分类矩阵分别归为“半导体”和“美股资金”；两条 Profile 标为 `CONFLICT`。
3. `鏈上顯微鏡` 使用“每交易日收盘后”，但加密市场24/7，业务截止时点为 `NEEDS_CONFIRMATION`。
4. 多数频道给了“常讲什么”，但没有明确负例、负责人、优先级、近30天采用历史和实际采用/拒绝样例。
5. 原文统一风险提示已逐条保存在 `source_fields_raw.global_risk_template_raw`；不得把它替代成投资建议。

## 解析与保真

- 每个 Profile 保存完整 `raw_channel_block`、原始简介、内容板块、受众、更新频率、标签、SEO、跨分类矩阵原始行与品牌家族字段。
- 生成字段使用 `SUPPLIED / DERIVED_FROM_SUPPLIED / PROPOSED / UNKNOWN / CONFLICT` 标注 provenance。
- 未提供的正/负样例保持空数组并列入 `missing_fields`。
"""
    (OUT / "source_inventory.md").write_text(inventory, encoding="utf-8")

    review_lines = [
        "# ChannelProfile v0.1 DRAFT 业务审阅版",
        "",
        "> 本文件是20频道草案，不是批准后的生产配置。`PROPOSED` 需要人工确认，`UNKNOWN` 不得自动补齐。",
        "",
    ]
    for profile, row in zip(profiles, CHANNELS, strict=True):
        review_lines.extend(
            [
                f"## {profile['source_index']:02d}. {profile['channel_name']}",
                "",
                f"- ID：`{profile['channel_id']}`；状态：`{profile['profile_status']}`",
                f"- 原始分类：`{profile['source_category_directory']}`；矩阵分类：`{profile['source_category_matrix']}`",
                f"- 原始矩阵行：{profile['source_fields_raw']['matrix_row_raw']}",
                f"- 品牌家族：{profile['source_fields_raw']['brand_family_raw']} / {profile['source_fields_raw']['brand_meaning_raw']}",
                f"- 市场/范围：`{profile['primary_market']}` / {', '.join(profile['security_scope'])}",
                f"- 原始受众：{profile['target_audience']}",
                f"- 原始频率：{profile['source_fields_raw']['update_frequency_raw']}",
                f"- 原始标签：{profile['source_fields_raw']['tags_raw']}",
                f"- 归纳 Topic：{'; '.join(profile['preferred_topic_types'])}",
                f"- Why Channel：{row['distinction']}",
                f"- 当前依赖：{'; '.join(row['dependencies'])}",
                f"- 主要缺口：{'; '.join(row['gaps'])}",
                f"- 提议 Evidence 政策：`{profile['minimum_evidence_policy']}`",
                f"- 提议配额：主候选5、备选0-3；不足使用 `{profile['shortage_policy']}`",
                f"- 缺失字段：{'; '.join(profile['missing_fields'])}",
                f"- 冲突：{'; '.join(profile['conflicts']) if profile['conflicts'] else '无已识别内部冲突'}",
                "",
            ]
        )
    (OUT / "channel_profiles_human_review.md").write_text("\n".join(review_lines), encoding="utf-8")

    overlap_rows = []
    for profile, row in zip(profiles, CHANNELS, strict=True):
        overlap_rows.append(
            {
                "channel_id": profile["channel_id"],
                "channel_name": profile["channel_name"],
                "primary_market": profile["primary_market"],
                "closest_overlap_channels": ";".join(row["closest"]),
                "market_overlap": "HIGH" if any(name in {"個股顯微鏡", "收盤夜話", "產業透視鏡", "權值旗艦", "資金雷達"} for name in [row["name"], *row["closest"]]) and row["primary_market"] == "TW" else "MIXED",
                "entity_sector_overlap": ";".join(row["sectors"] or row["entities"]) or "BROAD_OR_UNKNOWN",
                "topic_overlap": ";".join(row["topic_types"]),
                "evidence_requirement_difference": ";".join(row["dependencies"]),
                "content_depth_format_difference": row["depth"],
                "same_event_probability": row["same_event_probability"],
                "collision_risk": row["collision_risk"],
                "why_channel_distinction": row["distinction"],
                "provenance": "DERIVED_FROM_SUPPLIED",
            }
        )
    write_csv(OUT / "channel_overlap_matrix.csv", list(overlap_rows[0]), overlap_rows)

    coverage_evidence = (
        "migrations/013_official_data_connect.sql; src/global_x_finance/official_data.py; "
        "src/global_x_finance/anomaly_engine.py; data/taiwan-demo.db read-only audit 2026-08-18; "
        "migrations/015_industry_mapping.sql (uncommitted/not applied); src/global_x_finance/x_intelligence.py"
    )
    coverage_rows = []
    for profile, row in zip(profiles, CHANNELS, strict=True):
        coverage_rows.append(
            {
                "channel_id": profile["channel_id"],
                "channel_name": profile["channel_name"],
                "twse_tpex_eod_status": "AVAILABLE_VERIFIED",
                "historical_baseline_anomaly_status": "AVAILABLE_VERIFIED",
                "industry_mapping_status": "PARTIAL",
                "mops_material_disclosure_status": "PARTIAL",
                "monthly_revenue_financials_calls_guidance_status": "NOT_IMPLEMENTED",
                "taiwan_news_status": "BLOCKED_RIGHTS",
                "international_news_status": "BLOCKED_RIGHTS",
                "x_status": "AVAILABLE_BUT_PROTOTYPE",
                "us_eod_status": "NOT_IMPLEMENTED",
                "earnings_macro_calendar_status": "NOT_IMPLEMENTED",
                "channel_30d_adoption_history_status": "NOT_IMPLEMENTED",
                "feedback_1h_6h_24h_status": "NOT_IMPLEMENTED",
                "core_dependencies": ";".join(row["dependencies"]),
                "critical_gaps": ";".join(row["gaps"]),
                "pilot_feasibility": row["feasibility"],
                "evidence_basis": coverage_evidence,
            }
        )
    assert all(
        value in CAPABILITY_STATES
        for coverage in coverage_rows
        for key, value in coverage.items()
        if key.endswith("_status")
    )
    write_csv(OUT / "channel_data_coverage_matrix.csv", list(coverage_rows[0]), coverage_rows)

    pilot_lines = [
        "# P06A 三频道试点建议",
        "",
        "> 所有选择均为 `RECOMMENDED_PENDING_APPROVAL`。本文件不代表 P06B 已批准或实现。",
        "",
        "## 推荐结论",
        "",
        "| 类型 | 频道 | 当前可复用 | 关键前提 |",
        "|---|---|---|---|",
        "| SIGNAL_HEAVY | 資金雷達 | 台股 EOD、历史基线、Anomaly Engine | 不把量价异动写成真实资金净流入 |",
        "| EVENT_HEAVY | 個股顯微鏡 | 有限 MOPS 重大讯息、台股 EOD | 首版接受窄事件范围与真实短缺 |",
        "| CROSS_ENTITY | 產業透視鏡 | 台股 EOD、事件关系框架 | Industry Mapping 审阅后使用，共现不写成因果 |",
        "",
    ]
    for pilot in PILOTS:
        pilot_lines.extend(
            [
                f"## {pilot['pilot_type']}：{pilot['channel_name']}",
                "",
                f"- 状态：`{pilot['status']}`",
                "- 推荐理由：" + "；".join(pilot["why"]),
                "- 反对理由：" + "；".join(pilot["objections"]),
                "- P06B 前置：" + "；".join(pilot["p06b_prerequisites"]),
                "- 替代项：" + pilot["alternative"],
                "",
            ]
        )
    pilot_lines.extend(
        [
            "## 为什么不是一个频道或直接20个",
            "",
            "一个频道无法验证同一共享事件如何产生不同 Why Channel；直接20个会把尚未确认的频率、禁区、数据权利和分类冲突固化成20套低质量规则。三个试点覆盖 Signal、公司 Event 和跨实体三种核心路径，同时把第一轮限制在台股，避免被尚未接入的美股/全球/链上数据完全阻断。",
            "",
            "## 五日 Replay 的边界",
            "",
            "P06A 只定义验收，不执行 Replay。P06B 获批后应使用最近五个完整台股交易日；所有候选必须显示时段、Evidence、未知与短缺，不得因目标5条而补造事件。",
        ]
    )
    (OUT / "pilot_recommendation.md").write_text("\n".join(pilot_lines), encoding="utf-8")

    examples = build_examples()
    assert sum(len(pilot["examples"]) for pilot in examples["pilots"]) == 15
    write_json(OUT / "pilot_topic_card_examples.json", examples)

    open_rows = [
        {
            "question_id": qid,
            "category": category,
            "affected_channels": affected,
            "question": question,
            "why_material": why,
            "decision_options": options,
            "current_state": state,
        }
        for qid, category, affected, question, why, options, state in OPEN_QUESTIONS
    ]
    write_csv(OUT / "open_questions.csv", list(open_rows[0]), open_rows)

    acceptance = """# P06A 验收报告

## 产物状态

- 频道输入：20个唯一频道，计数完整；分类存在2条 `CONFLICT`。
- ChannelProfile：20条 `0.1-draft`，均保留原始块与字段级 provenance。
- 重叠矩阵：20条频道行，包含重叠对象、差异、同 Event 概率、撞题风险与 Why Channel。
- 数据覆盖矩阵：20条频道行，使用限定状态枚举并附仓库证据。
- 试点：3个，均为 `RECOMMENDED_PENDING_APPROVAL`。
- Topic Card：15条，全部标记 `SCHEMA_EXAMPLE_NOT_REAL_TOPIC`。
- 开放问题：仅保留7个会改变规则或试点的问题。

## 范围核对

- 未修改应用代码、Flask、Schema、migration、数据库、来源配置、Anomaly Engine、排名或公共站点。
- 未把未提交 Industry Mapping 写成生产能力；状态为 `PARTIAL`。
- 未把美股 EOD、新闻授权、X 原型、财报/宏观日历或 LLM 写成已完成。
- 未接入或测试新的外部来源。

## 结构化校验

- 专用 P06A validator：`PASS`。核对20个 Profile/唯一 ID、20行重叠矩阵、20行数据覆盖矩阵、3种试点、15条 schema 标签和7个实质问题。
- 当前能力定向测试：`19 passed`，范围为 official data、Anomaly Engine、未提交 Industry Mapping 工作树与 Schema；这不代表 Industry Mapping 已生产集成。
- `git diff --check`：`PASS`；只报告工作树中的 LF→CRLF 警告，没有 whitespace error。
- `powershell -ExecutionPolicy Bypass -File scripts/project-memory-check.ps1`：`PASS`。

## 应用测试

本任务只新增研究/文档产物，按任务书不重跑完整应用套件。跳过原因：P06A 明确禁止应用实现，定向测试与结构校验足以验证本次能力矩阵和产物契约。
"""
    (OUT / "acceptance_report.md").write_text(acceptance, encoding="utf-8")

    report = """# BEN RADAR 20频道画像与三频道试点建议（P06A）

- 日期：2026-08-18
- 状态：`P06A_COMPLETE_PENDING_HUMAN_APPROVAL`
- 输入：用户提供的《20 頻道分類歸集總覽表（完整版）》
- 边界：本报告完成频道审计与试点建议；P06B 尚未实现

## 一、先说结论

本次实际识别 **20个唯一频道**，没有补造、重复或漏掉频道。频道内容足以建立第一版画像，但还不足以直接开发20频道：原文的分类目录只合计18个，`半導體駭客` 与 `華爾街溫度計` 在正文和矩阵中的归类冲突；绝大多数频道也没有负例、近30天采用历史、负责人和优先级。

第一轮建议只做三个差异频道，并全部等待人工批准：

1. **資金雷達 / SIGNAL_HEAVY**：验证台股 EOD 与异常 Signal 如何变成选题；必须明确“量价异动不等于资金净流入”。
2. **個股顯微鏡 / EVENT_HEAVY**：验证 MOPS 公司 Event + EOD 如何形成单公司选题；先接受月营收/财报/法说缺失和真实短缺。
3. **產業透視鏡 / CROSS_ENTITY**：验证多公司共现、事件关系与频道差异；Industry Mapping 审阅前不能当生产能力，共现不能写成供应链因果。

## 二、20频道按业务与数据成熟度分组

### 台股优先组（6）

`個股顯微鏡、收盤夜話、產業透視鏡、權值旗艦、資金雷達、半導體駭客（台股部分）`

这一组最接近当前能力，但只有 EOD/历史异常最成熟；公司基本面、行业/供应链、机构资金与半导体跨市场资料仍有缺口。

### 美股/中概组（7）

`那指火箭、板塊輪動儀、暗池雷達、期權守門人、財報獵人、中概風向球、華爾街溫度計`

美股 EOD、期权/暗池、ETF 流量、SEC/财报日历、13F 与 DXY/CNH 未接入，国际新闻权利也未确认。当前不适合做首批真实 Replay。

### 全球宏观与商品组（4）

`宏觀天秤、全球資金地圖、地緣炸藥庫、週期航海家`

需要宏观/央行日历、全球资产、商品、库存、运价及合格国际事件 Evidence；当前主要为 `NOT_IMPLEMENTED / BLOCKED_RIGHTS`。

### 链上组（1）

`鏈上顯微鏡` 需要链上、OI、清算和质押数据，当前未接入；24/7 市场的业务截止时点也未确认。

### 理财教育与长期策略组（2）

`財商拆彈組、定投實驗室` 分别缺监管/产品案例来源和10-30年历史/ETF参考数据/回测能力，不能用当天股票异常替代。

## 三、为什么先做这三个

三个试点共用 `Evidence → Signal → Event → Topic → Channel Assignment → Channel Daily Brief`，但分别检验不同环节。它们都以台股为主，能够利用当前真实 EOD；同时又不会把一个页面复制三份。

不先选美股、宏观、期权或链上频道，是因为数据未接入或权利未确认。不是这些频道不重要，而是当前做出来只能依赖结构示例或产生大量真实短缺。

不直接做20个，是因为每日5候选与各频道原定更新频率存在未决冲突：频道中既有每日，也有每周、财报季和事件触发。若不先确认，系统会把“每日监控”和“每日生产”混为一谈。

## 四、最大的三个缺口

1. **业务规则缺口**：每日5候选与实际发布频率的关系、分类冲突、负例/禁区、负责人和近30天采用历史未确认。
2. **台股公司与产业数据缺口**：MOPS 只有有限重大讯息；月营收、财报、法说、Guidance、机构资金、供应链指标未完成；Industry Mapping 仍为未提交且未接入的 `PARTIAL`。
3. **非台股数据与权利缺口**：美股 EOD、期权/暗池、宏观/财报日历、商品/链上数据未实现；台湾及国际新闻生产使用权未确认，X 仍是原型。

## 五、能力事实

- `AVAILABLE_VERIFIED`：TWSE/TPEx EOD 与历史基线；当前只读核对为97,603条、1,087个 TWSE 和889个 TPEx 证券，日期截至2026-08-17。
- `AVAILABLE_VERIFIED`：Anomaly Engine 的先前日期 Replay 与解释性规则；状态仍是 `READY_FOR_HUMAN_REVIEW`，不是业务选题规则已验证。
- `PARTIAL`：MOPS 重大讯息，当前只读核对11条且已映射；不等于月营收/财报/法说完整能力。
- `PARTIAL`：Industry Mapping 的未提交 migration/module/tests 当前存在，但数据库无相关表且未接 Topic 流程。
- `BLOCKED_RIGHTS / AVAILABLE_BUT_PROTOTYPE`：新闻和 X 只能按当前治理状态使用，不能写成生产授权。
- `NOT_IMPLEMENTED`：美股 EOD、财报/宏观日历、频道近30天采用历史、1H/6H/24H反馈。

## 六、P06B 前必须确认

1. 每日5候选是每天都生成，还是只在频道计划发布/事件触发日要求？
2. 是否批准三个试点；尤其是資金雷達能否采用“量价异动、非净资金流”的窄定义？
3. 個股顯微鏡能否先做 MOPS + EOD，还是必须先补月营收/财报/法说？
4. 產業透視鏡能否在独立审阅后使用官方行业码映射进行候选召回？
5. 半導體駭客与華爾街溫度計最终归类是什么？
6. 至少为三个试点补充正例、负例和明确禁区。

## 七、Topic Card 示例边界

本任务生成每个试点5条、共15条结构化样例。它们全部标记 `SCHEMA_EXAMPLE_NOT_REAL_TOPIC`，仅用于确认字段、准备度、Why Now、Why Channel、Evidence、市场时段和风险展示方式，不是今天真实热点。

## 八、建议下一步

业务负责人先确认试点名单与上面少量问题。确认后再写 P06B：仅实现三个频道、最近五个完整交易日 Replay、五个业务日人工试用和真实采用/拒绝记录；不要在 P06B 同时扩美股、20频道、内容生成或实时行情。

## 九、验证结果

- P06A 专用结构校验：通过（20 Profile、20+20矩阵行、3试点、15条 schema 示例、7个实质问题）。
- 当前能力定向测试：19项通过；Industry Mapping 仍仅代表未提交工作树可运行，不代表已接入生产。
- `git diff --check`：通过，仅有 LF→CRLF 提示。
- Project Memory check：通过。
- 完整应用测试：未运行；本任务仅改研究、报告和 Project Memory，且任务书禁止应用实现。

## 技术附录：产物

- `research/ben_radar_channel_intake/source_inventory.md`
- `research/ben_radar_channel_intake/channel_profiles_v0.1.json`
- `research/ben_radar_channel_intake/channel_profiles_human_review.md`
- `research/ben_radar_channel_intake/channel_overlap_matrix.csv`
- `research/ben_radar_channel_intake/channel_data_coverage_matrix.csv`
- `research/ben_radar_channel_intake/pilot_recommendation.md`
- `research/ben_radar_channel_intake/pilot_topic_card_examples.json`
- `research/ben_radar_channel_intake/open_questions.csv`
- `research/ben_radar_channel_intake/acceptance_report.md`
"""
    DELIVERABLE.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
