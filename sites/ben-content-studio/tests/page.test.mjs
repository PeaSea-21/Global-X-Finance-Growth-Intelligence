import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("studio hides sample-free channels and gives every visible channel five unique topics", async () => {
  const [html, css, script, dataText] = await Promise.all([
    readFile(new URL("index.html", root), "utf8"),
    readFile(new URL("styles.css", root), "utf8"),
    readFile(new URL("app.js", root), "utf8"),
    readFile(new URL("data.json", root), "utf8"),
  ]);
  const data = JSON.parse(dataText);

  assert.match(html, /BEN 內容審稿/);
  assert.match(html, /href="favicon\.svg"/);
  assert.doesNotMatch(html, /\.\.\/ben-channel-review\/favicon\.svg/);
  assert.match(html, /topic-dialog/);
  assert.match(html, /history-tab/);
  assert.match(html, /歷史回顧/);
  assert.match(html, /refresh-button/);
  assert.match(html, /YouTube/);
  assert.match(script, /個股顯微鏡/);
  assert.match(script, /收盤夜話/);
  assert.match(script, /產業透視鏡/);
  assert.match(script, /權值旗艦/);
  assert.match(script, /資金雷達/);
  assert.match(script, /那指火箭/);
  assert.match(script, /板塊輪動儀/);
  assert.match(script, /暗池雷達/);
  assert.match(script, /期權守門人/);
  assert.match(script, /財報獵人/);
  assert.match(script, /宏觀天秤/);
  assert.match(script, /全球資金地圖/);
  assert.match(script, /地緣炸藥庫/);
  assert.match(script, /週期航海家/);
  assert.match(script, /鏈上顯微鏡/);
  assert.match(script, /中概風向球/);
  assert.match(script, /財商拆彈組/);
  assert.match(script, /半導體駭客/);
  assert.match(script, /華爾街溫度計/);
  assert.match(script, /定投實驗室/);
  assert.match(script, /已有樣本頻道：每頻道5題完整文稿/);
  assert.match(script, /content_status !== "WAITING_FOR_TRANSCRIPT_SAMPLES"/);
  assert.match(script, /看完整文稿/);
  assert.equal(data.weight_topics[0].editorial_status, "PREVIEW_FROM_OFFICIAL_EOD");
  assert.ok(data.close_talk_editorial);
  assert.match(script, /展開完整文稿/);
  assert.match(script, /Evidence/);
  assert.match(script, /為什麼選這題/);
  assert.match(script, /回顧與驗證/);
  assert.match(script, /資料源與時間/);
  assert.match(script, /原文發布/);
  assert.match(script, /抓取時間/);
  assert.match(script, /Asia\/Taipei/);
  assert.match(script, /原稿不改寫/);
  assert.match(script, /Date\.now\(\)/);
  assert.match(script, /cache: "no-store"/);
  assert.match(css, /empty-state/);
  assert.match(css, /\[hidden\]\s*\{\s*display:\s*none\s*!important/);
  assert.match(css, /channel-state/);
  assert.equal(data.studio_artifact, "BEN_CONTENT_STUDIO_DAILY");
  assert.equal(data.weight_topics.length, 5);
  assert.equal(data.briefs.length, 3);
  assert.equal(data.channel_workbench.channel_count, 20);
  assert.equal(data.channel_workbench.draft_ready_channel_count, 11);
  assert.equal(data.channel_workbench.waiting_sample_channel_count, 9);
  assert.equal(data.channel_workbench.public_visible_channel_count, 11);
  assert.equal(data.channel_workbench.hidden_waiting_channel_count, 9);
  assert.equal(data.channel_workbench.news_source_success_count, 14);
  assert.equal(data.channel_workbench.news_source_count, 14);
  assert.equal(data.channel_workbench.official_source_count, 4);
  assert.equal(data.channel_workbench.channels.length, 20);
  assert.equal(data.channel_workbench.history_entry_count, data.channel_workbench.channel_history_index.length);
  assert.ok(data.channel_workbench.channel_history_index.length >= 11);
  assert.deepEqual(
    data.channel_workbench.channels.filter((channel) => channel.content_status === "WAITING_FOR_TRANSCRIPT_SAMPLES").map((channel) => channel.channel_name),
    ["個股顯微鏡", "產業透視鏡", "財報獵人", "宏觀天秤", "地緣炸藥庫", "週期航海家", "半導體駭客", "華爾街溫度計", "定投實驗室"],
  );
  const fullScripts = data.channel_workbench.channels.flatMap((channel) => channel.topics).filter((topic) => topic.script_text);
  const visibleChannels = data.channel_workbench.channels.filter((channel) => channel.content_status !== "WAITING_FOR_TRANSCRIPT_SAMPLES");
  const allTopics = visibleChannels.flatMap((channel) => channel.topics);
  const publicTitles = allTopics.flatMap((topic) => topic.title_options);
  assert.equal(visibleChannels.length, 11);
  assert.ok(visibleChannels.every((channel) => channel.topics.length === 5));
  assert.equal(allTopics.length, 55);
  assert.equal(allTopics.filter((topic) => topic.candidate_type === "CHANNEL_TOPIC_OUTLINE").length, 0);
  assert.equal(new Set(publicTitles.map((title) => title.replace(/\s/g, "").toLowerCase())).size, publicTitles.length);
  assert.equal(fullScripts.length, 55);
  const minimums = new Map([
    ["收盤夜話", 3000],
    ["權值旗艦", 2000], ["那指火箭", 2000], ["板塊輪動儀", 2000], ["全球資金地圖", 2000],
    ["資金雷達", 1500], ["暗池雷達", 1500], ["鏈上顯微鏡", 1500], ["中概風向球", 1500],
    ["期權守門人", 1200], ["財商拆彈組", 1200],
  ]);
  assert.ok(visibleChannels.every((channel) => channel.minimum_script_character_count === minimums.get(channel.channel_name)));
  assert.ok(visibleChannels.every((channel) => channel.topics.every((topic) => (
    topic.script_character_count >= minimums.get(channel.channel_name)
    && topic.script_minimum_character_count === minimums.get(channel.channel_name)
    && topic.script_meets_target === true
  ))));
  assert.equal(new Set(fullScripts.map((topic) => topic.script_text.replace(/\s/g, ""))).size, 55);
  assert.ok(allTopics.every((topic) => topic.manuscript_alignment?.status === "PASS"));
  assert.ok(allTopics.every((topic) => topic.selection_reason?.dimensions?.length >= 5));
  assert.ok(allTopics.every((topic) => topic.review_checkpoints?.length >= 3));
  assert.ok(allTopics.every((topic) => topic.outcome_review?.status === "PENDING_DATA"));
  const allSources = allTopics.flatMap((topic) => topic.evidence || []);
  assert.equal(allSources.length, 134);
  assert.ok(allSources.every((source) => (
    source.published_at || source.fetched_at || source.trade_date || source.observed_at || source.data_as_of || source.announced_at
  )));
  assert.match(css, /source-cards/);
  assert.match(css, /source-times/);

  const historyArtifacts = await Promise.all(data.channel_workbench.channel_history_index.map(async (entry) => {
    const artifact = JSON.parse(await readFile(new URL(entry.path, root), "utf8"));
    assert.equal(artifact.snapshot_fingerprint, entry.snapshot_fingerprint);
    assert.equal(artifact.channel.channel_id, entry.channel_id);
    return artifact;
  }));
  assert.equal(new Set(historyArtifacts.map((artifact) => artifact.channel.channel_id)).size, 11);
});
