const BRIEF_URL = "../ben-channel-review/brief.json";

const CHANNEL_META = {
  "資金雷達": {
    order: 1,
    accent: "#087c72",
    kicker: "MONEY MOVEMENT",
    description: "從異常成交與價格變化找線索，再追問資金為什麼集中到這裡。",
    status: "今日正式 Brief",
  },
  "個股顯微鏡": {
    order: 2,
    accent: "#2e6094",
    kicker: "COMPANY DEEP DIVE",
    description: "把公司公告、營運事件與收盤反應放在一起，先確認事實再談影響。",
    status: "今日正式 Brief",
  },
  "產業透視鏡": {
    order: 3,
    accent: "#9a6810",
    kicker: "SECTOR LOGIC",
    description: "找同產業多家公司同步異動，拆開共通主線與尚未證實的因果。",
    status: "今日正式 Brief",
  },
  "收盤夜話": {
    order: 4,
    accent: "#b83a35",
    kicker: "MARKET STORY",
    description: "用一兩個主角講清楚今天盤面的情緒、轉折與明日觀察。",
    status: "試編預覽 · 資料缺口已標示",
  },
  "權值旗艦": {
    order: 5,
    accent: "#66538a",
    kicker: "INDEX LEADERS",
    description: "只看真正能牽動大盤的權值股，分清領漲、拖累與成交焦點。",
    status: "試編預覽 · 不宣稱指數貢獻點",
  },
};

const WEIGHT_TOPICS = [
  {
    candidate_rank: 1,
    candidate_type: "WEIGHTED_EOD_PREVIEW",
    editorial_status: "PREVIEW_FROM_OFFICIAL_EOD",
    title: "聯發科收跌145元、成交481億元：權值電子今天的壓力中心在哪？",
    why_now: ["聯發科收在3,700元，較前一日下跌145元，估算跌幅約3.77%；今日成交金額約481.32億元。"],
    why_channel: ["聯發科是權值電子核心公司，適合用來觀察大型科技股內部強弱。"],
    facts: ["收盤3,700元", "漲跌-145元", "成交量12,864,952股", "成交金額48,131,667,840元"],
    unknowns: ["未接入正式指數權重，因此不計算聯發科拖累指數點數。", "下跌催化劑仍需公告或多方新聞確認。"],
    evidence: [{ source_id: "TWSE", evidence_class: "OFFICIAL_EOD", url: "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260820&type=ALLBUT0999&response=json" }],
    opinion_evidence: [],
    security_ids: ["TWSE:2454"],
    stock_details: [{ name: "聯發科", security_id: "TWSE:2454", close: 3700, change_pct: -3.77, current_volume: 12864952 }],
  },
  {
    candidate_rank: 2,
    candidate_type: "WEIGHTED_EOD_PREVIEW",
    editorial_status: "PREVIEW_FROM_OFFICIAL_EOD",
    title: "台積電收2375元逆勢上漲：權值核心為什麼沒有和聯發科同方向？",
    why_now: ["台積電收在2,375元、上漲25元，估算漲幅約1.06%；與聯發科形成明顯分歧。"],
    why_channel: ["用權值核心的分歧理解盤面，比單看加權指數漲跌更接近本頻道定位。"],
    facts: ["收盤2,375元", "漲跌+25元", "成交量15,873,737股", "成交金額37,530,483,650元"],
    unknowns: ["尚未接入準確指數貢獻點。", "不能只由收盤價推導外資意圖。"],
    evidence: [{ source_id: "TWSE", evidence_class: "OFFICIAL_EOD", url: "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260820&type=ALLBUT0999&response=json" }],
    opinion_evidence: [],
    security_ids: ["TWSE:2330"],
    stock_details: [{ name: "台積電", security_id: "TWSE:2330", close: 2375, change_pct: 1.06, current_volume: 15873737 }],
  },
  {
    candidate_rank: 3,
    candidate_type: "WEIGHTED_EOD_PREVIEW",
    editorial_status: "PREVIEW_FROM_OFFICIAL_EOD",
    title: "鴻海量增收紅但漲幅有限：AI權值股今天是接棒還是休息？",
    why_now: ["鴻海收在246.5元、上漲1.5元，估算漲幅約0.61%，成交量約2,634萬股。"],
    why_channel: ["鴻海是AI硬體權值觀察點，但僅憑價量不能宣稱資金已全面轉向。"],
    facts: ["收盤246.5元", "漲跌+1.5元", "成交量26,344,428股", "成交金額6,492,076,639元"],
    unknowns: ["AI訂單與今日股價的直接關係尚未確認。", "法人買賣超未納入本次預覽。"],
    evidence: [{ source_id: "TWSE", evidence_class: "OFFICIAL_EOD", url: "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260820&type=ALLBUT0999&response=json" }],
    opinion_evidence: [],
    security_ids: ["TWSE:2317"],
    stock_details: [{ name: "鴻海", security_id: "TWSE:2317", close: 246.5, change_pct: 0.61, current_volume: 26344428 }],
  },
  {
    candidate_rank: 4,
    candidate_type: "WEIGHTED_COMPARISON_PREVIEW",
    editorial_status: "PREVIEW_DERIVED_COMPARISON",
    title: "台積電漲、聯發科跌：權值雙核心不同調，盤面正在交易哪條主線？",
    why_now: ["同一交易日台積電估算上漲1.06%，聯發科估算下跌3.77%，方向與幅度明顯不同。"],
    why_channel: ["權值股內部分歧本身就是盤面結構題，但原因必須再由新聞與公告核驗。"],
    facts: ["台積電收2,375元、+25元", "聯發科收3,700元、-145元"],
    unknowns: ["尚未確認造成分歧的共同或個別催化劑。", "未接入指數權重，不能換算對大盤的實際點數影響。"],
    evidence: [{ source_id: "TWSE", evidence_class: "OFFICIAL_EOD", url: "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260820&type=ALLBUT0999&response=json" }],
    opinion_evidence: [],
    security_ids: ["TWSE:2330", "TWSE:2454"],
    stock_details: [],
  },
  {
    candidate_rank: 5,
    candidate_type: "WEIGHTED_LIQUIDITY_PREVIEW",
    editorial_status: "PREVIEW_DERIVED_COMPARISON",
    title: "聯發科成交金額高於台積電：今天權值股的注意力為何集中在跌勢？",
    why_now: ["聯發科今日成交金額約481.32億元，高於台積電約375.30億元；注意力集中不等於買盤流入。"],
    why_channel: ["用成交焦點補充價格方向，但不把成交金額誤寫成淨流入。"],
    facts: ["聯發科成交金額48,131,667,840元", "台積電成交金額37,530,483,650元"],
    unknowns: ["買賣方向與法人身分未由成交金額本身確認。", "期貨與外資部位尚未接入。"],
    evidence: [{ source_id: "TWSE", evidence_class: "OFFICIAL_EOD", url: "https://www.twse.com.tw/rwd/zh/afterTrading/MI_INDEX?date=20260820&type=ALLBUT0999&response=json" }],
    opinion_evidence: [],
    security_ids: ["TWSE:2454", "TWSE:2330"],
    stock_details: [],
  },
];

let channels = [];
let activeChannel = null;
let activeTopic = null;

const $ = (selector) => document.querySelector(selector);
const list = (value) => Array.isArray(value) ? value : [];
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));

function editorialTitle(channelName, item) {
  if (channelName === "資金雷達") {
    const stock = list(item.stock_details)[0];
    if (stock?.name && stock?.volume_ratio) return `${stock.name}爆出${Number(stock.volume_ratio).toFixed(1)}倍量！今天資金為什麼突然集中？`;
  }
  if (channelName === "個股顯微鏡") {
    return `${item.title.replace("公告：", "：")}，這次真正要看的營運訊號是什麼？`;
  }
  if (channelName === "產業透視鏡") {
    return `${item.title.replace("出现", "同時出現")}：共同主線成立了嗎？`;
  }
  return item.title;
}

function topicLabel(item) {
  if (item.candidate_type?.includes("DISCLOSURE")) return "官方事件";
  if (item.candidate_type?.includes("NEWS")) return "新聞事件";
  if (item.candidate_type?.includes("X_EVENT")) return "X 線索";
  if (item.candidate_type?.includes("CROSS_ENTITY")) return "產業共振";
  if (item.candidate_type?.includes("WEIGHTED")) return "權值觀察";
  return "價量線索";
}

function allEvidence(item) {
  return [...list(item.evidence), ...list(item.opinion_evidence)];
}

function whyText(item) {
  return list(item.why_now)[0] || list(item.facts)[0] || "今日候選已通過時效與 Evidence 檢查。";
}

function draftFor(channelName, item) {
  const facts = list(item.facts).slice(0, 4).join("；");
  const unknown = list(item.unknowns)[0] || "後續仍需追蹤新的官方資料。";
  const stocks = list(item.stock_details).map((row) => row.name).filter(Boolean).join("、") || list(item.security_ids).join("、");
  const title = editorialTitle(channelName, item);
  const openings = {
    "資金雷達": `各位朋友，今天資金雷達先看一個盤面突然放大的訊號：${title}\n\n先別急著把爆量當成利多。今天可以確認的數據是：${facts}。這代表市場注意力確實集中，但成交放大不等於法人淨流入，更不能直接推導後面一定續漲。\n\n現在真正要查的是兩件事。第一，這次異動有沒有公司公告、產業消息或多個獨立來源支持；第二，明天量能能不能延續，而不是只出現一天。${unknown}\n\n所以今天的結論不是追價，而是把${stocks || "這個標的"}放進觀察名單：先確認催化劑，再判斷這是主線啟動，還是一次性的成交異常。`,
    "個股顯微鏡": `今天個股顯微鏡把鏡頭對準${stocks || "這家公司"}。表面上看到的是一則公告，但真正重要的是：這件事會不會改變公司的營運節奏？\n\n目前已確認的事實是：${facts}。公告本身可以核驗，但公告與股價、營收或獲利之間的因果不能直接畫等號。\n\n接下來要沿著三條線看：收入是否改變、毛利率與現金流是否跟上，以及公司後續說法能不能被正式財報驗證。${unknown}\n\n這一題值得做，不是因為公告標題很大，而是它提供了一個可以持續追蹤公司體質的時間點。`,
    "產業透視鏡": `今天產業透視鏡不只看一家公司，而是看一整組股票為什麼同時出現異動。${title}\n\n可以確認的盤面事實是：${facts}。多家公司同時異動，代表這個產業值得往下查，但它只能證明共現，不能自動證明大家共享同一張訂單或同一個催化劑。\n\n下一步要拆成三層：上游需求有沒有變、公司營收與庫存是否同步，以及領漲公司和跟漲公司差在哪裡。${unknown}\n\n真正有用的產業題，不是列出一串股票，而是找出誰有基本面、誰只有題材，還有這條主線能不能延續。`,
    "收盤夜話": `各位朋友，今天這一盤最值得聊的，不是一張漲跌榜，而是盤面裡出現的明顯分歧。${title}\n\n今天可以先確認：${facts}。有人看到價格就急著下結論，但收盤夜話更想問，這個變化到底是整體主線，還是只有少數股票在表演？\n\n我們把盤面拆開看：先看權值股方向，再看產業有沒有多家公司呼應，最後回到成交量與公告。${unknown}\n\n明天最重要的觀察點，是今天的主角能不能延續量能，以及同族群是否繼續擴散。只要這兩件事沒有同時出現，就先把它當成需要追蹤的盤面線索。`,
    "權值旗艦": `歡迎回到權值旗艦。今天看大盤，不能只看最後一個指數數字，因為核心權值股走出了不同方向。${title}\n\n先看官方收盤資料：${facts}。這些數字能告訴我們誰強、誰弱、成交焦點在哪裡，但目前沒有正式權重資料，不能把它誇大成精確的指數貢獻點。\n\n接下來的判斷分三層：權值股能不能站回關鍵位置、成交焦點是否延續，以及新聞或公告有沒有補上催化劑。${unknown}\n\n今天的結論是條件判斷，不是買賣建議。權值股若繼續分歧，大盤就容易震盪；只有核心公司重新同向，盤面的方向才會更清楚。`,
  };
  return openings[channelName] || `${title}\n\n${facts}\n\n${unknown}`;
}

function buildCloseTalk(briefs) {
  const industry = briefs.find((row) => row.channel_name === "產業透視鏡")?.assignments || [];
  const signals = briefs.find((row) => row.channel_name === "資金雷達")?.assignments || [];
  const events = briefs.find((row) => row.channel_name === "個股顯微鏡")?.assignments || [];
  const picks = [industry[0], WEIGHT_TOPICS[3], signals[0], industry[2], events[0]].filter(Boolean);
  return picks.map((item, index) => ({
    ...item,
    candidate_rank: index + 1,
    candidate_type: `CLOSE_TALK_${item.candidate_type}`,
    editorial_status: "EDITORIAL_PREVIEW",
    title: [
      `今天盤面主線不是單一飆股：${item.title}`,
      item.title,
      `${item.title}，收盤後真正要查的是什麼？`,
      `強勢族群開始擴散？${item.title}`,
      `${item.title.replace("公告：", "：")}，明天盤面要留意什麼？`,
    ][index],
    why_channel: ["從今日正式 Brief 中挑出能代表盤面情緒與轉折的主角；本頻道仍缺三大法人、融資券與當沖比完整資料。"],
  }));
}

function normalizeChannels(payload) {
  const briefs = list(payload.briefs);
  const core = briefs.map((brief) => ({
    name: brief.channel_name,
    meta: CHANNEL_META[brief.channel_name],
    topics: list(brief.assignments).slice(0, 5).map((item) => ({ ...item, title: editorialTitle(brief.channel_name, item) })),
    official: true,
  }));
  core.push({ name: "收盤夜話", meta: CHANNEL_META["收盤夜話"], topics: buildCloseTalk(briefs), official: false });
  core.push({ name: "權值旗艦", meta: CHANNEL_META["權值旗艦"], topics: WEIGHT_TOPICS, official: false });
  return core.sort((a, b) => a.meta.order - b.meta.order);
}

function renderOverview() {
  const container = $("#channel-overview");
  container.innerHTML = "";
  channels.forEach((channel) => {
    const fragment = $("#channel-template").content.cloneNode(true);
    const button = fragment.querySelector("button");
    button.style.setProperty("--accent", channel.meta.accent);
    fragment.querySelector(".channel-number").textContent = `0${channel.meta.order}`;
    fragment.querySelector(".channel-name").textContent = channel.name;
    fragment.querySelector(".channel-description").textContent = channel.meta.description;
    fragment.querySelector(".channel-foot b").textContent = `${channel.topics.length} 個今日選題`;
    button.addEventListener("click", () => showChannel(channel));
    container.appendChild(fragment);
  });
}

function showChannel(channel) {
  activeChannel = channel;
  $("#channel-overview").hidden = true;
  $("#channel-detail").hidden = false;
  $("#page-title").textContent = "今日頻道選題";
  $("#page-summary").textContent = "先看標題，再用理由、Evidence 和頻道草稿完成判斷。";
  $("#detail-kicker").textContent = channel.meta.kicker;
  $("#detail-title").textContent = channel.name;
  $("#detail-summary").textContent = channel.meta.description;
  $("#detail-status").textContent = channel.official
    ? "今日正式 Brief：通過日期、Evidence 與市場標的檢查。文稿為本頁新增的頻道草稿預覽。"
    : channel.meta.status;
  const listRoot = $("#topic-list");
  listRoot.innerHTML = "";
  channel.topics.forEach((topic, index) => {
    const fragment = $("#topic-template").content.cloneNode(true);
    const row = fragment.querySelector(".topic-row");
    row.style.setProperty("--accent", channel.meta.accent);
    fragment.querySelector(".topic-rank").textContent = String(index + 1).padStart(2, "0");
    fragment.querySelector(".topic-meta").textContent = `${topicLabel(topic)} · ${topic.editorial_status || "NEEDS_REVIEW"}`;
    fragment.querySelector("h3").textContent = topic.title;
    fragment.querySelector("p").textContent = whyText(topic);
    fragment.querySelector(".topic-open").addEventListener("click", () => openTopic(channel, topic));
    listRoot.appendChild(fragment);
  });
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function evidenceLinks(item) {
  const rows = allEvidence(item);
  if (!rows.length) return '<span>暫無可點擊 Evidence</span>';
  return rows.map((row, index) => {
    const label = `${row.evidence_class || row.epistemic_status || "Evidence"} · ${row.source_id || `來源 ${index + 1}`}`;
    return row.url
      ? `<a href="${escapeHtml(row.url)}" target="_blank" rel="noreferrer">${escapeHtml(label)} ↗</a>`
      : `<span>${escapeHtml(label)}</span>`;
  }).join("");
}

function openTopic(channel, topic) {
  activeTopic = topic;
  const draft = draftFor(channel.name, topic);
  $("#dialog-content").innerHTML = `
    <div class="dialog-inner">
      <span class="topic-type">${escapeHtml(channel.name)} · ${escapeHtml(topicLabel(topic))}</span>
      <h2>${escapeHtml(topic.title)}</h2>
      <div class="reason-grid">
        <section class="reason-block"><h3>為什麼是今天</h3><ul>${list(topic.why_now).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || `<li>${escapeHtml(whyText(topic))}</li>`}</ul></section>
        <section class="reason-block"><h3>為什麼適合這個頻道</h3><ul>${list(topic.why_channel).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || `<li>${escapeHtml(channel.meta.description)}</li>`}</ul></section>
        <section class="reason-block"><h3>已確認事實</h3><ul>${list(topic.facts).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || "<li>請從原始 Evidence 核對。</li>"}</ul></section>
        <section class="reason-block"><h3>還不能下的結論</h3><ul>${list(topic.unknowns).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || "<li>事件與股價之間的因果仍需確認。</li>"}</ul></section>
      </div>
      <section class="source-block"><h3>點擊核對來源</h3><div class="source-links">${evidenceLinks(topic)}</div></section>
      <div class="draft-actions">
        <button class="draft-toggle" type="button">展開頻道草稿</button>
        <button class="copy-button" type="button">複製草稿</button>
      </div>
      <section class="draft-block" hidden>
        <p class="draft-note">頻道草稿預覽 · 由今日 Evidence 與單篇文字稿結構生成 · 上線前需人工核對</p>
        <h3>${escapeHtml(topic.title)}</h3>
        <div class="draft-copy">${escapeHtml(draft)}</div>
      </section>
    </div>`;
  const draftBlock = $(".draft-block");
  $(".draft-toggle").addEventListener("click", (event) => {
    draftBlock.hidden = !draftBlock.hidden;
    event.currentTarget.textContent = draftBlock.hidden ? "展開頻道草稿" : "收起頻道草稿";
  });
  $(".copy-button").addEventListener("click", async (event) => {
    const button = event.currentTarget;
    try {
      await navigator.clipboard.writeText(draft);
      button.textContent = "已複製";
    } catch {
      button.textContent = "複製失敗";
    }
    setTimeout(() => { button.textContent = "複製草稿"; }, 1200);
  });
  $("#topic-dialog").showModal();
}

function showOverview() {
  activeChannel = null;
  $("#channel-detail").hidden = true;
  $("#channel-overview").hidden = false;
  $("#page-title").textContent = "今天先做哪個頻道？";
  $("#page-summary").textContent = "五個頻道各自選題，不把同一張漲幅榜換名字重複使用。";
}

async function boot() {
  const response = await fetch(BRIEF_URL, { cache: "no-store" });
  if (!response.ok) throw new Error(`Brief HTTP ${response.status}`);
  const payload = await response.json();
  channels = normalizeChannels(payload);
  $("#session-date").textContent = `${payload.market_session_date} 收盤資料`;
  $("#generated-time").textContent = new Intl.DateTimeFormat("zh-TW", { hour: "2-digit", minute: "2-digit", hour12: false, timeZone: "Asia/Taipei" }).format(new Date(payload.generated_at));
  renderOverview();
}

$("#back-button").addEventListener("click", showOverview);
$(".brand").addEventListener("click", (event) => { event.preventDefault(); showOverview(); });
$("#dialog-close").addEventListener("click", () => $("#topic-dialog").close());
$("#topic-dialog").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });

boot().catch((error) => {
  $("#channel-overview").innerHTML = `<p>今日 Brief 讀取失敗：${escapeHtml(error.message)}</p>`;
});
