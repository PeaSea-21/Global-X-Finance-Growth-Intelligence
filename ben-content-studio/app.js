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
  $("#page-title").textContent = "今日頻道選題";
  $("#page-summary").textContent = "先看標題，再用理由、Evidence 和頻道草稿完成判斷。";
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
  const draft = topic.script_text || "今天這個選題的完整文稿尚未生成。";
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
        <p class="draft-note">${topic.script_text ? "完整文稿 · 上線前需人工核對" : "今日文稿尚未生成"}</p>
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
