const DATA_URL = "data.json";

const CHANNEL_META = {
  "收盤夜話": {
    order: 1,
    accent: "#b83a35",
    kicker: "TAIWAN POST-CLOSE EDITORIAL",
    description: "下班後 15 分鐘，把今天大盤發生什麼、誰在買賣、明天看什麼講清楚。",
    status: "收盤夜話單頻道試點",
  },
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

function normalizeEditorial(payload) {
  const editorial = payload.close_talk_editorial || {};
  const angles = list(editorial.angles);
  return angles.map((angle, index) => ({
    ...angle,
    candidate_rank: angle.rank || index + 1,
    candidate_type: "CLOSE_TALK_EDITORIAL",
    editorial_status: angle.editorial_state || editorial.status || "DRAFT_FOR_HUMAN_REVIEW",
    title: list(angle.title_options)[0] || angle.episode_question || `收盤夜話選題 ${index + 1}`,
    facts: list(angle.confirmed_facts).map((fact) => typeof fact === "string" ? fact : fact.text).filter(Boolean),
    why_now: angle.why_today ? [angle.why_today] : [],
    why_channel: angle.why_this_channel ? [angle.why_this_channel] : [],
    evidence: list(angle.source_cards).map((card) => ({
      ...card,
      source_id: card.source_name || card.source_id,
      evidence_class: card.epistemic_status || "SOURCE",
    })),
    script_text: angle.script?.full_text || "",
    script_character_count: angle.script?.character_count || characterCount(angle.script?.full_text || ""),
  }));
}

function normalizeChannels(payload) {
  const editorial = payload.close_talk_editorial || {};
  return [{
    name: "收盤夜話",
    meta: CHANNEL_META["收盤夜話"],
    topics: normalizeEditorial(payload),
    editorial,
    official: editorial.status === "DRAFT_FOR_HUMAN_REVIEW",
  }];
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
  channels = normalizeChannels(payload);
  if (channels.length !== 1) {
    throw new Error("收盤夜話資料尚未發布");
  }
  const sessionDate = payload.market_session_date;
  const isCurrent = sessionDate === taipeiDate();
  $("#session-date").textContent = `${sessionDate} 收盤資料`;
  $("#generated-time").textContent = new Intl.DateTimeFormat("zh-TW", {
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
    timeZone: "Asia/Taipei",
  }).format(new Date(payload.generated_at));
  const editorial = payload.close_talk_editorial || {};
  $("#ranking-method").textContent = editorial.status === "DRAFT_FOR_HUMAN_REVIEW" ? "編輯稿待審" : "資料待齊";
  const xRow = sourceRow(payload, "X");
  $("#x-count").textContent = `${list(editorial.angles).length} 個選題`;
  $("#source-twse").textContent = sourceLabel(payload, "TWSE_EOD");
  $("#source-tpex").textContent = sourceLabel(payload, "TPEX_EOD");
  $("#source-mops").textContent = sourceLabel(payload, "MOPS");
  $("#source-news").textContent = sourceLabel(payload, "NEWS");
  $("#source-x").textContent = sourceLabel(payload, "X");
  const refreshState = $("#refresh-state");
  refreshState.className = `refresh-state${isCurrent ? "" : " is-stale"}`;
  refreshState.textContent = isCurrent
    ? `已載入 ${sessionDate} 最新收盤版`
    : `目前顯示最近成功的 ${sessionDate} 收盤版，今日資料尚未發布`;
  if ($("#topic-dialog").open) $("#topic-dialog").close();
  showChannel(channels[0]);
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
  $("#page-title").textContent = "今日收盤夜話文稿";
  $("#page-summary").textContent = "只看收盤夜話：先選題，再核對理由、Evidence 和完整文稿。";
  $("#detail-kicker").textContent = channel.meta.kicker;
  $("#detail-title").textContent = channel.name;
  $("#detail-summary").textContent = channel.meta.description;
  const editorial = channel.editorial || {};
  $("#detail-status").textContent = channel.topics.length
    ? "今日收盤夜話編輯稿：標題、理由、Evidence 與文稿集中在這裡。"
    : `${editorial.reason || "今日收盤夜話完整文稿尚未生成。"}`;
  const listRoot = $("#topic-list");
  listRoot.innerHTML = "";
  if (!channel.topics.length) {
    const empty = document.createElement("div");
    empty.className = "empty-state";
    empty.innerHTML = `<strong>今天的收盤夜話文稿還沒生成</strong><p>${escapeHtml(editorial.reason || "官方收盤資料尚未全部到齊，系統不會拿其他頻道內容代替。")}</p>`;
    listRoot.appendChild(empty);
    return;
  }
  channel.topics.forEach((topic, index) => {
    const fragment = $("#topic-template").content.cloneNode(true);
    const row = fragment.querySelector(".topic-row");
    row.style.setProperty("--accent", channel.meta.accent);
    fragment.querySelector(".topic-rank").textContent = String(index + 1).padStart(2, "0");
    fragment.querySelector(".topic-meta").textContent = `${topicLabel(topic)} · ${topic.editorial_status || "NEEDS_REVIEW"}`;
    fragment.querySelector("h3").textContent = topic.title;
    fragment.querySelector("p").textContent = whyText(topic);
    fragment.querySelector(".topic-open").textContent = "看完整文稿";
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
  const draft = topic.script_text || "今天這個選題的完整文稿尚未生成。";
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
      <div class="draft-actions">
        <button class="draft-toggle" type="button">展開頻道草稿</button>
        <button class="copy-button" type="button">複製草稿</button>
      </div>
      <section class="draft-block" hidden>
        <p class="draft-note">${topic.script_text ? `正文字符数：${draftCount.toLocaleString("zh-TW")}（不含空白） · 上線前需人工核對` : "今日文稿尚未生成"}</p>
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
  if (channels[0]) showChannel(channels[0]);
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
