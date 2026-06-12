const test = require("node:test");
const assert = require("node:assert/strict");
const { JSDOM } = require("jsdom");

const renderer = require("../lib/renderer.js");

function post(id = "1") {
  return {
    id,
    text: "<img src=x onerror=alert(1)> plain text",
    created_at: "2026-06-12T10:00:00Z",
    url: `https://x.com/example/status/${id}`,
    author: {
      username: "example",
      name: "Example User",
      profile_image_url: "https://example.com/avatar.png",
      verified: false,
    },
    metrics: { replies: 1, reposts: 2, likes: 3000, views: 1000000 },
    media: [],
  };
}

test("renders external text without interpreting HTML", () => {
  const dom = new JSDOM("<main id='feed'></main>");
  const feed = dom.window.document.getElementById("feed");
  renderer.renderFeed(dom.window.document, feed, [post()], "alice");
  assert.equal(feed.querySelectorAll("img").length, 1);
  assert.match(feed.textContent, /<img src=x onerror=alert\(1\)> plain text/);
});

test("deduplicates posts and replaces the previous feed", () => {
  const dom = new JSDOM("<main id='feed'></main>");
  const feed = dom.window.document.getElementById("feed");
  renderer.renderFeed(dom.window.document, feed, [post(), post()], "alice");
  assert.equal(feed.querySelectorAll(".visionx-post").length, 1);
  renderer.renderFeed(dom.window.document, feed, [post("2")], "bob");
  assert.equal(feed.querySelectorAll(".visionx-post").length, 1);
  assert.equal(feed.querySelector(".visionx-post").dataset.postId, "2");
});

test("removes the injected container without touching the original feed", () => {
  const dom = new JSDOM(
    "<main id='feed'><div id='original'>Original</div></main>",
  );
  const feed = dom.window.document.getElementById("feed");
  renderer.renderFeed(dom.window.document, feed, [post()], "alice");
  renderer.removeFeed(dom.window.document);
  assert.equal(dom.window.document.getElementById(renderer.CONTAINER_ID), null);
  assert.equal(
    dom.window.document.getElementById("original").textContent,
    "Original",
  );
});

test("formats metric counts", () => {
  assert.equal(renderer.formatCount(999), "999");
  assert.equal(renderer.formatCount(1500), "1.5K");
  assert.equal(renderer.formatCount(2500000), "2.5M");
});

test("rejects non-HTTPS external URLs", () => {
  assert.equal(renderer.safeHttpsUrl("javascript:alert(1)"), "");
  assert.equal(renderer.safeHttpsUrl("http://example.com/image.png"), "");
  assert.equal(
    renderer.safeHttpsUrl("https://example.com/image.png"),
    "https://example.com/image.png",
  );
});
