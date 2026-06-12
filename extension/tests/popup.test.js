const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const { JSDOM } = require("jsdom");

function loadPopup(queryResult, sendMessage) {
  const html = fs.readFileSync(
    path.join(__dirname, "..", "popup.html"),
    "utf8",
  );
  const dom = new JSDOM(html);
  global.document = dom.window.document;
  global.chrome = {
    runtime: { sendMessage: async () => ({}) },
    tabs: {
      query: async () => queryResult,
      sendMessage,
    },
  };
  delete require.cache[require.resolve("../popup.js")];
  return require("../popup.js");
}

test("rejects feed loading when the active tab is not X", async () => {
  const popup = loadPopup(
    [{ id: 1, url: "https://example.com/" }],
    async () => ({}),
  );
  const response = await popup.sendToActiveXTab({
    type: "VISIONX_LOAD_FEED",
  });
  assert.equal(response.ok, false);
  assert.match(response.error, /Open an X.com tab/);
});

test("reports a content-script messaging failure clearly", async () => {
  const popup = loadPopup([{ id: 2, url: "https://x.com/home" }], async () => {
    throw new Error("No receiver");
  });
  const response = await popup.sendToActiveXTab({
    type: "VISIONX_RESTORE_FEED",
  });
  assert.equal(response.ok, false);
  assert.match(response.error, /Refresh the page/);
});
