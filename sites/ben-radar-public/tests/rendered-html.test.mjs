import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import test from "node:test";

async function render() {
  const workerUrl = new URL("../dist/server/index.js", import.meta.url);
  workerUrl.searchParams.set("test", `${process.pid}-${Date.now()}`);
  const { default: worker } = await import(workerUrl.href);
  return worker.fetch(
    new Request("https://ben-radar.test/", { headers: { accept: "text/html" } }),
    { ASSETS: { fetch: async () => new Response("Not found", { status: 404 }) } },
    { waitUntil() {}, passThroughOnException() {} },
  );
}

test("server-renders the BEN Radar public snapshot", async () => {
  const response = await render();
  assert.equal(response.status, 200);
  assert.match(response.headers.get("content-type") ?? "", /^text\/html\b/i);
  const html = await response.text();
  assert.match(html, /BEN Radar/);
  assert.match(html, /市场异动/);
  assert.match(html, /实际成交量/);
  assert.match(html, /RVOL/);
  assert.match(html, /机会雷达/);
  assert.match(html, /查看 Evidence/);
  assert.match(html, /加入选题池/);
  assert.match(html, /ben-stock-workbench\.v0\.1/);
  assert.match(html, /非投资建议/);
  assert.ok((html.match(/class="event-card"/g) ?? []).length >= 16);
  assert.doesNotMatch(html, /codex-preview|SkeletonPreview|Tunnel Unavailable/);
});

test("ships product metadata, snapshot data, and social card", async () => {
  const [page, layout, payload] = await Promise.all([
    readFile(new URL("../app/page.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/layout.tsx", import.meta.url), "utf8"),
    readFile(new URL("../app/radar-data.json", import.meta.url), "utf8"),
  ]);
  const data = JSON.parse(payload);
  assert.equal(data.events.length, 16);
  assert.equal(data.stock_workbench.top20.length, 20);
  assert.equal(Object.keys(data.stock_workbench.details).length, 20);
  assert.equal(data.stock_workbench.replay_date, "2026-08-17");
  assert.ok(data.stock_workbench.top20.every((stock) => stock.current_volume > 0 && stock.median_volume_20d > 0));
  assert.ok(data.source_coverage.snapshot_concentration.unique_publishers >= 5);
  assert.ok(data.events.every((event) => event.event_id && event.items.length > 0));
  assert.match(page, /ben-stock-radar\.public-queue\.v1/);
  assert.match(page, /导出 JSON/);
  assert.match(layout, /BEN Radar｜台湾股票异动工作台/);
  assert.match(layout, /openGraph/);
  await access(new URL("../public/og.png", import.meta.url));
  await assert.rejects(access(new URL("../app/_sites-preview/SkeletonPreview.tsx", import.meta.url)));
});
