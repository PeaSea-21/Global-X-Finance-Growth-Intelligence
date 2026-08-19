const FEEDBACK_KEY = "ben-channel-review.feedback.v1";
let activePayload = null;
let feedback = loadFeedback();

const fmt = (value, digits = 0) => {
  if (value === null || value === undefined || Number.isNaN(Number(value))) return "UNKNOWN";
  return new Intl.NumberFormat("zh-TW", { maximumFractionDigits: digits }).format(Number(value));
};

const pct = (value) => {
  if (value === null || value === undefined) return "UNKNOWN";
  const number = Number(value);
  return `${number >= 0 ? "+" : ""}${number.toFixed(2)}%`;
};

const sourceLabels = {
  TWSE_EOD: ["上市收盤資料", "本版有完整交易日資料"],
  TPEX_EOD: ["上櫃收盤資料", "本版有完整交易日資料"],
  MOPS: ["公司重大訊息", "目前只有有限記錄，還不夠解釋全部異動"],
  NEWS: ["財經新聞", "本次有歷史記錄，正式授權與覆蓋仍待補"],
  X: ["X 公開內容", "本班次未啟用，不影響官方行情與新聞結果"],
  INDUSTRY_MAPPING: ["官方產業分類", "只能幫忙分組，不能證明供應鏈與共同原因"],
};

const channelNotes = {
  SIGNAL_HEAVY: "目前實際做的是價量異動，不是真正的法人或 ETF 資金流。",
  EVENT_HEAVY: "有公司事件就優先使用；找不到原因時，只能保留為待查候選。",
  CROSS_ENTITY: "同產業一起異動只用來找線索，不代表它們有共同訂單或共同催化劑。",
};

function loadFeedback() {
  try { return JSON.parse(localStorage.getItem(FEEDBACK_KEY) || "{}"); }
  catch { return {}; }
}

function saveFeedback(feedback) {
  localStorage.setItem(FEEDBACK_KEY, JSON.stringify(feedback));
}

function updateFeedbackSummary() {
  document.querySelector("#feedback-count").textContent = String(Object.keys(feedback).length);
}

function csvCell(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function downloadFeedback() {
  if (!activePayload) return;
  const rows = [["channel", "rank", "candidate_id", "title", "feedback"]];
  activePayload.briefs.forEach((brief) => {
    brief.assignments.slice(0, brief.target_count).forEach((item) => {
      const feedbackId = `${brief.channel_id}:${item.candidate_id}`;
      rows.push([brief.channel_name, item.candidate_rank, item.candidate_id, item.title, feedback[feedbackId] || ""]);
    });
  });
  const content = `\uFEFF${rows.map((row) => row.map(csvCell).join(",")).join("\r\n")}`;
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }));
  const link = document.createElement("a");
  link.href = url;
  link.download = `BEN_Radar_三頻道回饋_${activePayload.market_session_date}.csv`;
  link.click();
  URL.revokeObjectURL(url);
}

function list(target, values, emptyText = "無") {
  target.replaceChildren();
  const rows = values && values.length ? values : [emptyText];
  rows.forEach((value) => {
    const item = document.createElement("li");
    item.textContent = value;
    target.append(item);
  });
}

function paragraphs(target, values) {
  target.replaceChildren();
  (values || []).forEach((value) => {
    const item = document.createElement("p");
    item.textContent = value;
    target.append(item);
  });
}

function stockRow(stock) {
  const row = document.createElement("div");
  row.className = "stock-row";
  const fields = [
    ["收盤", fmt(stock.close, 2)],
    ["漲跌", pct(stock.change_pct)],
    ["成交量", fmt(stock.current_volume)],
    ["RVOL", `${fmt(stock.volume_ratio, 2)} 倍`],
  ];
  row.innerHTML = `<div class="stock-name"><strong></strong><span></span></div>${fields.map(() => '<div class="stock-metric"><span></span><strong></strong></div>').join("")}`;
  row.querySelector(".stock-name strong").textContent = stock.name;
  row.querySelector(".stock-name span").textContent = stock.security_id;
  row.querySelectorAll(".stock-metric").forEach((element, index) => {
    element.querySelector("span").textContent = fields[index][0];
    element.querySelector("strong").textContent = fields[index][1];
  });
  return row;
}

function topicCard(item, channelId) {
  const card = document.querySelector("#topic-template").content.firstElementChild.cloneNode(true);
  card.dataset.candidateId = item.candidate_id;
  card.querySelector(".topic-rank").textContent = String(item.candidate_rank).padStart(2, "0");
  card.querySelector(".topic-meta").textContent = `${item.candidate_type} · ${item.freshness_state}`;
  card.querySelector("h3").textContent = item.title;
  card.querySelector(".research-state").textContent = item.unknowns?.length ? "待補原因" : "可進一步討論";
  paragraphs(card.querySelector(".why-now"), item.why_now);
  paragraphs(card.querySelector(".why-channel"), item.why_channel);

  const stocks = card.querySelector(".stock-list");
  (item.stock_details || []).forEach((stock) => stocks.append(stockRow(stock)));
  if (!item.stock_details?.length) stocks.remove();

  list(card.querySelector(".facts"), item.facts, "目前沒有已確認欄位");
  list(card.querySelector(".unknowns"), item.unknowns, "無");

  const evidenceLinks = card.querySelector(".evidence-links");
  [...(item.evidence || []), ...(item.opinion_evidence || [])].forEach((evidence) => {
    const link = document.createElement("a");
    link.href = evidence.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    const title = document.createElement("b");
    title.textContent = evidence.evidence_class || "EVIDENCE";
    const source = document.createElement("span");
    source.textContent = `${evidence.source_id || "UNKNOWN"} · ${evidence.trade_date || evidence.published_at || evidence.announced_at || evidence.observed_at || "日期未知"}`;
    link.append(title, source);
    evidenceLinks.append(link);
  });

  const buttons = card.querySelectorAll("[data-feedback]");
  const feedbackId = `${channelId}:${item.candidate_id}`;
  const sync = () => buttons.forEach((button) => button.classList.toggle("active", feedback[feedbackId] === button.dataset.feedback));
  buttons.forEach((button) => button.addEventListener("click", () => {
    feedback[feedbackId] = feedback[feedbackId] === button.dataset.feedback ? null : button.dataset.feedback;
    if (!feedback[feedbackId]) delete feedback[feedbackId];
    saveFeedback(feedback);
    updateFeedbackSummary();
    sync();
  }));
  sync();
  return card;
}

function render(payload) {
  activePayload = payload;
  const isReplay = Boolean(payload.replay_mode);
  document.querySelector("#run-kicker").textContent = isReplay
    ? "TAIWAN POST-CLOSE · HISTORICAL REPLAY"
    : "TAIWAN POST-CLOSE · CURRENT SESSION";
  document.querySelector("#run-state-title").textContent = isReplay
    ? "這是歷史回放，不是今天即時結果。"
    : "這是當日收盤資料，不是盤中即時行情。";
  document.querySelector("#replay-copy").textContent = isReplay
    ? `頁面展示 ${payload.market_session_date} 收盤回放；資料截至 ${payload.data_as_of}。`
    : `頁面展示 ${payload.market_session_date} 收盤結果；資料截至 ${payload.data_as_of}，未確認的上漲原因仍會標示待查。`;
  document.querySelector("#results-title").textContent = isReplay
    ? "三頻道歷史試跑結果"
    : "三頻道今日收盤結果";
  const totalTopics = payload.briefs.reduce(
    (sum, brief) => sum + Math.min(brief.target_count, brief.assignments.length),
    0,
  );
  document.querySelector("#feedback-total").textContent = String(totalTopics);
  const summary = [
    ["資料日期", payload.market_session_date],
    ["試點範圍", `${payload.briefs.length} / 20 頻道`],
    ["本版候選", `${totalTopics} 個`],
    ["排序", "規則排序，不是 AI"],
  ];
  const runSummary = document.querySelector("#run-summary");
  summary.forEach(([label, value]) => {
    const item = document.createElement("div");
    item.innerHTML = "<dt></dt><dd></dd>";
    item.querySelector("dt").textContent = label;
    item.querySelector("dd").textContent = value;
    runSummary.append(item);
  });

  const tabs = document.querySelector("#channel-tabs");
  const panels = document.querySelector("#channel-panels");
  payload.briefs.forEach((brief, index) => {
    const tab = document.createElement("button");
    tab.type = "button";
    tab.id = `tab-${brief.channel_id}`;
    tab.setAttribute("role", "tab");
    tab.setAttribute("aria-selected", index === 0 ? "true" : "false");
    tab.setAttribute("aria-controls", `panel-${brief.channel_id}`);
    tab.innerHTML = "<strong></strong><span></span><em></em>";
    tab.querySelector("strong").textContent = brief.channel_name;
    tab.querySelector("span").textContent = brief.channel_type;
    tab.querySelector("em").textContent = String(Math.min(brief.target_count, brief.assignments.length));
    tabs.append(tab);

    const panel = document.createElement("section");
    panel.id = `panel-${brief.channel_id}`;
    panel.className = "channel-panel";
    panel.setAttribute("role", "tabpanel");
    panel.setAttribute("aria-labelledby", tab.id);
    panel.hidden = index !== 0;
    panel.innerHTML = '<header class="channel-intro"><div><h3></h3><p></p></div><div class="channel-warning"></div></header><div class="topic-list"></div>';
    panel.querySelector("h3").textContent = brief.channel_name;
    panel.querySelector(".channel-intro p").textContent = brief.summary;
    panel.querySelector(".channel-warning").textContent = channelNotes[brief.channel_type] || brief.fixed_boundary;
    const topicList = panel.querySelector(".topic-list");
    brief.assignments.slice(0, brief.target_count).forEach((item) => topicList.append(topicCard(item, brief.channel_id)));
    panels.append(panel);

    tab.addEventListener("click", () => {
      tabs.querySelectorAll("[role=tab]").forEach((item) => item.setAttribute("aria-selected", item === tab ? "true" : "false"));
      panels.querySelectorAll("[role=tabpanel]").forEach((item) => { item.hidden = item !== panel; });
    });
  });

  const sourceTable = document.querySelector("#source-table");
  payload.source_readiness.forEach((source) => {
    const [label, note] = sourceLabels[source.source] || [source.source, "本版有記錄"];
    const item = document.createElement("article");
    item.className = "source-item";
    item.innerHTML = "<span></span><strong></strong><p></p>";
    item.querySelector("span").textContent = source.source;
    item.querySelector("strong").textContent = label;
    item.querySelector("p").textContent = `${note}（${fmt(source.record_count)} 筆）`;
    sourceTable.append(item);
  });
  updateFeedbackSummary();
}

document.querySelector("#download-feedback").addEventListener("click", downloadFeedback);
document.querySelector("#clear-feedback").addEventListener("click", () => {
  feedback = {};
  saveFeedback(feedback);
  document.querySelectorAll("[data-feedback]").forEach((button) => button.classList.remove("active"));
  updateFeedbackSummary();
});

fetch("brief.json", { cache: "no-store" })
  .then((response) => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then(render)
  .catch((error) => {
    document.querySelector("#results").insertAdjacentHTML("beforeend", `<p class="load-error">資料讀取失敗：${String(error.message || error)}</p>`);
  });
