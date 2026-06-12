const FEED_SELECTOR = 'div[data-testid="primaryColumn"] section > div > div';
const MAX_WAIT_MS = 15000;

injectStyles();

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message.type === "VISIONX_LOAD_FEED") {
    loadFeed(message)
      .then(() => sendResponse({ ok: true }))
      .catch((error) => sendResponse({ ok: false, error: error.message }));
    return true;
  }
  if (message.type === "VISIONX_RESTORE_FEED") {
    VisionXRenderer.removeFeed(document);
    sendResponse({ ok: true });
  }
  return false;
});

async function loadFeed(message) {
  const feed = await waitForFeed(document, MAX_WAIT_MS);
  VisionXRenderer.renderFeed(document, feed, message.posts, message.source);
}

function waitForFeed(documentRef, timeoutMs) {
  const current = documentRef.querySelector(FEED_SELECTOR);
  if (current) return Promise.resolve(current);

  return new Promise((resolve, reject) => {
    const observer = new MutationObserver(() => {
      const feed = documentRef.querySelector(FEED_SELECTOR);
      if (feed) {
        clearTimeout(timeout);
        observer.disconnect();
        resolve(feed);
      }
    });
    const timeout = setTimeout(() => {
      observer.disconnect();
      reject(
        new Error(
          "The X timeline did not become available. Refresh the page and try again.",
        ),
      );
    }, timeoutMs);
    observer.observe(documentRef.documentElement, {
      childList: true,
      subtree: true,
    });
  });
}

function injectStyles() {
  if (document.getElementById("visionx-styles")) return;
  const style = document.createElement("style");
  style.id = "visionx-styles";
  style.textContent = `
    #visionx-feed-container {
      border-bottom: 1px solid rgb(47, 51, 54);
      color: inherit;
      font-family: TwitterChirp, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }
    .visionx-banner {
      padding: 12px 16px;
      background: rgba(20, 110, 245, 0.1);
      color: rgb(29, 155, 240);
      font-size: 14px;
      font-weight: 700;
    }
    .visionx-post {
      display: grid;
      grid-template-columns: 48px minmax(0, 1fr);
      gap: 12px;
      padding: 14px 16px;
      border-top: 1px solid rgb(47, 51, 54);
    }
    .visionx-avatar {
      width: 48px;
      height: 48px;
      border-radius: 50%;
      object-fit: cover;
    }
    .visionx-post-header {
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      align-items: baseline;
    }
    .visionx-post-header span,
    .visionx-post-header time,
    .visionx-post-footer {
      color: rgb(113, 118, 123);
    }
    .visionx-post-text {
      margin: 4px 0 10px;
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      line-height: 1.35;
    }
    .visionx-media {
      display: grid;
      gap: 4px;
      margin: 10px 0;
      overflow: hidden;
      border: 1px solid rgb(47, 51, 54);
      border-radius: 8px;
    }
    .visionx-media img,
    .visionx-media video {
      display: block;
      width: 100%;
      max-height: 540px;
      object-fit: contain;
      background: black;
    }
    .visionx-post-footer {
      display: flex;
      flex-wrap: wrap;
      justify-content: space-between;
      gap: 8px 14px;
      font-size: 12px;
    }
    .visionx-post-footer a {
      color: rgb(29, 155, 240);
      text-decoration: none;
    }
    @media (max-width: 520px) {
      .visionx-post {
        grid-template-columns: 40px minmax(0, 1fr);
        padding: 12px;
      }
      .visionx-avatar {
        width: 40px;
        height: 40px;
      }
    }
  `;
  document.head.append(style);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { waitForFeed };
}
