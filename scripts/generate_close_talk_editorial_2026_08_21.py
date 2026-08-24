from __future__ import annotations

import argparse
import json
import textwrap
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


OFFICIAL_HUMAN_URLS = {
    "TWSE_INDEX_AND_SECTORS": "https://www.twse.com.tw/zh/trading/historical/mi-index.html",
    "MARKET_BREADTH": "https://www.twse.com.tw/zh/trading/historical/mi-index.html",
    "TWSE_INSTITUTIONAL_FLOW": "https://www.twse.com.tw/zh/trading/foreign/bfi82u.html",
    "OFFICIAL_EOD": "https://www.twse.com.tw/zh/trading/historical/mi-index.html",
}


def load_pack(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def source_index(pack: dict[str, Any]) -> dict[str, dict[str, Any]]:
    rows: dict[str, dict[str, Any]] = {}
    for dataset in pack["cash_market_source_pack"]["datasets"]:
        if dataset["status"] == "READY":
            rows[f"OFFICIAL:{dataset['dataset_id']}:{pack['market_session_date']}"] = dataset
    for row in pack.get("market_activity_leaders", []):
        rows[row["evidence_id"]] = row
    for field in ("news_leads", "x_attention_leads", "official_disclosure_leads"):
        for row in pack.get(field, []):
            rows[row["evidence_id"]] = row
    return rows


def card(index: dict[str, dict[str, Any]], evidence_id: str, *, title: str | None = None,
         source_name: str | None = None, url: str | None = None,
         status: str | None = None) -> dict[str, Any]:
    row = index[evidence_id]
    if evidence_id.startswith("OFFICIAL:TWSE_INDEX_AND_SECTORS"):
        source = "臺灣證券交易所"
        link = row.get("source_url") or (
            "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260821"
            "&type=ALLBUT0999&response=json"
        )
        default_title = "2026-08-21 發行量加權指數與產業類指數"
        epistemic = "FACT"
        published = "2026-08-21"
    elif evidence_id.startswith("OFFICIAL:MARKET_BREADTH"):
        source = "TWSE/TPEx官方EOD整合"
        link = (
            "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260821"
            "&type=ALLBUT0999&response=json"
        )
        default_title = "2026-08-21 上市櫃漲跌家數與成交資料"
        epistemic = "FACT"
        published = "2026-08-21"
    elif evidence_id.startswith("OFFICIAL:TWSE_INSTITUTIONAL_FLOW"):
        source = "臺灣證券交易所"
        link = row.get("source_url")
        default_title = "2026-08-21 三大法人買賣金額統計"
        epistemic = "FACT"
        published = "2026-08-21"
    elif evidence_id.startswith("OFFICIAL_EOD"):
        source = row.get("source_name", "臺灣證券交易所")
        link = row.get("source_url")
        default_title = (
            f"{row.get('company_name', '')}（{row.get('security_id', '')}）"
            f" 2026-08-21 官方收盤資料"
        )
        epistemic = "FACT"
        published = "2026-08-21"
    else:
        source = row.get("source_name", "來源")
        link = row.get("url")
        default_title = row.get("title", evidence_id)
        epistemic = row.get("epistemic_status", "REPORTED")
        published = row.get("published_at")
    if evidence_id.startswith("OFFICIAL:TWSE_INDEX_AND_SECTORS"):
        human_link = OFFICIAL_HUMAN_URLS["TWSE_INDEX_AND_SECTORS"]
    elif evidence_id.startswith("OFFICIAL:MARKET_BREADTH"):
        human_link = OFFICIAL_HUMAN_URLS["MARKET_BREADTH"]
    elif evidence_id.startswith("OFFICIAL:TWSE_INSTITUTIONAL_FLOW"):
        human_link = OFFICIAL_HUMAN_URLS["TWSE_INSTITUTIONAL_FLOW"]
    elif evidence_id.startswith("OFFICIAL_EOD"):
        human_link = OFFICIAL_HUMAN_URLS["OFFICIAL_EOD"]
    else:
        human_link = url or link
    raw_link = url or link
    return {
        "evidence_id": evidence_id,
        "epistemic_status": status or epistemic,
        "source_name": source_name or source,
        "title": title or default_title,
        "published_at": published,
        "fetched_at": row.get("fetched_at") or row.get("collected_at"),
        "url": human_link,
        "human_verification_url": human_link,
        "raw_api_url": raw_link if raw_link != human_link else None,
    }


def script_payload(text: str, sections: list[str]) -> dict[str, Any]:
    return {
        "character_target": "1600-2800",
        "character_count": len("".join(text.split())),
        "character_count_basis": "UNICODE_CODEPOINTS_EXCLUDING_WHITESPACE",
        "sections": sections,
        "full_text": text,
    }


def leader(index: dict[str, dict[str, Any]], security_id: str) -> dict[str, Any]:
    return index[next(key for key in index if key.startswith(f"OFFICIAL_EOD:{security_id}:"))]


def fact(text: str, *evidence_ids: str) -> dict[str, Any]:
    return {"text": text, "evidence_ids": list(evidence_ids)}


def script_one(pack: dict[str, Any]) -> str:
    return textwrap.dedent(f"""
    各位朋友，今天這一盤如果只看最後的收盤數字，會覺得市場很簡單：加權指數上漲290.55點，重新站回45,000點。但把早盤、盤中和收盤拆開看，今天其實不是一路順風，而是一場先被外部壓力嚇到、再靠權值股和幾個強勢族群把情緒拉回來的反攻。

    先把結果講清楚。加權指數收在45,224.29點，上漲290.55點，漲幅0.65%。盤後報導記錄，指數早盤最低一度到44,583.87點，盤中跌幅超過300點，最後收復45,000點。這個走法的話題性，不在於單純的紅K，而在於市場先把美債殖利率、海外股市偏弱和風險情緒放大，最後又用台積電和航運、金融把指數拉回來。

    市場廣度也比指數本身更值得看。今天上市有592家上漲、381家下跌、106家平盤；上櫃有414家上漲、367家下跌、93家平盤，另外4家漲跌資料未確認。換句話說，紅盤不是只有一兩檔權值股獨撐，上漲家數確實比下跌家數多。不過，這個廣度仍然不是全面普漲，因為電子零組件類指數下跌2.65%，電腦及週邊設備下跌1.65%，盤面明顯存在輪動。

    台積電是今天最清楚的穩盤主角。它收2,410元，上漲35元，成交金額約375.90億元，而且收在今日高點。聯發科收3,790元，上漲90元，成交金額約212.15億元，這兩檔一起走強，對指數和市場情緒都有幫助。但不要因此把所有大型科技股都歸類成同步轉強，鴻海反而收跌0.41%，電子零組件和電腦週邊也在跌，權值股內部仍然有分歧。

    再看產業方向，油電燃氣上漲3.42%，航運上漲3.37%，塑膠上漲3.08%，金融保險上漲2.53%；另一邊，電子零組件、電機機械、電腦週邊和通信網路走弱。我的解讀是，今天的反彈有廣度，但不是所有資金重新押回同一個AI故事，而是從弱勢電子零組件轉向航運、金融、記憶體等更有即時話題的族群。

    現貨法人資料也給了多方一點支持。臺灣證券交易所資料顯示，上市外資淨買超約283.05億元，投信淨買約18.78億元，自營商自營部位淨買約29.10億元，合計約331.06億元。這代表至少在上市現貨上，今天法人不是站在同一邊賣出。不過要注意，TPEx三大法人資料今天還沒有同日回傳，所以這裡只能說上市法人偏多，不能把它擴大成整個上市櫃市場都完成轉多。

    還有幾個常見的盤後說法，今天不能直接下結論。臺指期貨的基差、未平倉、外資期貨部位，選擇權Put/Call Ratio，以及借券資料都還沒有接入；兩市融資融券也還在等同日官方資料。因此，今天不能把早盤下殺解釋成外資期貨壓盤，也不能說尾盤拉回就是空單回補。這些都是可能的解釋，但目前不是已核實的事實。

    所以我會把今天定義成「指數重返45K、廣度改善，但產業輪動仍很明顯」的一天。多方的證據是指數收回45,000點、上市櫃上漲家數占優、台積電收在高點、上市法人合計買超；空方的提醒是電子零組件逆勢下跌、TPEx法人和衍生品部位還沒補齊，今天成交資料的市場範圍也要看清楚，不能只用一個漂亮的收盤點數就宣布盤勢全面翻多。

    明天我會看三件事。第一，45,000點能不能站穩，並且不是開盤摸到而是收盤留下來；第二，上漲家數能不能繼續高於下跌家數，如果指數上漲但下跌家數擴大，反彈就可能變窄；第三，台積電、聯發科和今天強勢的航運、金融能不能同時維持相對強度。若只剩一檔權值股撐指數，或電子零組件繼續大幅落後，今天的紅盤就要用輪動反彈來理解，而不是全面行情。

    對海外臺人來說，盤後摘要最重要的不是替你猜明天漲跌，而是把盤面分成已經發生的事和下一個交易日要驗證的問題。今天已經發生的是：指數從跌逾300點的位置拉回、收復45K，上市法人偏買，資金也確實轉向航運與金融。還沒有發生、所以不能先講滿的，是期貨部位是否支持反彈、TPEx法人是否同步，以及這個輪動能不能延續。

    你覺得今天的45K，是一次有廣度的修復，還是高檔震盪中的反彈？明天收盤，我們就用45,000點、漲跌家數和強勢族群的成交金額回頭驗證。以上是盤後資料整理與情境分析，不是投資建議。
    """).strip()


def script_two(pack: dict[str, Any]) -> str:
    return textwrap.dedent("""
    大家好，歡迎來到收盤夜話。今天如果你只看大盤，會說臺股重返45K；但如果把成交金額和族群拆開，真正把市場注意力拉回來的，其實是南亞科、華邦電這一組記憶體雙雄。問題是，這到底是記憶體主線重新確認，還是昨天強、今天再跟著情緒延伸的一段行情？

    先看兩檔股票的收盤結果。南亞科收528元，上漲11元、漲幅2.13%，成交金額約334.94億元；華邦電收181元，上漲4.5元、漲幅2.55%，成交金額約201.35億元。兩檔合計成交金額超過536億元，單看市場注意力，確實已經不是普通的個股波動。南亞科成交量約6,412.8萬股，華邦電成交量約1.127億股，價和量都進入今天的盤面前段班。

    新聞面也有幾個可以核對的催化。中央社和其他媒體報導，SK海力士被韓媒指可能在日本宮城縣投資數十兆韓元興建記憶體工廠；同一天，市場也在討論美光把資料中心需求形容為高於可承諾供應約50%，並在美國投入100億美元設立AI記憶體研發中心。這些消息共同推高了記憶體的注意度，但要把話說準：它們是產業新聞和市場情緒的證據，不是南亞科或華邦電當季獲利已經因此增加的直接證明。

    為什麼今天這題值得收盤後再講一次？因為它同時滿足三個條件。第一，兩檔同題材股票同日走強，不是單一股票獨唱；第二，成交金額都很大，市場真的有人在看、有人在換手；第三，海外原廠的投資與供需訊息，讓記憶體不只是臺股內部的短線故事。這比看到一檔股票突然漲停，就直接說主力進場，證據更完整。

    但今天也不能只講多方。南亞科盤中最高534元，最低512元，收盤528元；華邦電最高182元、最低174.5元，收181元。它們都有明顯的盤中振幅，代表市場對這個題材的看法並不平靜。官方收盤資料能確認價格、成交量和成交金額，新聞能確認市場在討論什麼，卻不能替我們確認每一筆成交背後是長線建倉、短線追價，還是隔日交易。沒有期貨、借券和融資融券的同日資料，就不要把擁擠度寫成確定答案。

    再把記憶體放回今天的整個盤面。加權指數上漲0.65%，航運和金融走強，電子零組件類指數卻下跌2.65%。也就是說，記憶體雙雄雖然表現不錯，但它們並沒有帶動所有電子股同步上漲。欣興收跌4.82%，景碩跌4.70%，南電跌5.02%，台光電跌5.10%，同樣是市場熟悉的AI和載板供應鏈，今天反而成為下跌的一側。這個反差很適合拿來提醒觀眾：題材強，不等於整個產業每一家公司都同樣受惠。

    我的看法是，今天的記憶體比較像「事件、價格、成交」暫時對上了焦點，但主線能不能延續，還要等新的供需證據。SK海力士可能赴日擴產，長期看是產能與區域布局訊息；美光說需求高於供給，則是管理層對需求的描述；南亞科和華邦電上漲，是臺股投資人當天的交易結果。這三層訊息不能直接畫成一條因果線，中間還缺價格、訂單、財報或公司公告的更直接連接。

    明天我會看三個檢查點。第一，南亞科和華邦電是否至少一檔維持成交金額前段，另一檔也沒有放量長黑；第二，記憶體強勢是否擴散到更多公司，而不是只靠兩檔雙雄撐住；第三，有沒有新的公司公告、原廠報價或第二家獨立來源補上供需證據。如果明天兩檔一起開高走低、成交量快速萎縮，那今天更像情緒延伸；如果量能維持、族群擴散，才比較接近主線正在形成。

    所以今天的結論不是「記憶體一定還會漲」，而是：它是今天最有市場注意度、也最值得繼續核對的一組題材。已確認的是兩檔收盤上漲、成交金額很大，外部也有SK海力士和美光相關報導；還沒確認的是臺廠獲利是否同步上修、報價是否真的轉強，以及這段行情是不是已經過熱。把這幾件事分開，才不會把一個有話題的收盤日，講成沒有退路的單邊故事。

    你覺得記憶體這一波現在是在主線中段，還是短線情緒高點？明天收盤，我們再用雙雄的相對強弱、成交金額和族群擴散一起驗證。以上是盤後資料整理與情境分析，不是投資建議。
    """).strip()


def script_three(pack: dict[str, Any]) -> str:
    return textwrap.dedent("""
    今天臺股還有一組很有畫面的主角，就是貨櫃三雄。大盤早盤一度下跌超過300點，最後收漲290.55點；但航運類指數上漲3.37%，萬海、陽明、長榮同步收紅。這個故事的重點不是「航運股今天很強」這一句，而是當電子零組件回檔的時候，航運能不能接住市場的注意力，成為今天反彈裡最有擴散感的族群。

    先看官方收盤數字。萬海收124.5元，上漲11元、漲幅9.69%，成交金額約104.31億元；陽明收64元，上漲3.7元、漲幅6.14%，成交金額約124.65億元；長榮收251.5元，上漲5.5元、漲幅2.24%，成交金額約81.68億元。三檔合計成交金額超過310億元，而且不是只有一檔上漲，這就是它比單一價量異動更適合做收盤題目的原因。

    新聞面同樣有對應。盤後報導提到，貨櫃三雄走強，市場關注運價在第三季傳統旺季的表現；另一篇報導則指出SCFI自6月以來維持相對高檔，航運股和相關ETF受到資金注意。這些報導能說明市場為什麼把航運拿出來討論，但它們不能直接等同於三家公司下一季獲利一定上修。運價、裝載率、成本和公司實際財報，還要另外核對。

    再看今天的產業輪動。航運上漲3.37%，金融保險上漲2.53%，塑膠上漲3.08%，同時電子零組件下跌2.65%，電腦及週邊設備下跌1.65%。這種一邊漲、一邊跌的盤面，顯示今天的反彈不是所有資金重新回到同一個方向，而是有資金在找相對強勢、也有資金在降低電子零組件的曝險。貨櫃三雄之所以有話題，正是因為它們在指數翻紅的過程中，提供了很清楚的另一條線索。

    但是，航運三雄也不能只看當日漲幅。萬海接近一成的漲幅，陽明成交量接近兩億股，代表短線交易非常熱；長榮漲幅相對溫和，說明族群內部並不是完全同步。官方資料可以確認誰漲得多、誰成交金額大，新聞可以確認市場在討論運價和旺季，卻沒有證據讓我們直接說是外資全面買進，或是三家公司都已經進入同一個獲利加速階段。TPEx法人、兩市融資融券和期貨部位目前仍是未知，短線籌碼不能先替盤面做結論。

    我的解讀是，今天航運是「族群擴散已出現、基本面延續仍待確認」。三檔一起收紅，比一檔突然漲停更有市場廣度；航運指數上漲，也比只看個股更能支持題目的成立。但運價高檔能維持多久、旺季是否已反映在股價、長榮和陽明能不能跟上萬海的強度，這些才是接下來真正要追的問題。

    明天我會看三件事。第一，萬海、陽明、長榮是否至少兩檔維持相對大盤強勢，並且沒有全部開高走低；第二，航運類指數是否繼續高於大盤，還是只剩個別股票撐場；第三，運價或公司公告有沒有新的、可獨立核對的資料。如果明天只有萬海繼續衝、另外兩檔量縮轉弱，題材就會從族群行情收斂成單股行情；如果三檔成交金額和相對強度都維持，航運才有機會繼續當作市場輪動的觀察主線。

    今天的收盤夜話，把航運放在記憶體和權值股旁邊看，會比只追單一熱門股更完整。臺股收盤重新站回45K是真的，貨櫃三雄同步走強也是真的；但運價對獲利的傳導、法人實際部位和下一個交易日的延續性，現在都還沒有全部確認。先把已發生的事講清楚，再把要驗證的地方留下來，才是盤後摘要真正有用的地方。

    你覺得今天的航運上漲，是資金短線換位，還是第三季旺季行情重新被市場定價？明天我們再用三雄的相對強弱和新的運價、公告資料回頭驗證。以上是盤後資料整理與情境分析，不是投資建議。
    """).strip()


def build_editorial(pack: dict[str, Any]) -> dict[str, Any]:
    date = pack["market_session_date"]
    idx = source_index(pack)
    d = pack["cash_market_source_pack"]["datasets"]
    datasets = {row["dataset_id"]: row for row in d}
    twse_index = f"OFFICIAL:TWSE_INDEX_AND_SECTORS:{date}"
    breadth = f"OFFICIAL:MARKET_BREADTH_AND_TURNOVER:{date}"
    flow = f"OFFICIAL:TWSE_INSTITUTIONAL_FLOW:{date}"
    eod = lambda sid: f"OFFICIAL_EOD:{sid}:{date}"
    news = {row["evidence_id"]: row for row in pack["news_leads"]}
    n = lambda eid: f"NEWS:{eid}"

    cards1 = [
        card(idx, twse_index), card(idx, breadth), card(idx, flow),
        card(idx, n("0ec8f20d-6be5-4699-b057-c3511364fbb2")),
        card(idx, eod("TWSE:2330")), card(idx, eod("TWSE:2454")),
    ]
    cards2 = [
        card(idx, eod("TWSE:2408")), card(idx, eod("TWSE:2344")),
        card(idx, n("3b585a80-fa29-449f-9979-78bcf576a2ec")),
        card(idx, n("1613f5a7-ceb5-4976-926f-2ae8d7b9c46f")),
        card(idx, n("8d8a68b7-6239-46f7-b8f6-99bdb8037862")),
    ]
    cards3 = [
        card(idx, eod("TWSE:2615")), card(idx, eod("TWSE:2609")),
        card(idx, eod("TWSE:2603")), card(idx, twse_index),
        card(idx, n("b23c5403-99be-46fb-9f24-17a661159427")),
        card(idx, n("77e30d9a-f960-410f-92bf-c38e4f4bde02")),
    ]
    cards4 = [
        card(idx, twse_index), card(idx, eod("TWSE:3037")),
        card(idx, eod("TWSE:3189")), card(idx, eod("TWSE:8046")),
        card(idx, n("3b015b32-9378-4da0-969f-49bac5ec2c4b")),
    ]
    cards5 = [
        card(idx, eod("TWSE:2454")), card(idx, n("c9619be6-4e81-46a0-b0df-f187167bb35a")),
        card(idx, twse_index), card(idx, flow),
        card(idx, n("434dfd54-6699-45af-be11-33879dc03ca7")),
    ]

    return {
        "schema_version": "ben-close-talk-editorial.v0.1",
        "market_session_date": date,
        "data_as_of": pack["data_as_of"],
        "channel_id": "ch-02-tw-close-night-talk",
        "channel_name": "收盤夜話",
        "status": "DRAFT_FOR_HUMAN_REVIEW",
        "style_pack_id": "ben-tw-close-talk-v0.1",
        "style_pack_status": "PROVISIONAL_TWO_FULL_TRANSCRIPTS",
        "ranking_method": "EDITORIAL_RULES_V0_1",
        "ranking_note": "先看市場影響範圍與事件強度，再看跨來源注意度、證據完整度、頻道適配與次日可驗證性；價量異動不單獨等於熱點。",
        "known_data_gaps": [
            "TPEx指數與TPEx三大法人尚未取得同日資料。",
            "兩市融資融券、臺指期貨基差/未平倉/法人部位、選擇權Put/Call Ratio與借券資料尚未接入。",
            "X只作為注意度與觀點線索，不能升級為財經事實；本稿未用X替代官方資料。",
        ],
        "angles": [
            {
                "rank": 1,
                "editorial_state": "CONFIRMED_HOT",
                "episode_question": "臺股從早盤跌逾300點到收復45K，這是全面回暖，還是權值股與輪動族群合力修復？",
                "title_options": [
                    "【臺股重返45K】早盤跌逾300點後翻紅！台積電撐盤、航運金融接棒，反彈全面嗎？",
                    "臺股收漲290點站回45,000：上市法人買超，但電子零組件為何還在跌？",
                    "【收盤夜話】指數紅、產業卻分裂：今天到底是反轉，還是資金換位？",
                ],
                "why_today": "加權指數收復45,000點，早盤一度跌逾300點；上市櫃上漲家數占優、上市法人偏買，但電子零組件類指數逆勢下跌，形成全市場都在修復與產業明顯分裂的同日矛盾。",
                "why_this_channel": "最符合收盤夜話從大盤、廣度、法人到明日觀察的固定路徑，海外觀眾不用盯盤也能理解今天紅盤背後的結構。",
                "confirmed_facts": [
                    fact("加權指數收45,224.29點，上漲290.55點，漲幅0.65%。", twse_index),
                    fact("上市上漲592家、下跌381家；上櫃上漲414家、下跌367家，另有4家漲跌未確認。", breadth),
                    fact("上市外資淨買約283.05億元、投信淨買約18.78億元，自營商自營部位淨買約29.10億元，上市三大法人合計淨買約331.06億元。", flow),
                    fact("台積電收2,410元、上漲35元；盤後報導記錄台股成交量約7,192.8億元。", eod("TWSE:2330"), n("0ec8f20d-6be5-4699-b057-c3511364fbb2")),
                ],
                "interpretation": "今天的多方證據是指數從低點拉回、上漲家數占優、上市法人偏買；空方提醒則是電子零組件、電腦週邊與通信網路走弱，TPEx法人和衍生品資料尚未同日確認。因此比較準確的說法是廣度改善、資金輪動，尚不能宣布所有產業同步轉強。",
                "unknowns": [
                    "TPEx三大法人尚未取得同日回傳，不能把上市法人方向直接外推到整個上市櫃市場。",
                    "臺指期貨、選擇權與借券資料尚未接入，不能把早盤下殺或尾盤拉回解釋成特定部位操作。",
                    "成交量新聞為媒體報導值，官方EOD覆蓋成交額是已抓取證券的加總，兩者口徑不同。",
                ],
                "anchor_securities": ["TWSE:2330", "TWSE:2454", "TWSE:2615"],
                "tomorrow_checkpoints": [
                    {"metric": "加權指數45,000點", "positive_if": "收盤站穩45,000點", "caution_if": "再度跌破44,583點附近早盤低點", "evidence_ids": [twse_index, n("0ec8f20d-6be5-4699-b057-c3511364fbb2")]},
                    {"metric": "市場廣度", "positive_if": "上市櫃上漲家數持續高於下跌家數", "caution_if": "指數上漲但下跌家數反超", "evidence_ids": [breadth]},
                    {"metric": "上市法人與強勢族群", "positive_if": "法人買超延續且航運/金融不只剩單一股票", "caution_if": "法人轉賣、電子弱勢擴大", "evidence_ids": [flow, twse_index]},
                ],
                "ranking_reasons": ["影響全市場且有早盤急跌到收盤翻紅的明顯情節", "指數、廣度、法人和媒體可交叉核對", "明日可用45K、漲跌家數與法人方向直接驗證"],
                "source_cards": cards1,
                "script": script_payload(script_one(pack), ["cold_open", "market_snapshot", "breadth_and_sectors", "anchor_story_one", "cash_flow", "unknowns", "tomorrow_checkpoints", "audience_question", "risk_boundary"]),
            },
            {
                "rank": 2,
                "editorial_state": "CONFIRMED_HOT",
                "episode_question": "南亞科、華邦電同步走強且成交金額很大，記憶體是主線重新確認，還是消息帶動的短線情緒？",
                "title_options": [
                    "【記憶體雙雄再點火】南亞科528、華邦電181：SK海力士赴日設廠，主線續不續？",
                    "南亞科成交335億、華邦電201億！記憶體行情在中段，還是已經過熱？",
                    "【收盤夜話】美光說需求高於供給50%，臺股記憶體雙雄真的接到春天了嗎？",
                ],
                "why_today": "南亞科與華邦電同日上漲、合計成交金額超過536億元；SK海力士赴日擴產、美光需求高於供給等48小時內產業訊息，讓價格、成交與跨市場注意度同時出現。",
                "why_this_channel": "頻道既有樣本擅長用雙主角拆解盤面，這一題能保留雙股敘事，同時把原廠新聞、官方收盤數字和不能過度推論的部分分開。",
                "confirmed_facts": [
                    fact("南亞科收528元，上漲11元、漲幅2.13%，成交金額約334.94億元。", eod("TWSE:2408")),
                    fact("華邦電收181元，上漲4.5元、漲幅2.55%，成交金額約201.35億元。", eod("TWSE:2344")),
                    fact("中央社報導SK海力士可能在日本宮城縣投資數十兆韓元興建記憶體工廠。", n("3b585a80-fa29-449f-9979-78bcf576a2ec")),
                    fact("媒體報導美光管理層表示資料中心客戶需求較其能承諾供應量高約50%。", n("1613f5a7-ceb5-4976-926f-2ae8d7b9c46f")),
                ],
                "interpretation": "兩檔同題材股票同步上漲且成交金額進入市場前列，確實比單一價量異動更接近可講的熱點；但SK海力士的可能擴產是產能布局訊息，美光的需求描述是原廠觀點，兩者都不能直接證明南亞科或華邦電當季獲利會同步上修。",
                "unknowns": [
                    "FactPack沒有獨立可核驗的DRAM現貨或合約報價變化。",
                    "沒有證據證明海外原廠消息與兩檔個股當日漲幅存在單一直接因果。",
                    "兩市融資融券、期貨與借券資料尚未取得，短線擁擠度未知。",
                ],
                "anchor_securities": ["TWSE:2408", "TWSE:2344"],
                "tomorrow_checkpoints": [
                    {"metric": "雙雄相對強弱", "positive_if": "至少一檔續強且另一檔沒有放量長黑", "caution_if": "兩檔同步開高走低並吞回大部分漲幅", "evidence_ids": [eod("TWSE:2408"), eod("TWSE:2344")]},
                    {"metric": "成交金額與族群擴散", "positive_if": "雙雄仍在成交前段且更多記憶體股跟上", "caution_if": "量能急縮或只剩單一股票撐場", "evidence_ids": [eod("TWSE:2408"), eod("TWSE:2344") ]},
                    {"metric": "供需新證據", "positive_if": "出現公司公告、原廠報價或第二家獨立來源", "caution_if": "討論只重複擴產與需求口號", "evidence_ids": [n("3b585a80-fa29-449f-9979-78bcf576a2ec"), n("1613f5a7-ceb5-4976-926f-2ae8d7b9c46f")]},
                ],
                "ranking_reasons": ["兩檔同題材股票同步上漲且合計成交金額超過536億元", "外部原廠新聞與臺股價格形成跨來源共振", "雙主角符合頻道敘事且有清楚的次日驗證點"],
                "source_cards": cards2,
                "script": script_payload(script_two(pack), ["cold_open", "two_stock_snapshot", "news_catalysts", "counterevidence", "interpretation", "tomorrow_checkpoints", "audience_question", "risk_boundary"]),
            },
            {
                "rank": 3,
                "editorial_state": "CONFIRMED_HOT",
                "episode_question": "電子零組件回檔時，貨櫃三雄同步走強，航運能不能成為今天反彈的另一條主線？",
                "title_options": [
                    "【貨櫃三雄接棒】萬海大漲9.69%、陽明6.14%、長榮也紅：航運是換位還是主線？",
                    "電子零組件跌2.65%，航運卻漲3.37%：臺股45K靠誰接住？",
                    "【收盤夜話】萬海、陽明、長榮一起動，第三季旺季行情重新定價了嗎？",
                ],
                "why_today": "萬海、陽明、長榮同步收紅，航運類指數上漲3.37%，三檔合計成交金額超過310億元；盤後新聞同時提到運價高檔與第三季旺季，族群擴散比單一股票更有話題。",
                "why_this_channel": "收盤夜話需要把大盤輪動講給沒有盯盤的人，貨櫃三雄提供清楚的同族群比較，也能和電子零組件下跌形成當日盤面對照。",
                "confirmed_facts": [
                    fact("萬海收124.5元，上漲11元、漲幅9.69%，成交金額約104.31億元。", eod("TWSE:2615")),
                    fact("陽明收64元，上漲3.7元、漲幅6.14%，成交金額約124.65億元。", eod("TWSE:2609")),
                    fact("長榮收251.5元，上漲5.5元、漲幅2.24%，成交金額約81.68億元。", eod("TWSE:2603")),
                    fact("盤後報導提到SCFI自6月以來維持相對高檔、第三季傳統旺季帶動航運股注意度。", n("b23c5403-99be-46fb-9f24-17a661159427")),
                ],
                "interpretation": "三檔同族群同步走強、航運類指數也上漲，已經比單股異動更有族群證據；但運價對獲利的傳導、裝載率與成本仍需要公司公告或財報確認。今天可以說航運是輪動中的強勢族群，不能直接說三家公司進入同一個獲利加速階段。",
                "unknowns": [
                    "沒有同日TPEx法人、融資融券、期貨與借券資料可判斷短線部位。",
                    "運價新聞不能單獨證明三家公司下一季獲利已經上修。",
                    "萬海漲幅明顯高於長榮，族群內部是否真正同步仍待下一個交易日確認。",
                ],
                "anchor_securities": ["TWSE:2615", "TWSE:2609", "TWSE:2603"],
                "tomorrow_checkpoints": [
                    {"metric": "三雄相對大盤強弱", "positive_if": "至少兩檔維持強於大盤且沒有全部開高走低", "caution_if": "只剩萬海單獨上攻", "evidence_ids": [eod("TWSE:2615"), eod("TWSE:2609"), eod("TWSE:2603")]},
                    {"metric": "航運類指數", "positive_if": "航運類指數續強且族群成交金額不縮", "caution_if": "指數翻紅但航運快速落後", "evidence_ids": [twse_index]},
                    {"metric": "運價或公司公告", "positive_if": "出現新的可獨立核對運價、公告或財報訊息", "caution_if": "只剩重複的旺季敘事", "evidence_ids": [n("b23c5403-99be-46fb-9f24-17a661159427")]},
                ],
                "ranking_reasons": ["三檔同族群同步收紅，合計成交金額超過310億元", "航運類指數與盤後運價新聞互相呼應", "和電子零組件走弱形成清楚的市場輪動對照"],
                "source_cards": cards3,
                "script": script_payload(script_three(pack), ["cold_open", "sector_snapshot", "three_stock_comparison", "news_catalyst", "counterevidence", "tomorrow_checkpoints", "audience_question", "risk_boundary"]),
            },
            {
                "rank": 4,
                "editorial_state": "MARKET_TENSION",
                "episode_question": "同樣是AI與電子供應鏈，記憶體走強，欣興、景碩、南電和台光電卻同步回檔，市場在重新挑選什麼？",
                "title_options": [
                    "【AI族群大分歧】記憶體走強，載板四強卻跌4%到5%：資金在換哪裡？",
                    "欣興1085、南電1135都重挫：AI題材沒有消失，為何股票先分家？",
                    "【收盤夜話】同一個AI故事，今天為什麼有人漲、有人跌？",
                ],
                "why_today": "電子零組件類指數下跌2.65%，欣興、景碩、南電、台光電等高成交個股跌幅集中在約4%至5%，與記憶體和航運走強形成強烈反差。",
                "why_this_channel": "這是盤後最需要被解釋的矛盾之一：指數上漲不等於所有AI供應鏈都強，頻道可以用白話拆出今日資金輪動而非只報漲幅。",
                "confirmed_facts": [
                    fact("電子零組件類指數下跌2.65%。", twse_index),
                    fact("欣興收1085元、下跌4.82%，成交金額約238.07億元。", eod("TWSE:3037")),
                    fact("景碩收811元、下跌4.70%；南電收1135元、下跌5.02%。", eod("TWSE:3189"), eod("TWSE:8046")),
                    fact("盤後報導記錄載板三雄跌逾4%，同日記憶體和貨櫃族群走強。", n("3b015b32-9378-4da0-969f-49bac5ec2c4b")),
                ],
                "interpretation": "今天不是AI題材消失，而是市場把同一個大題材拆成不同分支重新定價。官方資料能確認載板與電子零組件跌幅，新聞能確認市場注意到記憶體與航運較強；但訂單或公司基本面差異還沒有在本資料包內完整核驗。",
                "unknowns": ["各公司當日跌幅的具體催化劑尚未由公司公告逐一確認。", "不能只靠同產業同日漲跌推論供應鏈因果。", "融資融券、借券和期貨部位尚未接入，短線賣壓來源未知。"],
                "anchor_securities": ["TWSE:3037", "TWSE:3189", "TWSE:8046"],
                "tomorrow_checkpoints": [
                    {"metric": "電子零組件類指數", "positive_if": "跌幅收斂且不再落後大盤", "caution_if": "指數續漲但電子零組件跌幅擴大", "evidence_ids": [twse_index]},
                    {"metric": "載板三雄相對強弱", "positive_if": "至少兩檔止跌且成交不失控", "caution_if": "三檔同步放量破低", "evidence_ids": [eod("TWSE:3037"), eod("TWSE:3189"), eod("TWSE:8046")]},
                ],
                "ranking_reasons": ["漲跌分化比單純漲幅更能解釋今日盤面", "高成交個股提供可核對的代表性樣本", "與記憶體、航運強勢形成鮮明反差"],
                "source_cards": cards4,
            },
            {
                "rank": 5,
                "editorial_state": "EVENT_RETEST",
                "episode_question": "聯發科在搶單傳言後反彈2.43%，這是止跌訊號，還是消息風險尚未解除？",
                "title_options": [
                    "【聯發科反彈90元】搶單傳言後重新站回3790：止跌了，還是只是一天紅？",
                    "AMD、Marvell爭搶Google ASIC傳言未平，聯發科今天為何翻紅？",
                    "【收盤夜話】聯發科反彈要看什麼，不是只看今天漲幾塊？",
                ],
                "why_today": "聯發科收3790元、上漲2.43%，但48小時內仍有搶單傳言與投信連續賣超的報導；今天反彈與前期消息壓力同時存在，適合做成明日驗證型題目。",
                "why_this_channel": "收盤夜話需要把一檔權值股的價格反應和新聞風險放在一起，說清楚什麼是已發生的反彈，什麼還不能叫做趨勢反轉。",
                "confirmed_facts": [
                    fact("聯發科收3790元，上漲90元、漲幅2.43%，成交金額約212.15億元。", eod("TWSE:2454")),
                    fact("媒體報導聯發科受到AMD與Marvell爭搶Google AI ASIC傳言影響，投信連續四天共賣超5654張。", n("c9619be6-4e81-46a0-b0df-f187167bb35a")),
                    fact("上市法人今日合計淨買約331.06億元，但TPEx法人同日資料尚未取得。", flow),
                ],
                "interpretation": "今天的股價反彈是已確認的市場結果，新聞傳言是注意度來源；兩者都不能單獨證明訂單真的轉向或賣壓完全結束。比較有用的問題是聯發科能否在消息未完全釐清時守住反彈，並且成交和法人方向是否支持。",
                "unknowns": ["Google ASIC供應商傳言沒有公司正式公告核實。", "投信後續是否停止賣超、外資與投信分歧是否收斂尚待新資料。", "期貨選擇權和借券資料未接入，無法判斷衍生品壓力。"],
                "anchor_securities": ["TWSE:2454"],
                "tomorrow_checkpoints": [
                    {"metric": "聯發科反彈延續", "positive_if": "收盤維持在今日收盤附近且成交不急縮", "caution_if": "快速跌回今日低點3695元附近", "evidence_ids": [eod("TWSE:2454")]},
                    {"metric": "法人方向", "positive_if": "投信賣壓收斂且上市法人合計未轉大幅賣超", "caution_if": "股價反彈但法人再度同步賣出", "evidence_ids": [flow]},
                    {"metric": "消息核實", "positive_if": "公司公告或多家獨立來源補充訂單事實", "caution_if": "仍只有傳言與評論重複", "evidence_ids": [n("c9619be6-4e81-46a0-b0df-f187167bb35a")]},
                ],
                "ranking_reasons": ["權值股反彈與前期負面傳言形成可追蹤的事件重測", "成交金額超過212億元，市場注意度足夠", "明日可用價格、法人和新公告驗證"],
                "source_cards": cards5,
            },
        ],
        "input_fingerprint": "close-talk-base-2026-08-21",
        "run_id": "close-talk-editorial:2026-08-21:base",
        "studio_artifact": "BEN_CONTENT_STUDIO_DAILY",
        "studio_artifact_version": "1.0",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--fact-pack", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    pack = load_pack(Path(args.fact_pack))
    editorial = build_editorial(pack)
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    Path(args.output).write_text(json.dumps(editorial, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"status": "PASS", "date": editorial["market_session_date"], "angles": len(editorial["angles"])}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
