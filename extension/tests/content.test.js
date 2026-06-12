const assert = require("node:assert/strict");
const test = require("node:test");
const { JSDOM } = require("jsdom");

function loadContent() {
  const dom = new JSDOM(
    "<!doctype html><html><head></head><body></body></html>",
  );
  global.document = dom.window.document;
  global.MutationObserver = dom.window.MutationObserver;
  global.VisionXRenderer = require("../lib/renderer.js");
  global.chrome = {
    runtime: {
      onMessage: { addListener() {} },
    },
  };
  delete require.cache[require.resolve("../content.js")];
  return { dom, api: require("../content.js") };
}

test("discovers a timeline that appears after the content script starts", async () => {
  const { dom, api } = loadContent();
  const waiting = api.waitForFeed(dom.window.document, 250);

  const primary = dom.window.document.createElement("div");
  primary.dataset.testid = "primaryColumn";
  primary.innerHTML = "<section><div><div id='timeline'></div></div></section>";
  dom.window.document.body.append(primary);

  const timeline = await waiting;
  assert.equal(timeline.id, "timeline");
});

test("stops observing when the timeline never appears", async () => {
  const { dom, api } = loadContent();
  await assert.rejects(
    api.waitForFeed(dom.window.document, 10),
    /timeline did not become available/,
  );
});
