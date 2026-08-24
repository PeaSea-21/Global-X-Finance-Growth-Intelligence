from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from opencc import OpenCC


ROOT = Path(__file__).resolve().parents[1]
CHANNEL_ORDER = (
    "個股顯微鏡",
    "收盤夜話",
    "產業透視鏡",
    "權值旗艦",
    "資金雷達",
    "那指火箭",
    "板塊輪動儀",
    "暗池雷達",
    "期權守門人",
    "財報獵人",
)
WAITING_CHANNELS = {"個股顯微鏡", "產業透視鏡", "財報獵人"}
TRADITIONAL = OpenCC("s2twp")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _character_count(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def _traditional(value: str) -> str:
    return TRADITIONAL.convert(value)


def _news_item(
    items: list[dict[str, Any]],
    title_fragment: str,
    source_name: str | None = None,
) -> dict[str, Any]:
    for item in items:
        if title_fragment not in str(item.get("title") or ""):
            continue
        if source_name and item.get("source_name") != source_name:
            continue
        return item
    source_suffix = f" from {source_name}" if source_name else ""
    raise ValueError(f"missing weekend item containing {title_fragment!r}{source_suffix}")


def _news_card(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_id": item["source_name"],
        "evidence_class": item.get("epistemic_status") or "REPORTED",
        "title": item["title"],
        "published_at": item["published_at"],
        "fetched_at": item.get("fetched_at"),
        "freshness_bucket": item["freshness_bucket"],
        "human_verification_url": item["human_verification_url"],
        "raw_api_url": None,
    }


def _official_card(
    source_id: str,
    title: str,
    human_url: str,
    raw_url: str,
) -> dict[str, Any]:
    return {
        "source_id": source_id,
        "evidence_class": "OFFICIAL_EOD",
        "title": title,
        "published_at": "2026-08-21T13:30:00+08:00",
        "freshness_bucket": "LAST_MARKET_SESSION",
        "human_verification_url": human_url,
        "raw_api_url": raw_url,
    }


def _topic(
    *,
    topic_id: str,
    title_options: list[str],
    why_now: list[str],
    why_channel: list[str],
    facts: list[str],
    unknowns: list[str],
    evidence: list[dict[str, Any]],
    script_text: str = "",
    editorial_status: str = "DRAFT_FOR_HUMAN_REVIEW",
    candidate_type: str = "CHANNEL_EDITORIAL_DRAFT",
) -> dict[str, Any]:
    converted_titles = [_traditional(value) for value in title_options]
    converted_why_now = [_traditional(value) for value in why_now]
    converted_why_channel = [_traditional(value) for value in why_channel]
    converted_facts = [_traditional(value) for value in facts]
    converted_unknowns = [_traditional(value) for value in unknowns]
    script = _traditional(script_text.strip())
    return {
        "candidate_id": topic_id,
        "candidate_type": candidate_type,
        "editorial_status": editorial_status,
        "title": converted_titles[0],
        "title_options": converted_titles,
        "why_now": converted_why_now,
        "why_channel": converted_why_channel,
        "facts": converted_facts,
        "unknowns": converted_unknowns,
        "evidence": evidence,
        "opinion_evidence": [],
        "script_text": script,
        "script_character_count": _character_count(script),
        "risk_flags": ["DRAFT_FOR_HUMAN_REVIEW", "NOT_INVESTMENT_ADVICE"],
    }


def _close_talk_topics(editorial: dict[str, Any]) -> list[dict[str, Any]]:
    topics: list[dict[str, Any]] = []
    for angle in editorial.get("angles", []):
        script = angle.get("script") or {}
        cards = []
        for card in angle.get("source_cards", []):
            cards.append(
                {
                    "source_id": card.get("source_name") or card.get("source_id"),
                    "evidence_class": card.get("epistemic_status") or "SOURCE",
                    "title": card.get("title") or card.get("claim"),
                    "published_at": card.get("published_at"),
                    "fetched_at": card.get("fetched_at") or card.get("collected_at"),
                    "freshness_bucket": card.get("freshness_bucket") or "LAST_MARKET_SESSION",
                    "human_verification_url": card.get("human_verification_url") or card.get("url"),
                    "raw_api_url": card.get("raw_api_url"),
                }
            )
        full_text = str(script.get("full_text") or "")
        topics.append(
            {
                "candidate_id": angle.get("angle_id") or f"close-talk-{angle.get('rank')}",
                "candidate_type": "CLOSE_TALK_EDITORIAL",
                "editorial_status": angle.get("editorial_state") or editorial.get("status"),
                "title": (angle.get("title_options") or [angle.get("episode_question")])[0],
                "title_options": angle.get("title_options") or [],
                "why_now": [angle.get("why_today")] if angle.get("why_today") else [],
                "why_channel": [angle.get("why_this_channel")] if angle.get("why_this_channel") else [],
                "facts": [
                    fact.get("text") if isinstance(fact, dict) else fact
                    for fact in angle.get("confirmed_facts", [])
                ],
                "unknowns": angle.get("unknowns") or [],
                "evidence": cards,
                "opinion_evidence": [],
                "script_text": full_text,
                "script_character_count": _character_count(full_text),
                "risk_flags": angle.get("risk_flags") or ["DRAFT_FOR_HUMAN_REVIEW"],
            }
        )
    return topics


def _build_new_topics(
    weekend_items: list[dict[str, Any]],
    weight_topics: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    twse_human = "https://www.twse.com.tw/zh/trading/historical/mi-index.html"
    twse_raw = (
        "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX"
        "?date=20260821&type=ALLBUT0999&response=json"
    )
    twse_index = _official_card(
        "臺灣證券交易所",
        "2026-08-21 上市收盤行情",
        twse_human,
        twse_raw,
    )
    twse_flow = _official_card(
        "臺灣證券交易所",
        "2026-08-21 三大法人買賣金額統計",
        "https://www.twse.com.tw/zh/trading/foreign/t86.html",
        "https://openapi.twse.com.tw/v1/fund/BFI82U",
    )

    nvidia_earnings = _news_card(
        _news_item(weekend_items, "輝達將於8月26日公布上季財報", "經濟日報")
    )
    nvidia_price_cnbc = _news_card(
        _news_item(weekend_items, "Nvidia customers reportedly warned", "CNBC")
    )
    nvidia_price_tw = _news_card(
        _news_item(weekend_items, "記憶體成本攀升，NVIDIA", "科技新報財經")
    )
    extended_hours = _news_card(
        _news_item(weekend_items, "美股延長交易台灣複委託跟進", "中央社財經")
    )
    ai_capex = _news_card(
        _news_item(weekend_items, "AI產業鏈從資本支出擴張、轉向獲利驗證", "ETtoday財經雲")
    )
    ai_profit = _news_card(
        _news_item(weekend_items, "台股企業Q2狂賺1.8兆創新高", "Yahoo奇摩股市")
    )
    server_odm = _news_card(
        _news_item(weekend_items, "三大伺服器代工廠財報3率", "Yahoo奇摩股市")
    )
    packaging = _news_card(
        _news_item(weekend_items, "封測五雄砸逾4,600億擴產", "經濟日報")
    )
    market_box = _news_card(
        _news_item(weekend_items, "台股高檔震盪", "Yahoo奇摩股市")
    )
    fund_rotation = _news_card(
        _news_item(weekend_items, "投信由買轉賣台股資金風向變了", "Yahoo奇摩股市")
    )
    weekly_rotation = _news_card(
        _news_item(weekend_items, "台股一週跌586點市值蒸發", "Yahoo奇摩股市")
    )
    hon_hai_news = _news_card(
        _news_item(weekend_items, "鴻海財報創高卻一直跌", "Yahoo奇摩股市")
    )
    rising_yields = _news_card(
        _news_item(weekend_items, "Rising yields rattled the market", "CNBC")
    )

    weight_by_id = {topic["security_ids"][0]: topic for topic in weight_topics}
    tsmc = weight_by_id["TWSE:2330"]
    mediatek = weight_by_id["TWSE:2454"]
    hon_hai = weight_by_id["TWSE:2317"]
    delta = weight_by_id["TWSE:2308"]
    fubon = weight_by_id["TWSE:2881"]

    weighted_script = """
各位朋友，權值旗艦上線。最近一個交易日的台股看起來是漂亮反彈：8月21日加權指數收在45,224.29點，上漲290.55點。但真正要問的不是指數紅不紅，而是這根紅K到底由誰撐起來。

先看第一組主引擎。台積電收2,410元，上漲1.47%，成交金額約375.90億元；聯發科收3,790元，上漲2.43%，成交約212.15億元。兩檔同時走強，代表大型電子權值至少在收盤端提供了穩定力量。上市三大法人合計淨買約331.06億元，也讓這次反彈不只是散戶單邊追價。

但第二組訊號沒有完全同步。台達電只小漲0.29%，鴻海反而下跌0.41%；相對之下，富邦金大漲4.69%。這表示盤面並不是單純的AI權值全面回歸，而是電子核心、金融權值和其他大型股之間重新分工。尤其鴻海財報題材仍在，股價卻沒有跟著指數上行，這個背離比一句「大盤反彈」更值得追蹤。

這裡必須把界線講清楚。目前資料沒有正式成分權重，也沒有同日TAIFEX法人淨部位，因此不能計算每檔股票對指數貢獻幾點，更不能把走勢寫成外資刻意壓盤或拉抬。能確認的只有收盤價、成交額、法人現貨流向，以及權值股之間的相對強弱。

下一個交易日看三件事。第一，台積電和聯發科能否維持強於大盤；第二，鴻海是否補漲，否則AI權值仍是分裂；第三，金融權值的強勢能否延續。若三組同步，反彈的廣度才算擴大；若只剩台積電撐住指數，表面紅盤和內部結構就可能再次分家。這不是猜方向，而是把多空攻防拆成可以驗證的條件。
"""

    capital_script = """
今天資金雷達不只看哪一檔漲最多，而是看錢從哪裡撤、又往哪裡集中。最近一個交易日，加權指數雖然反彈290.55點，但週線仍下跌586點。就在大盤高檔整理的同時，媒體整理顯示航運一週逆勢上漲約13%，另有報導指出投信操作由買轉賣，電子與金融的配置方向出現變化。這三個訊號放在一起，才構成真正的資金換位問題。

先看官方收盤數據。富邦金8月21日收134元，上漲4.69%；貨櫃股方面，萬海上漲9.69%、陽明上漲6.14%、長榮上漲2.24%。同一天，台積電與聯發科也收紅，但鴻海下跌0.41%。所以這不是電子全面退潮，而是資金從單一AI權值，擴散到金融與航運，同時保留部分電子核心部位。

再看法人。上市三大法人合計淨買約331.06億元，代表現貨總量並沒有全面撤退；但總買超不能回答錢進了哪些產業。媒體提到投信由買轉賣、砍電子抱金融，這只能當作進一步核對的線索，不能直接推論所有法人都完成換倉。真正的產業資金雷達還需要板塊成交占比、跨股法人分布，以及至少連續兩到三個交易日的持續性。

因此，現在可以提出一個暫定結論：資金正在嘗試從擁擠的電子主線，向金融與航運分流，但還不能說新主線已經確立。下一個交易日，如果航運三雄成交額維持、金融權值續強，而且電子高檔股沒有再度全面吸回資金，輪動才有延續證據。反過來，如果航運量能迅速退潮、富邦金回吐，而台積電重新獨撐大盤，那今天看到的更可能只是短線避險與補漲。

資金雷達真正要抓的不是一根大紅K，而是資金能不能從一檔擴散到三檔、從一天延續到多天。這篇先把變化標出來，下一篇再用同一組條件驗證它到底是輪動，還是只有一天的煙火。
"""

    nasdaq_script = """
這一週那斯達克真正的主線，不只是指數漲跌，而是兩個事件同時逼近：輝達預計在8月26日公布上季財報，另一方面，多家媒體報導輝達客戶被告知，AI伺服器可能因記憶體成本上升而調價，漲幅超過15%。一個是需求與獲利的驗證，一個是成本能否轉嫁的測試，兩者會一起影響市場怎麼重估AI成長股。

先拆時間線。財報公布前，市場會先交易預期；財報公布後，真正重要的不是營收有沒有高於共識一點，而是資料中心需求、毛利率、供應能力和後續指引能不能同時站得住。若伺服器調價屬實，價格上升可能代表需求仍強，也可能代表成本壓力正在往客戶端轉移。只看「漲價」兩個字，無法判斷對晶片商、伺服器廠和雲端客戶誰最有利。

再看那指結構。輝達是大型科技與AI交易的重要錨點，但目前還沒有同時點的NDX、QQQ成分廣度和成交資料，所以不能把單一公司事件直接寫成整個那指一定向上或向下。較合理的做法，是觀察財報後半導體、雲端平台、伺服器供應鏈能否同步反應。若只有輝達一檔上漲，而其他AI成分股跟不上，那是單點行情；若漲勢向多個子產業擴散，才比較接近那指火箭重新點火。

對亞洲投資人還有一個制度變化。中央社報導，美股延長交易後，台灣複委託是否跟進將由券商自行評估。這代表未來亞洲時區的反應速度可能提升，但流動性、價差與券商實際開放時段仍需逐項確認，不能把「可評估」寫成「已全面上線」。

接下來看三個條件：財報指引是否支持高成長、伺服器漲價是否伴隨需求延續、以及AI漲勢是否從輝達擴散到那指其他大型成分股。三項同時成立，才是結構性利多；若毛利率或資本支出回報出現疑問，市場可能先重新定價。這集不押單一方向，只把這枚火箭需要的燃料、點火器和熄火條件列清楚。
"""

    rotation_script = """
AI硬體最近出現一個很有意思的矛盾：企業獲利仍在創高，資本支出也沒有停，但市場開始從「有AI就買」轉向追問「誰能把AI變成利潤」。這正是板塊輪動最容易發生的時刻。

第一個板塊是記憶體與伺服器成本。多家媒體報導，記憶體成本上升可能推動輝達AI伺服器調價超過15%。如果消息後續得到公司或供應鏈正式確認，受影響的不只輝達，還包括記憶體供應商、伺服器代工廠與雲端客戶。成本上升能不能順利轉嫁，會決定毛利留在哪一段。

第二個板塊是伺服器代工。最新報導把鴻海、廣達與緯穎的財報三率放在一起比較，顯示同樣承接AI需求，營運策略與獲利結構仍可能不同。這代表下一階段不能只看出貨量，還要看營業利益率、產品組合和客戶集中度。資金如果開始從純題材轉向獲利驗證，代工廠之間的股價差距可能進一步拉開。

第三個板塊是先進封裝。封測五雄被報導合計投入逾4,600億元擴產，反映AI帶來的產能需求仍在延伸。但擴產是長期供給，股價交易的是未來回報；如果折舊先上來、訂單或利用率沒有同步，資本支出也可能成為壓力。因此，擴產金額本身不是買進理由，而是後續追蹤產能利用率與獲利的起點。

台股企業第二季獲利被報導合計約1.8兆元並創新高，市場仍有基本面支撐；同時也有觀察指出，AI產業鏈正在從資本支出擴張走向獲利驗證。把這些線索放在一起，眼前的輪動不是AI對非AI，而是AI內部從故事、設備、產能，轉向毛利與現金流。

今天先不引用標普11大板塊ETF資金流，因為目前還沒有完整的XLK、XLF、XLE、XLV同時點數據。所以下一個驗證點很清楚：看記憶體漲價能否轉嫁、伺服器代工毛利能否改善、封裝擴產能否換成利用率。三條線誰先交出獲利，資金就更可能往誰那裡輪動；只靠新聞熱度而沒有財務兌現的板塊，則最容易先退潮。
"""

    dark_pool_script = """
各位朋友，今天暗池雷達先按下暫停鍵。不是市場沒有題目，而是8月26日輝達財報前，公開新聞已經非常熱：一邊是財報即將公布，一邊是AI伺服器可能因記憶體成本上升而調價超過15%。現貨事件很清楚，但真正能支持「暗池大單」或「期權主力方向」的原始資料，目前還沒有公開到足以核對。

這個差別非常重要。要判斷一筆期權交易，至少需要標的現價與時間、到期日、履約價、Call或Put、成交量、未平倉量、成交價、買賣方向證據、隱含波動率，以及它是不是多腿組合的一部分。少掉任何幾項，都可能把保護性Put、價差單、平倉或造市商對沖，誤寫成機構單邊看空。

同樣地，期權大單不等於暗池。真正的暗池或大宗交易，需要可核對的成交打印、時間、價格、數量與來源。現在只有財報與產業新聞，沒有這些欄位，所以這集不能說華爾街正在押注崩盤，也不能說主力提前埋伏拉升。把新聞熱度包裝成「千萬美元對賭」，看起來刺激，實際上是在跳過證據。

那這個頻道今天還能做什麼？可以先建立財報前的四項觀察表。第一，財報前後現貨是否突破並站穩關鍵區間；第二，近月與次月隱含波動率是否同步上升；第三，成交量放大後，未平倉量隔日是否真的增加；第四，異常合約能否排除多腿組合與深度實值對沖。只有四項資料齊全，才進入意圖分析。

公開新聞提供了事件背景：輝達財報日期、AI伺服器調價傳聞，以及AI資本支出回報的市場討論。但這些只能說明「為什麼值得監控」，不能回答「機構已經押哪一邊」。今天的結論就是資料不足時不亂下判斷。等原始期權鏈、OI變化與真實暗池打印到位，我們再把多種可能意圖逐一排除，而不是先寫結論再找證據。
"""

    options_script = """
多數人遇到輝達財報週，第一反應是買一張Call賭大漲，或買一張Put防崩盤。但期權守門人今天要先提醒：買方最大虧損雖然有限，並不代表這筆交易自然合理。財報前最容易被忽略的成本，是隱含波動率、時間價值與買賣價差。

公開資訊顯示，輝達預計在8月26日公布上季財報；同時，市場正在討論AI伺服器可能因記憶體成本上升而調價。這種事件密集的時段，期權價格往往會提前反映對波動的期待。即使你看對股價方向，如果實際波動不及期權定價，或財報後隱含波動率快速回落，買方仍可能虧損。方向、幅度與時間，三個條件缺一不可。

第一層先算最大損失。任何策略都要在下單前寫清楚最壞情境，而不是用「財報一定有行情」取代風控。買方要接受權利金可能大幅損失；賣方則必須知道裸賣Call或Put的尾端風險遠高於收到的權利金。沒有完整損益圖與保證金條件，不應把策略稱為穩定收益。

第二層看波動率結構。不能只看單一IV數字，還要比較近月與次月、財報前後到期日，以及同履約價附近的偏斜。目前還沒有即時IV、IV Rank、OI和波動率曲面，因此今天不提供特定合約，也不把任何履約價包裝成勝率較高。

第三層看執行環境。中央社報導，美股延長交易後，台灣複委託是否跟進由券商自行評估。延長時段不等於每個時段都有同樣流動性；夜盤價差、報價深度與券商規則都可能不同。對期權而言，流動性不足時的滑價，會直接改變原本漂亮的理論損益。

所以財報週的守門順序是：先確定最大虧損，再確認事件是否已反映在波動率，最後評估流動性與退出方案。資料不齊時，空手也是一種完整決策。這不是要你猜輝達漲跌，而是先確保無論結果如何，單一事件都不會把整個帳戶拖進無法承受的風險。
"""

    return {
        "權值旗艦": [
            _topic(
                topic_id="weighted-flagship:2026-08-21:market-rebound",
                title_options=[
                    "【45K攻防】台積電、聯發科撐盤，鴻海卻收黑：權值股真的同一條心？",
                    "台股收漲290點，五大權值只有四檔紅：下一站看誰補上？",
                    "【權值旗艦】電子核心與金融接棒，這次反彈廣度夠不夠？",
                ],
                why_now=["最近交易日指數重返45,000點，但五檔權值觀察股並未同步上漲。"],
                why_channel=["以指數為骨架比較台積電、聯發科、鴻海、台達電與富邦金的收盤分工。"],
                facts=[
                    "加權指數收45,224.29點，上漲290.55點。",
                    tsmc["why_now"][0],
                    mediatek["why_now"][0],
                    hon_hai["why_now"][0],
                    delta["why_now"][0],
                    fubon["why_now"][0],
                    "上市三大法人合計淨買約331.06億元。",
                ],
                unknowns=[
                    "未接入正式成分權重，不能計算各股精確指數貢獻。",
                    "未接入同日TAIFEX法人部位，不能推論期現貨動機。",
                ],
                evidence=[twse_index, twse_flow, hon_hai_news, market_box],
                script_text=weighted_script,
            )
        ],
        "資金雷達": [
            _topic(
                topic_id="capital-radar:2026-08-23:rotation-watch",
                title_options=[
                    "【資金換位】台股週跌586點，航運逆漲13%：電子撤、金融航運接？",
                    "富邦金漲4.69%、貨櫃三雄齊揚：資金真的離開AI了嗎？",
                    "投信由買轉賣後，誰在吸金？下一個交易日看三個續航條件",
                ],
                why_now=["週末24小時新聞同時出現投信配置變化、航運逆勢走強與台股箱型整理。"],
                why_channel=["把單日價量、法人現貨與至少三檔代表股放在一起判斷資金是否擴散。"],
                facts=[
                    "加權指數8月21日上漲290.55點，但媒體統計台股週線下跌586點。",
                    "媒體統計航運一週逆勢上漲約13%。",
                    "富邦金8月21日上漲4.69%。",
                    "萬海、陽明、長榮8月21日分別上漲9.69%、6.14%、2.24%。",
                ],
                unknowns=[
                    "尚未完成全產業成交占比与法人跨股分布，不能确认新主线已经成立。",
                    "TPEx同日法人资料仍不完整。",
                ],
                evidence=[twse_index, twse_flow, fund_rotation, weekly_rotation, market_box],
                script_text=capital_script,
            )
        ],
        "那指火箭": [
            _topic(
                topic_id="nasdaq-rocket:2026-08-23:nvidia-event-week",
                title_options=[
                    "【那指事件週】輝達8月26日財報撞上伺服器漲價：AI火箭還缺哪桶燃料？",
                    "NVIDIA財報倒數，AI伺服器傳漲逾15%：那指是需求強，還是成本壓力？",
                    "美股延長交易、輝達財報接棒：亞洲投資人這週盯三個條件",
                ],
                why_now=["輝達財報日期、AI伺服器調價報導與延長交易議題集中在同一個24小時窗口。"],
                why_channel=["从事件时间线、那指结构与亚洲交易影响拆解科技成长股。"],
                facts=[
                    "經濟日報報導輝達將於8月26日公布上季財報。",
                    "CNBC與科技新報均報導AI伺服器可能因記憶體成本上升而調價。",
                    "中央社報導台灣券商將自行評估是否跟進美股延長交易。",
                ],
                unknowns=[
                    "資料包沒有同時點NDX、QQQ成分廣度與成交資料。",
                    "調價消息仍需公司正式說法與財報毛利率交叉確認。",
                ],
                evidence=[nvidia_earnings, nvidia_price_cnbc, nvidia_price_tw, extended_hours],
                script_text=nasdaq_script,
            )
        ],
        "板塊輪動儀": [
            _topic(
                topic_id="sector-rotator:2026-08-23:ai-profit-test",
                title_options=[
                    "【AI不再齊漲】記憶體漲價、代工比毛利、封測砸4600億：資金選誰？",
                    "AI牛市進入獲利驗證：記憶體、伺服器、先進封裝誰先交成績？",
                    "從資本支出到現金流，AI硬體三板塊正在重新排隊",
                ],
                why_now=["最近24小時的消息同時指向記憶體成本、伺服器代工獲利与封装扩产。"],
                why_channel=["用三個以上AI子板塊比較成本、毛利與資本支出，而不是只拆一檔股票。"],
                facts=[
                    "媒體報導記憶體成本可能推升AI伺服器價格。",
                    "最新報導比較鴻海、廣達與緯穎財報三率。",
                    "經濟日報報導封測五雄合計投入逾4,600億元擴產。",
                    "Yahoo奇摩報導台股企業第二季合計獲利約1.8兆元。",
                ],
                unknowns=[
                    "未接入標普11大板塊ETF同時點資金流，這篇只能定位為AI子產業輪動研究稿。",
                    "擴產金額不等於未來利用率或獲利。",
                ],
                evidence=[nvidia_price_tw, server_odm, packaging, ai_profit, ai_capex],
                script_text=rotation_script,
                editorial_status="PROVISIONAL_PROFILE_MISMATCH_REVIEW",
            )
        ],
        "暗池雷達": [
            _topic(
                topic_id="dark-pool-radar:2026-08-23:no-flow-no-claim",
                title_options=[
                    "輝達8月26日財報前，暗池雷達為何先按暫停鍵？沒有OI就別亂講主力",
                    "NVIDIA財報很熱，但暗池大單在哪？缺這8個欄位不能下結論",
                    "別把期權成交叫暗池：輝達事件週的四項真實驗證表",
                ],
                why_now=["輝達財報與伺服器調價消息升溫，但当前资料没有原始期权链或暗池打印。"],
                why_channel=["把频道最容易出现的证据误区直接拆开，并列出下一步必须补齐的字段。"],
                facts=[
                    "經濟日報報導輝達將於8月26日公布上季財報。",
                    "CNBC與科技新報報導AI伺服器調價消息。",
                ],
                unknowns=[
                    "缺少原始暗池成交打印。",
                    "缺少原始期權鏈，以及合約到期日、履約價、成交量、OI、IV、Delta與買賣方向證據。",
                    "不能把新聞熱度推論成機構單邊意圖。",
                ],
                evidence=[nvidia_earnings, nvidia_price_cnbc, ai_capex],
                script_text=dark_pool_script,
                editorial_status="EVIDENCE_LIMITED_DRAFT",
            )
        ],
        "期權守門人": [
            _topic(
                topic_id="options-gatekeeper:2026-08-23:event-risk-framework",
                title_options=[
                    "輝達財報週別把期權當彩票：方向看對，為什麼還可能虧錢？",
                    "買Call賭財報、買Put防崩盤？先過最大虧損與IV兩道門",
                    "美股延長交易不等於更安全：財報週期權的三層風控",
                ],
                why_now=["輝達財報与延长交易议题让事件风险、波动率定价和流动性同时成为重点。"],
                why_channel=["以最大損失、波動率結構與執行流動性三層拆解，而非預測單邊行情。"],
                facts=[
                    "經濟日報報導輝達將於8月26日公布上季財報。",
                    "中央社報導台灣券商將自行評估是否跟進美股延長交易。",
                    "CNBC報導長天期殖利率上升使市場波動。",
                ],
                unknowns=[
                    "未取得即時IV、IV Rank、OI、波動率曲面與完整交易成本。",
                    "因此不提供特定履約價或賣方策略。",
                ],
                evidence=[nvidia_earnings, extended_hours, rising_yields],
                script_text=options_script,
            )
        ],
    }


def build_payload(
    *,
    site_data: dict[str, Any],
    style_payload: dict[str, Any],
    weekend_payload: dict[str, Any],
    editorial: dict[str, Any],
) -> dict[str, Any]:
    if weekend_payload.get("status") != "NEWS_CRAWL_PASS":
        raise ValueError("weekend source snapshot is not NEWS_CRAWL_PASS")
    if weekend_payload.get("snapshot_date") != "2026-08-23":
        raise ValueError("unexpected weekend snapshot date")
    if editorial.get("status") != "DRAFT_FOR_HUMAN_REVIEW":
        raise ValueError("close-talk editorial is not ready for review")
    if editorial.get("market_session_date") != site_data.get("market_session_date"):
        raise ValueError("close-talk and site market dates do not match")

    style_by_name = {
        row["channel_name"]: row for row in style_payload.get("channels", [])
    }
    if tuple(style_by_name) != CHANNEL_ORDER:
        raise ValueError("style pack channel order mismatch")

    new_topics = _build_new_topics(
        list(weekend_payload.get("items") or []),
        list(site_data.get("weight_topics") or []),
    )
    channels: list[dict[str, Any]] = []
    for order, name in enumerate(CHANNEL_ORDER, start=1):
        style = style_by_name[name]
        if name == "收盤夜話":
            topics = _close_talk_topics(editorial)
            content_status = "READY_LAST_MARKET_SESSION"
            content_date = editorial["market_session_date"]
            reason = "最近成功交易日的完整盤後文稿；週日不冒充同日收盤稿。"
        elif name in WAITING_CHANNELS:
            topics = []
            content_status = "WAITING_FOR_TRANSCRIPT_SAMPLES"
            content_date = None
            reason = "尚無完整文稿樣本，語言、開場、敘事與結尾保持UNKNOWN；至少需要2篇完整稿。"
        else:
            topics = new_topics[name]
            content_status = "PROVISIONAL_DRAFT_READY"
            content_date = weekend_payload["snapshot_date"]
            reason = "依現有稀疏樣本與24/48小時來源生成，等待Ben校準頻道口吻。"
        channels.append(
            {
                "channel_order": order,
                "channel_id": style["channel_id"],
                "channel_name": name,
                "style_status": style["status"],
                "style_confidence": style["confidence"],
                "content_status": content_status,
                "content_date": content_date,
                "profile_promise": _traditional(style["profile_promise"]),
                "audience": _traditional(style["audience"]),
                "language_style": _traditional(style["language_style"]),
                "opening_hook": _traditional(style["opening_hook"]),
                "narrative_logic": [_traditional(value) for value in style["narrative_logic"]],
                "ending_pattern": _traditional(style["ending_pattern"]),
                "profile_sample_alignment": style["profile_sample_alignment"],
                "reason": _traditional(reason),
                "topics": topics,
            }
        )

    now = datetime.now(timezone(timedelta(hours=8))).isoformat(timespec="seconds")
    workbench = {
        "artifact": "BEN_FIRST10_CHANNEL_EDITORIAL_WORKBENCH",
        "schema_version": "1.0",
        "status": "DRAFT_FOR_HUMAN_REVIEW",
        "generated_at": now,
        "source_snapshot_date": weekend_payload["snapshot_date"],
        "last_market_session_date": site_data["market_session_date"],
        "fresh_event_window_hours": 24,
        "context_window_hours": 48,
        "channel_count": len(channels),
        "draft_ready_channel_count": sum(bool(row["topics"]) for row in channels),
        "waiting_sample_channel_count": sum(not row["topics"] for row in channels),
        "boundaries": [
            "週日資料是24/48小時選題快照，不是台股同日收盤稿。",
            "所有文稿均為人工審閱草稿，不是投資建議。",
            "未取得暗池打印或完整期權鏈時，不推論機構方向。",
            "三個無文稿樣本頻道不生成仿寫稿。",
        ],
        "channels": channels,
    }
    return workbench


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the first-ten BEN channel workbench.")
    parser.add_argument(
        "--site-data",
        default=str(ROOT / "sites" / "ben-content-studio" / "data.json"),
    )
    parser.add_argument(
        "--style-packs",
        default=str(
            ROOT
            / "research"
            / "ben_radar_first10_style_packs"
            / "style_packs_v0.1.json"
        ),
    )
    parser.add_argument(
        "--weekend-snapshot",
        default=str(
            ROOT
            / "outputs"
            / "ben_weekend_crawl"
            / "2026-08-23"
            / "latest.json"
        ),
    )
    parser.add_argument(
        "--close-talk-editorial",
        default=str(
            ROOT
            / "outputs"
            / "ben_channel_daily"
            / "2026-08-21"
            / "close_talk_editorial.json"
        ),
    )
    parser.add_argument(
        "--output",
        default=str(
            ROOT
            / "outputs"
            / "ben_first10_editorial"
            / "2026-08-23"
            / "first10_editorial.json"
        ),
    )
    args = parser.parse_args()

    site_path = Path(args.site_data)
    site_data = _read_json(site_path)
    workbench = build_payload(
        site_data=site_data,
        style_payload=_read_json(Path(args.style_packs)),
        weekend_payload=_read_json(Path(args.weekend_snapshot)),
        editorial=_read_json(Path(args.close_talk_editorial)),
    )
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(workbench, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    site_data["first_ten_workbench"] = workbench
    site_path.write_text(
        json.dumps(site_data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "status": "PASS",
                "channel_count": workbench["channel_count"],
                "draft_ready_channel_count": workbench["draft_ready_channel_count"],
                "waiting_sample_channel_count": workbench["waiting_sample_channel_count"],
                "output": str(output_path.resolve()),
                "site_data": str(site_path.resolve()),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
