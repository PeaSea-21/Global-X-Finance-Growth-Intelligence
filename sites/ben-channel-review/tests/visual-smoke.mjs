import assert from "node:assert/strict";
import { chromium } from "file:///C:/Users/yinen/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright/index.mjs";

const browser = await chromium.launch({
  headless: true,
  executablePath: "C:/Program Files/Google/Chrome/Application/chrome.exe",
});
const targetUrl = process.env.BEN_REVIEW_URL || "http://127.0.0.1:8770/";

const cases = [
  { name: "desktop", viewport: { width: 1280, height: 900 } },
  { name: "mobile", viewport: { width: 390, height: 844 } },
];

try {
  for (const testCase of cases) {
    const page = await browser.newPage({ viewport: testCase.viewport });
    const errors = [];
    page.on("console", (message) => {
      if (message.type() === "error") errors.push(message.text());
    });
    page.on("pageerror", (error) => errors.push(error.message));
    await page.goto(targetUrl, { waitUntil: "networkidle" });
    await page.locator("#channel-tabs button").first().waitFor();

    assert.equal(await page.locator("#channel-tabs button").count(), 3);
    assert.equal(await page.locator(".channel-panel:not([hidden]) .topic-card").count(), 5);
    const payload = JSON.parse(await page.request.get(`${targetUrl}brief.json`).then((response) => response.text()));
    assert.match(
      await page.locator("#replay-notice").innerText(),
      payload.replay_mode ? /歷史回放/ : /當日收盤資料/,
    );
    assert.match(await page.locator("#progress").innerText(), /還沒做到/);

    for (let index = 0; index < 3; index += 1) {
      await page.locator("#channel-tabs button").nth(index).click();
      assert.equal(await page.locator(".channel-panel:not([hidden]) .topic-card").count(), 5);
    }

    const feedbackButton = page.locator(".channel-panel:not([hidden]) .topic-card").first().locator('[data-feedback="USEFUL"]');
    await feedbackButton.click();
    assert.equal(await feedbackButton.evaluate((element) => element.classList.contains("active")), true);
    assert.equal(await page.evaluate(() => Boolean(localStorage.getItem("ben-channel-review.feedback.v1"))), true);
    assert.equal(await page.locator("#feedback-count").innerText(), "1");

    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    assert.ok(overflow <= 1, `horizontal overflow ${overflow}px at ${testCase.name}`);
    assert.deepEqual(errors, []);
    await page.evaluate(() => window.scrollTo(0, 0));
    await page.screenshot({
      path: `../../deliverables/BEN_channel_review_${testCase.name}.png`,
      fullPage: true,
    });
    await page.close();
  }
} finally {
  await browser.close();
}

console.log("Visual smoke passed: 3 tabs, 5 topics each, local feedback, no overflow, no page errors.");
