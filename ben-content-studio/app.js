const DATA_URL = "data.json";

const CHANNEL_META = {
  "個股顯微鏡": { accent: "#2e6094", kicker: "TAIWAN SINGLE STOCK" },
  "收盤夜話": { accent: "#b83a35", kicker: "TAIWAN POST-CLOSE" },
  "產業透視鏡": { accent: "#087c72", kicker: "TAIWAN INDUSTRY" },
  "權值旗艦": { accent: "#9a6810", kicker: "TAIWAN WEIGHTED STOCKS" },
  "資金雷達": { accent: "#53733f", kicker: "TAIWAN CAPITAL FLOW" },
  "那指火箭": { accent: "#6b4f9e", kicker: "NASDAQ 100" },
  "板塊輪動儀": { accent: "#9b4f65", kicker: "SECTOR ROTATION" },
  "暗池雷達": { accent: "#31536b", kicker: "DERIVATIVES EVIDENCE" },
  "期權守門人": { accent: "#8a5b2d", kicker: "OPTIONS RISK" },
  "財報獵人": { accent: "#4c6268", kicker: "EARNINGS REVIEW" },
  "宏觀天秤": { accent: "#315f78", kicker: "GLOBAL MACRO" },
  "全球資金地圖": { accent: "#6b5946", kicker: "GLOBAL CAPITAL FLOW" },
  "地緣炸藥庫": { accent: "#a13e37", kicker: "GEOPOLITICAL RISK" },
  "週期航海家": { accent: "#24756b", kicker: "COMMODITY CYCLE" },
  "鏈上顯微鏡": { accent: "#7252a0", kicker: "ONCHAIN DATA" },
  "中概風向球": { accent: "#a04c69", kicker: "CHINA ADRS" },
  "財商拆彈組": { accent: "#43845a", kicker: "FINANCIAL LITERACY" },
  "半導體駭客": { accent: "#3d5f98", kicker: "SEMICONDUCTOR TECH" },
  "華爾街溫度計": { accent: "#9b641c", kicker: "MARKET SENTIMENT" },
  "定投實驗室": { accent: "#537078", kicker: "DCA RESEARCH" },
};

let channels = [];
let activeChannel = null;
let activeTopic = null;

const $ = (selector) => document.querySelector(selector);
const list = (value) => Array.isArray(value) ? value : [];
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
const characterCount = (value) => [...String(value ?? "").replace(/\s/g, "")].length;

function topicLabel(item) {
  if (item.candidate_type?.includes("CLOSE_TALK_EDITORIAL")) return "收盤夜話選題";
  if (item.script_generation_method === "STYLE_PACK_EVIDENCE_TEMPLATE_V1") return "跨頻道熱點 · 本頻道完整稿";
  if (item.candidate_type?.includes("DISCLOSURE")) return "官方事件";
  if (item.candidate_type?.includes("NEWS")) return "新聞事件";
  if (item.candidate_type?.includes("X_EVENT")) return "X 線索";
  if (item.candidate_type?.includes("CROSS_ENTITY")) return "產業共振";
  if (item.candidate_type?.includes("WEIGHTED")) return "權值觀察";
  if (item.candidate_type?.includes("CHANNEL_EDITORIAL")) return "頻道暫定稿";
  return "價量線索";
}

function allEvidence(item) {
  return [...list(item.evidence), ...list(item.opinion_evidence)];
}

function whyText(item) {
  return list(item.why_now)[0] || list(item.facts)[0] || "今日候選已通過時效與 Evidence 檢查。";
}

function normalizeChannels(payload) {
  const workbench = payload.channel_workbench || payload.first_ten_workbench || {};
  return list(workbench.channels).filter((channel) => channel.content_status !== "WAITING_FOR_TRANSCRIPT_SAMPLES").map((channel) => ({
    ...channel,
    name: channel.channel_name,
    meta: {
      ...(CHANNEL_META[channel.channel_name] || {}),
      order: channel.channel_order,
      description: channel.profile_promise,
    },
    topics: list(channel.topics),
  }));
}

function sourceRow(payload, source) {
  return list(payload.source_readiness).find((row) => row.source === source) || {};
}

function sourceLabel(payload, source) {
  const row = sourceRow(payload, source);
  const count = Number.isFinite(Number(row.record_count)) ? ` · ${Number(row.record_count).toLocaleString("zh-TW")}` : "";
  return `${row.status || "未知"}${count}`;
}

function taipeiDate() {
  return new Intl.DateTimeFormat("en-CA", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    timeZone: "Asia/Taipei",
  }).format(new Date());
}

function applyPayload(payload) {
  const workbench = payload.channel_workbench || payload.first_ten_workbench;
  if (!workbench || Number(workbench.channel_count) !== 20) {
    throw new Error("20頻道審計資料尚未完整發布");
  }
  channels = normalizeChannels(payload);
  if (channels.length !== 11 || channels.some((channel) => channel.topics.length !== 5)) {
    throw new Error("已有樣本頻道尚未形成五題審稿面");
  }
  if (channels.some((channel) => channel.topics.some((topic) => !topic.script_text))) {
    throw new Error("已有樣本頻道仍有未完成文稿");
  }
  const snapshotDate = workbench.source_snapshot_date;
  const fullScriptCount = channels.reduce((total, channel) => total + channel.topics.filter((topic) => topic.script_text).length, 0);
  $("#session-date").textContent = `${snapshotDate} 選題快照`;
  $("#generated-time").textContent = snapshotDate;
  $("#ranking-method").textContent = `${channels.length} 個已有樣本`;
  $("#x-count").textContent = `${fullScriptCount} 篇`;
  $("#source-twse").textContent = sourceLabel(payload, "TWSE_EOD");
  $("#source-tpex").textContent = sourceLabel(payload, "TPEX_EOD");
  $("#source-mops").textContent = sourceLabel(payload, "MOPS");
  $("#source-news").textContent = `${workbench.news_source_success_count || 9}/${workbench.news_source_count || 9} · 官方${workbench.official_source_count || 0}`;
  $("#source-x").textContent = sourceLabel(payload, "X");
  $("#source-youtube").textContent = `${workbench.transcript_sample_count || 19}篇口吻樣本`;
  const refreshState = $("#refresh-state");
  refreshState.className = "refresh-state";
  refreshState.textContent = `已載入 ${snapshotDate} 選題快照；收盤夜話使用最近交易日 ${workbench.last_market_session_date}`;
  if ($("#topic-dialog").open) $("#topic-dialog").close();
  showOverview();
}

function renderOverview() {
  const container = $("#channel-overview");
  container.innerHTML = "";
  channels.forEach((channel) => {
    const fragment = $("#channel-template").content.cloneNode(true);
    const button = fragment.querySelector("button");
    button.style.setProperty("--accent", channel.meta.accent);
    fragment.querySelector(".channel-number").textContent = String(channel.meta.order).padStart(2, "0");
    fragment.querySelector(".channel-name").textContent = channel.name;
    fragment.querySelector(".channel-description").textContent = channel.meta.description;
    const fullCount = channel.topics.filter((topic) => topic.script_text).length;
    const waiting = channel.content_status === "WAITING_FOR_TRANSCRIPT_SAMPLES";
    button.classList.toggle("is-waiting", waiting);
    fragment.querySelector(".channel-state").textContent = waiting
      ? "等待文稿樣本"
      : channel.name === "收盤夜話"
        ? "最近交易日稿"
        : "暫定風格稿";
    fragment.querySelector(".channel-foot b").textContent = waiting
      ? "0 篇 · 不虛構"
      : `${channel.topics.length} 個選題 · ${fullCount} 篇全文`;
    button.addEventListener("click", () => showChannel(channel));
    container.appendChild(fragment);
  });
}

function showChannel(channel) {
  activeChannel = channel;
  $("#channel-overview").hidden = true;
  $("#channel-detail").hidden = false;
  $("#page-title").textContent = `${channel.name}：標題與文稿`;
  $("#page-summary").textContent = channel.reason;
  $("#detail-kicker").textContent = channel.meta.kicker;
  $("#detail-title").textContent = channel.name;
  $("#detail-summary").textContent = `${channel.meta.description} 風格狀態：${channel.style_status}。`;
  $("#detail-status").textContent = channel.topics.length
    ? `${channel.content_date} · ${channel.topics.filter((topic) => topic.script_text).length} 篇完整文稿 · 上線前人工核對`
    : channel.reason;
  const listRoot = $("#topic-list");
  listRoot.innerHTML = "";
  if (!channel.topics.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = `<strong>這個頻道暫不生成文稿</strong><p>${escapeHtml(channel.reason)}</p><p>需要：至少2篇完整文稿，包含標題、日期、正文與Ben認為好或不好的原因。</p>`;
    listRoot.appendChild(empty);
    return;
  }
  channel.topics.forEach((topic, index) => {
    const fragment = $("#topic-template").content.cloneNode(true);
    const row = fragment.querySelector(".topic-row");
    row.style.setProperty("--accent", channel.meta.accent);
    fragment.querySelector(".topic-rank").textContent = String(index + 1).padStart(2, "0");
    const scriptMeta = topic.script_text ? `正文 ${topic.script_character_count.toLocaleString("zh-TW")} 字符` : "選題綱要";
    fragment.querySelector(".topic-meta").textContent = `${topicLabel(topic)} · ${scriptMeta} · ${topic.editorial_status || "NEEDS_REVIEW"}`;
    fragment.querySelector("h3").textContent = topic.title;
    fragment.querySelector("p").textContent = whyText(topic);
    fragment.querySelector(".topic-open").textContent = topic.script_text ? "看完整文稿" : "看完整選題";
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
    const humanUrl = row.human_verification_url || row.url;
    const rawUrl = row.raw_api_url && row.raw_api_url !== humanUrl ? row.raw_api_url : "";
    const primary = humanUrl
      ? `<a href="${escapeHtml(humanUrl)}" target="_blank" rel="noreferrer">${escapeHtml(label)} · 官網核對 ↗</a>`
      : `<span>${escapeHtml(label)}</span>`;
    const raw = rawUrl
      ? `<a href="${escapeHtml(rawUrl)}" target="_blank" rel="noreferrer">原始資料 ↗</a>`
      : "";
    return `${primary}${raw}`;
  }).join("");
}

function openTopic(channel, topic) {
  activeTopic = topic;
  const draft = topic.script_text || "這個選題目前只有標題、理由與來源，尚未生成全文。";
  const draftCount = topic.script_character_count || characterCount(draft);
  const titleOptions = list(topic.title_options).length
    ? `<section class="title-options"><h3>可用標題</h3><ul>${list(topic.title_options).map((title) => `<li>${escapeHtml(title)}</li>`).join("")}</ul></section>`
    : "";
  $("#dialog-content").innerHTML = `
    <div class="dialog-inner">
      <span class="topic-type">${escapeHtml(channel.name)} · ${escapeHtml(topicLabel(topic))}</span>
      <h2>${escapeHtml(topic.title)}</h2>
      ${titleOptions}
      <div class="reason-grid">
        <section class="reason-block"><h3>為什麼是今天</h3><ul>${list(topic.why_now).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || `<li>${escapeHtml(whyText(topic))}</li>`}</ul></section>
        <section class="reason-block"><h3>為什麼適合這個頻道</h3><ul>${list(topic.why_channel).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || `<li>${escapeHtml(channel.meta.description)}</li>`}</ul></section>
        <section class="reason-block"><h3>已確認事實</h3><ul>${list(topic.facts).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || "<li>請從原始 Evidence 核對。</li>"}</ul></section>
        <section class="reason-block"><h3>還不能下的結論</h3><ul>${list(topic.unknowns).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || "<li>事件與股價之間的因果仍需確認。</li>"}</ul></section>
      </div>
      <section class="source-block"><h3>點擊核對來源</h3><div class="source-links">${evidenceLinks(topic)}</div></section>
      ${topic.script_text ? `<div class="draft-actions">
        <button class="draft-toggle" type="button">展開完整文稿</button>
        <button class="copy-button" type="button">複製文稿</button>
      </div>` : ""}
      <section class="draft-block" ${topic.script_text ? "hidden" : ""}>
        <p class="draft-note">${topic.script_text ? `正文字符數：${draftCount.toLocaleString("zh-TW")}（不含空白） · 上線前需人工核對` : "目前只有選題綱要"}</p>
        <h3>${escapeHtml(topic.title)}</h3>
        <div class="draft-copy">${escapeHtml(draft)}</div>
      </section>
    </div>`;
  const draftBlock = $(".draft-block");
  if (topic.script_text) {
    $(".draft-toggle").addEventListener("click", (event) => {
      draftBlock.hidden = !draftBlock.hidden;
      event.currentTarget.textContent = draftBlock.hidden ? "展開完整文稿" : "收起完整文稿";
    });
    $(".copy-button").addEventListener("click", async (event) => {
      const button = event.currentTarget;
      try {
        await navigator.clipboard.writeText(draft);
        button.textContent = "已複製";
      } catch {
        button.textContent = "複製失敗";
      }
      setTimeout(() => { button.textContent = "複製文稿"; }, 1200);
    });
  }
  $("#topic-dialog").showModal();
}

function showOverview() {
  activeChannel = null;
  $("#channel-overview").hidden = false;
  $("#channel-detail").hidden = true;
  $("#page-title").textContent = "已有樣本頻道：每頻道5題完整文稿";
  $("#page-summary").textContent = "同一熱點可以跨頻道覆蓋，但標題、切入角度與完整正文均依頻道定位生成；無文稿樣本的頻道不在本頁顯示。";
  renderOverview();
  window.scrollTo({ top: 0, behavior: "smooth" });
}

async function loadLatest() {
  const button = $("#refresh-button");
  button.disabled = true;
  button.classList.add("is-loading");
  const previousText = $("#refresh-state").textContent;
  $("#refresh-state").textContent = "正在重新讀取伺服器上的最新日報";
  try {
    const response = await fetch(`${DATA_URL}?v=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`資料 HTTP ${response.status}`);
    applyPayload(await response.json());
  } catch (error) {
    const refreshState = $("#refresh-state");
    refreshState.className = "refresh-state is-error";
    refreshState.textContent = channels.length
      ? `刷新失敗，繼續保留目前資料：${error.message}`
      : `今日資料讀取失敗：${error.message}`;
    if (!channels.length) $("#channel-overview").innerHTML = `<p>${escapeHtml(previousText)}</p>`;
  } finally {
    button.disabled = false;
    button.classList.remove("is-loading");
  }
}

$("#back-button").addEventListener("click", showOverview);
$(".brand").addEventListener("click", (event) => { event.preventDefault(); showOverview(); });
$("#dialog-close").addEventListener("click", () => $("#topic-dialog").close());
$("#topic-dialog").addEventListener("click", (event) => { if (event.target === event.currentTarget) event.currentTarget.close(); });
$("#refresh-button").addEventListener("click", loadLatest);

loadLatest();
