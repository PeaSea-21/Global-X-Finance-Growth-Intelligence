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
let historyIndex = [];
let reviewPolicy = {};
let activeChannel = null;
let activeTopic = null;

const $ = (selector) => document.querySelector(selector);
const list = (value) => Array.isArray(value) ? value : [];
const escapeHtml = (value) => String(value ?? "").replace(/[&<>'"]/g, (char) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" }[char]));
const characterCount = (value) => [...String(value ?? "").replace(/\s/g, "")].length;

function topicLabel(item) {
  if (item.candidate_type?.includes("CLOSE_TALK_EDITORIAL")) return "收盤夜話選題";
  if (item.script_generation_method?.startsWith("CHANNEL_PROGRAM_EVIDENCE_")) return "跨頻道熱點 · 時長達標完整稿";
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
  return item.selection_reason?.summary || list(item.why_now)[0] || list(item.facts)[0] || "今日候選已通過時效與 Evidence 檢查。";
}

const OUTCOME_LABELS = {
  CONFIRMED: "已驗證",
  PARTIALLY_CONFIRMED: "部分驗證",
  NOT_CONFIRMED: "尚未驗證",
  INVALIDATED: "原判斷失效",
  PENDING_DATA: "等待後續資料",
};

function outcomeLabel(value) {
  return OUTCOME_LABELS[value] || "等待後續資料";
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
    historyEntries: historyIndex.filter((entry) => entry.channel_id === channel.channel_id),
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
  historyIndex = list(workbench.channel_history_index);
  reviewPolicy = workbench.review_policy || {};
  channels = normalizeChannels(payload);
  if (channels.length !== 11 || channels.some((channel) => channel.topics.length !== 5)) {
    throw new Error("已有樣本頻道尚未形成五題審稿面");
  }
  if (channels.some((channel) => channel.topics.some((topic) => !topic.script_text))) {
    throw new Error("已有樣本頻道仍有未完成文稿");
  }
  if (channels.some((channel) => channel.topics.some((topic) => topic.script_meets_target !== true))) {
    throw new Error("已有樣本頻道仍有未達時長門檻的文稿");
  }
  if (channels.some((channel) => !channel.historyEntries.length)) {
    throw new Error("已有樣本頻道尚未建立可追溯的歷史回顧");
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
  refreshState.textContent = workbench.market_data_status === "SOURCE_PENDING"
    ? `已載入 ${snapshotDate} 同日來源文稿；TWSE 收盤資料待官方更新，最近真實交易日 ${workbench.last_market_session_date}`
    : `已載入 ${snapshotDate} 選題快照；收盤夜話使用交易日 ${workbench.last_market_session_date}`;
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
  $("#detail-summary").textContent = `${channel.meta.description} 目標時長：${channel.target_duration}；每篇至少 ${channel.minimum_script_character_count.toLocaleString("zh-TW")} 字符。風格狀態：${channel.style_status}。`;
  $("#detail-status").textContent = channel.topics.length
    ? `${channel.content_date} · ${channel.topics.filter((topic) => topic.script_text).length} 篇完整文稿 · 上線前人工核對`
    : channel.reason;
  $("#history-count").textContent = channel.historyEntries.length.toLocaleString("zh-TW");
  showChannelView("today");
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderTopics(channel, topics, root, options = {}) {
  root.innerHTML = "";
  const historical = options.historical === true;
  const date = options.contentDate || channel.content_date;
  topics.forEach((topic, index) => {
    const fragment = $("#topic-template").content.cloneNode(true);
    const row = fragment.querySelector(".topic-row");
    row.style.setProperty("--accent", channel.meta.accent);
    fragment.querySelector(".topic-rank").textContent = String(index + 1).padStart(2, "0");
    const targetState = topic.script_meets_target ? "已達時長門檻" : "未達時長門檻";
    const scriptMeta = topic.script_text
      ? `正文 ${Number(topic.script_character_count || 0).toLocaleString("zh-TW")} 字符 · ${topic.script_target_duration || "原稿"} · ${targetState}`
      : "選題綱要";
    const review = outcomeLabel(topic.outcome_review?.status);
    fragment.querySelector(".topic-meta").textContent = historical
      ? `${date} · ${review} · ${scriptMeta}`
      : `${topicLabel(topic)} · ${scriptMeta} · ${topic.editorial_status || "NEEDS_REVIEW"}`;
    fragment.querySelector("h3").textContent = topic.title;
    fragment.querySelector("p").textContent = whyText(topic);
    fragment.querySelector(".topic-open").textContent = historical ? "看原稿與結果" : "看完整文稿";
    fragment.querySelector(".topic-open").addEventListener("click", () => openTopic(channel, topic, {
      historical,
      contentDate: date,
      reviewProgress: options.reviewProgress,
    }));
    root.appendChild(fragment);
  });
}

function renderToday(channel) {
  const listRoot = $("#topic-list");
  listRoot.innerHTML = "";
  if (!channel.topics.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = `<strong>這個頻道暫不生成文稿</strong><p>${escapeHtml(channel.reason)}</p><p>需要：至少2篇完整文稿，包含標題、日期、正文與Ben認為好或不好的原因。</p>`;
    listRoot.appendChild(empty);
    return;
  }
  renderTopics(channel, channel.topics, listRoot);
}

function historyStatusSummary(entry) {
  const counts = entry.status_counts || {};
  const outcome = Object.entries(counts).map(([status, count]) => `${outcomeLabel(status)} ${count}`).join(" · ") || "等待後續資料";
  const progress = entry.review_progress || {};
  return `${outcome} · 到期 ${Number(progress.due_window_count || 0)} 檔 · 已過 ${Number(progress.elapsed_market_sessions || 0)} 個可用交易日`;
}

function topicsWithReviewEvents(artifact) {
  const events = list(artifact.review_events);
  const latestByTopic = new Map();
  events.forEach((event) => latestByTopic.set(event.candidate_id, event));
  return list(artifact.channel?.topics).map((topic) => {
    const event = latestByTopic.get(topic.candidate_id);
    if (!event) return topic;
    const checkpointResults = new Map(list(event.checkpoint_results).map((row) => [row.checkpoint_id, row]));
    return {
      ...topic,
      outcome_review: {
        status: event.status,
        summary: event.summary,
        observation_date: event.observation_date,
        measured_result: event.measured_result,
        evidence: list(event.evidence),
      },
      review_checkpoints: list(topic.review_checkpoints).map((checkpoint) => ({
        ...checkpoint,
        ...(checkpointResults.get(checkpoint.checkpoint_id) || {}),
      })),
    };
  });
}

async function openHistoryEntry(channel, entry, button) {
  const oldText = button.textContent;
  button.disabled = true;
  button.textContent = "讀取中";
  try {
    const response = await fetch(`${entry.path}?v=${Date.now()}`, { cache: "no-store" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const artifact = await response.json();
    const snapshot = artifact.channel;
    if (!snapshot || snapshot.channel_id !== channel.channel_id) throw new Error("歷史檔案與頻道不符");
    const historyRoot = $("#history-list");
    historyRoot.innerHTML = `
      <div class="history-head">
        <button class="history-back" type="button">← 返回歷史日期</button>
        <div><strong>${escapeHtml(entry.content_date)}</strong><span>${escapeHtml(historyStatusSummary(entry))} · 原稿不改寫</span></div>
      </div>
      <div class="history-topic-list"></div>`;
    historyRoot.querySelector(".history-back").addEventListener("click", () => renderHistoryIndex(channel));
    renderTopics(channel, topicsWithReviewEvents(artifact), historyRoot.querySelector(".history-topic-list"), {
      historical: true,
      contentDate: entry.content_date,
      reviewProgress: entry.review_progress,
    });
  } catch (error) {
    button.textContent = `讀取失敗：${error.message}`;
    return;
  } finally {
    button.disabled = false;
  }
  button.textContent = oldText;
}

function renderHistoryIndex(channel) {
  const root = $("#history-list");
  root.innerHTML = "";
  if (!channel.historyEntries.length) {
    root.innerHTML = '<div class="empty-state"><strong>尚無歷史版本</strong><p>第一次更新後，舊稿會自動保留在這裡。</p></div>';
    return;
  }
  channel.historyEntries.forEach((entry) => {
    const article = document.createElement("article");
    article.className = "history-entry";
    article.innerHTML = `
      <div><span>原始發布日</span><strong>${escapeHtml(entry.content_date)}</strong></div>
      <p>${escapeHtml(historyStatusSummary(entry))}</p>
      <small>${Number(entry.topic_count || 0).toLocaleString("zh-TW")} 個原始選題與完整文稿 · ${escapeHtml(entry.snapshot_fingerprint.slice(0, 12))}</small>
      <button type="button">打開回顧</button>`;
    article.querySelector("button").addEventListener("click", (event) => openHistoryEntry(channel, entry, event.currentTarget));
    root.appendChild(article);
  });
}

function showChannelView(view) {
  if (!activeChannel) return;
  const historical = view === "history";
  $("#today-tab").classList.toggle("is-active", !historical);
  $("#history-tab").classList.toggle("is-active", historical);
  $("#today-tab").setAttribute("aria-selected", String(!historical));
  $("#history-tab").setAttribute("aria-selected", String(historical));
  $("#topic-list").hidden = historical;
  $("#history-list").hidden = !historical;
  if (historical) renderHistoryIndex(activeChannel);
  else renderToday(activeChannel);
}

function evidenceLinks(item) {
  const rows = allEvidence(item);
  if (!rows.length) return '<p class="source-empty">暫無可點擊 Evidence</p>';
  return rows.map((row, index) => {
    const label = `${row.evidence_class || row.epistemic_status || "Evidence"} · ${row.source_id || `來源 ${index + 1}`}`;
    const humanUrl = row.human_verification_url || row.url;
    const rawUrl = row.raw_api_url && row.raw_api_url !== humanUrl ? row.raw_api_url : "";
    const primary = humanUrl
      ? `<a href="${escapeHtml(humanUrl)}" target="_blank" rel="noreferrer">官網核對 ↗</a>`
      : `<span>無可點擊原文</span>`;
    const raw = rawUrl
      ? `<a href="${escapeHtml(rawUrl)}" target="_blank" rel="noreferrer">原始資料 ↗</a>`
      : "";
    const published = sourceTimeRow("原文發布", row.published_at);
    const fetched = sourceTimeRow("抓取時間", row.fetched_at || row.collected_at);
    const sourceDate = !published
      ? sourceTimeRow("資料時間", row.trade_date || row.observed_at || row.data_as_of || row.announced_at)
      : "";
    const times = published || fetched || sourceDate
      ? `${published}${fetched}${sourceDate}`
      : '<span class="source-time-missing">時間未提供</span>';
    return `<article class="source-card">
      <div class="source-card-head"><strong>${escapeHtml(label)}</strong><span>${escapeHtml(row.freshness_bucket || "")}</span></div>
      <p>${escapeHtml(row.title || "來源未提供標題")}</p>
      <div class="source-times">${times}</div>
      <div class="source-actions">${primary}${raw}</div>
    </article>`;
  }).join("");
}

function formatSourceTime(value) {
  const raw = String(value || "").trim();
  if (!raw) return "";
  if (/^\d{4}-\d{2}-\d{2}$/.test(raw)) return `${raw.replaceAll("-", "/")}（來源資料日）`;
  const parsed = new Date(raw);
  if (Number.isNaN(parsed.getTime())) return raw;
  return new Intl.DateTimeFormat("zh-TW", {
    timeZone: "Asia/Taipei",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(parsed) + "（台北）";
}

function sourceTimeRow(label, value) {
  const formatted = formatSourceTime(value);
  return formatted ? `<span><b>${escapeHtml(label)}</b>${escapeHtml(formatted)}</span>` : "";
}

function selectionReasonHtml(topic) {
  const reason = topic.selection_reason || {};
  const rows = [
    ["現在變了什麼", reason.what_changed],
    ["觀眾為什麼要在意", reason.audience_relevance],
    ["為什麼由這個頻道講", reason.channel_fit],
    ["真正的矛盾", reason.editorial_tension],
    ["下一步怎麼驗證", reason.next_verification],
  ].filter(([, value]) => value);
  return rows.map(([label, value]) => `<li><strong>${escapeHtml(label)}：</strong>${escapeHtml(value)}</li>`).join("");
}

function reviewEvidenceLinks(rows) {
  return list(rows).map((row, index) => {
    const url = row.human_verification_url || row.url;
    const label = row.title || row.source_id || `結果來源 ${index + 1}`;
    return url
      ? `<a href="${escapeHtml(url)}" target="_blank" rel="noreferrer">${escapeHtml(label)} ↗</a>`
      : `<span>${escapeHtml(label)}</span>`;
  }).join("");
}

function reviewWindowLabel(row) {
  if (row.status === "DUE") return "到期應復盤";
  if (row.status === "UPCOMING") return `還差 ${Number(row.remaining_market_sessions || 0)} 個交易日`;
  if (row.status === "WAITING_PUBLICATION_METRICS") return "等待發布記錄";
  return "事件落地即復盤";
}

function reviewScheduleHtml(progress) {
  if (!progress) return '<p class="review-rule">原稿归档后才开始计算复盘周期。</p>';
  const rows = [
    ...list(progress.content_windows),
    ...list(progress.market_windows),
    ...(progress.event_window ? [progress.event_window] : []),
  ];
  return `<div class="review-schedule">
    <div class="review-schedule-head"><strong>复盘时间表</strong><span>截至 ${escapeHtml(progress.latest_available_market_session || "尚无完整市场日")}</span></div>
    ${rows.map((row) => `<div class="review-window status-${escapeHtml(row.status || "UPCOMING")}">
      <b>${escapeHtml(row.label)}</b><span>${escapeHtml(reviewWindowLabel(row))}</span><p>${escapeHtml(row.focus)}</p>
    </div>`).join("")}
  </div>`;
}

function outcomeReviewHtml(topic, options = {}) {
  const outcome = topic.outcome_review || { status: "PENDING_DATA", summary: "等待後續資料。" };
  const checkpoints = list(topic.review_checkpoints);
  const outcomeSummary = outcome.status === "PENDING_DATA"
    ? "尚未取得滿足核驗點的後續資料；不得標記為說中或看錯。"
    : (outcome.summary || "等待後續資料。");
  return `
    <section class="review-block">
      <div class="review-title"><h3>回顧與驗證</h3><span class="review-status status-${escapeHtml(outcome.status || "PENDING_DATA")}">${escapeHtml(outcomeLabel(outcome.status))}</span></div>
      <div class="thesis-grid">
        <div><strong>原稿基準判斷</strong><p>${escapeHtml(topic.thesis || "原稿未形成方向判斷。")}</p></div>
        <div><strong>原稿保留的反方解釋</strong><p>${escapeHtml(topic.counter_thesis || "尚無反方條件。")}</p></div>
      </div>
      <p class="review-summary">${escapeHtml(outcomeSummary)}${outcome.observation_date ? ` · 觀察日 ${escapeHtml(outcome.observation_date)}` : ""}</p>
      ${reviewScheduleHtml(options.reviewProgress)}
      <ol class="checkpoint-list">${checkpoints.map((checkpoint) => `
        <li><span>${escapeHtml(outcomeLabel(checkpoint.status))}</span><p>${escapeHtml(checkpoint.check)}</p>${checkpoint.measured_result ? `<small>${escapeHtml(checkpoint.measured_result)}</small>` : ""}</li>`).join("")}</ol>
      <div class="source-links review-links">${reviewEvidenceLinks(outcome.evidence)}</div>
      <p class="review-rule">只有具備觀察日期與可點擊結果來源，才可標記「已驗證」或「原判斷失效」。</p>
    </section>`;
}

function openTopic(channel, topic, options = {}) {
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
      <section class="selection-block"><h3>為什麼選這題</h3><p>${escapeHtml(topic.selection_reason?.summary || whyText(topic))}</p><ul>${selectionReasonHtml(topic)}</ul></section>
      <div class="reason-grid">
        <section class="reason-block"><h3>為什麼是今天</h3><ul>${list(topic.why_now).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || `<li>${escapeHtml(whyText(topic))}</li>`}</ul></section>
        <section class="reason-block"><h3>為什麼適合這個頻道</h3><ul>${list(topic.why_channel).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || `<li>${escapeHtml(channel.meta.description)}</li>`}</ul></section>
        <section class="reason-block"><h3>已確認事實</h3><ul>${list(topic.facts).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || "<li>請從原始 Evidence 核對。</li>"}</ul></section>
        <section class="reason-block"><h3>還不能下的結論</h3><ul>${list(topic.unknowns).map((row) => `<li>${escapeHtml(row)}</li>`).join("") || "<li>事件與股價之間的因果仍需確認。</li>"}</ul></section>
      </div>
      ${outcomeReviewHtml(topic, options)}
      <section class="source-block"><h3>資料源與時間</h3><p class="source-note">優先顯示原文發布時間；來源另有抓取時間時一併列出。所有時間統一換算為台北時間。</p><div class="source-cards">${evidenceLinks(topic)}</div></section>
      ${topic.script_text ? `<div class="draft-actions">
        <button class="draft-toggle" type="button">展開完整文稿</button>
        <button class="copy-button" type="button">複製文稿</button>
      </div>` : ""}
      <section class="draft-block" ${topic.script_text ? "hidden" : ""}>
        <p class="draft-note">${topic.script_text ? `${options.historical ? `原稿日期：${escapeHtml(options.contentDate || channel.content_date)} · 原稿不改寫 · ` : ""}正文字符數：${draftCount.toLocaleString("zh-TW")}（不含空白） · 目標 ${escapeHtml(topic.script_target_duration)}／最低 ${Number(topic.script_minimum_character_count).toLocaleString("zh-TW")} · 已達標 · 上線前需人工核對` : "目前只有選題綱要"}</p>
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
$("#today-tab").addEventListener("click", () => showChannelView("today"));
$("#history-tab").addEventListener("click", () => showChannelView("history"));

loadLatest();
