import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import test from "node:test";

const root = new URL("../", import.meta.url);

test("public review page states honest capability boundaries", async () => {
  const [html, script, payload] = await Promise.all([
    readFile(new URL("index.html", root), "utf8"),
    readFile(new URL("app.js", root), "utf8"),
    readFile(new URL("brief.json", root), "utf8"),
  ]);
  const data = JSON.parse(payload);
  assert.match(html, /正在確認資料版本/);
  assert.match(html, /現在做到哪裡/);
  assert.match(html, /還沒做到/);
  assert.match(html, /這次最想請 Ben 確認/);
  assert.match(html, /下載回饋 CSV/);
  assert.match(script, /規則排序，不是 AI/);
  assert.match(script, /BEN_Radar_三頻道回饋/);
  assert.doesNotMatch(html, /READY_TO_PITCH/);
  assert.match(script, /CURRENT SESSION/);
  assert.equal(typeof data.replay_mode, "boolean");
  assert.equal(data.briefs.length, 3);
  assert.ok(data.briefs.every((brief) => brief.assignments.length >= 5));
});

test("public review page ships all local assets", async () => {
  await Promise.all([
    readFile(new URL("styles.css", root)),
    readFile(new URL("favicon.svg", root)),
  ]);
});
