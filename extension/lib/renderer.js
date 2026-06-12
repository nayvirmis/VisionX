(function exposeVisionXRenderer(global) {
  const CONTAINER_ID = "visionx-feed-container";

  function formatCount(value) {
    const number = Number(value) || 0;
    if (number >= 1_000_000) return `${(number / 1_000_000).toFixed(1)}M`;
    if (number >= 1_000) return `${(number / 1_000).toFixed(1)}K`;
    return String(number);
  }

  function safeHttpsUrl(value) {
    try {
      const url = new URL(value);
      return url.protocol === "https:" ? url.href : "";
    } catch {
      return "";
    }
  }

  function createPostElement(documentRef, post) {
    const article = documentRef.createElement("article");
    article.className = "visionx-post";
    article.dataset.postId = post.id;

    const avatar = documentRef.createElement("img");
    avatar.className = "visionx-avatar";
    avatar.src =
      safeHttpsUrl(post.author?.profile_image_url) ||
      "https://abs.twimg.com/sticky/default_profile_images/default_profile_normal.png";
    avatar.alt = "";

    const body = documentRef.createElement("div");
    body.className = "visionx-post-body";

    const header = documentRef.createElement("div");
    header.className = "visionx-post-header";
    const name = documentRef.createElement("strong");
    name.textContent = post.author?.name || post.author?.username || "X user";
    const username = documentRef.createElement("span");
    username.textContent = `@${post.author?.username || "unknown"}`;
    const date = documentRef.createElement("time");
    date.dateTime = post.created_at || "";
    date.textContent = post.created_at
      ? new Date(post.created_at).toLocaleDateString()
      : "";
    header.append(name, username, date);

    const text = documentRef.createElement("p");
    text.className = "visionx-post-text";
    text.textContent = post.text || "";

    const media = documentRef.createElement("div");
    media.className = "visionx-media";
    for (const item of post.media || []) {
      const mediaUrl = safeHttpsUrl(item.url);
      if (!mediaUrl) continue;
      const element =
        item.type === "video"
          ? documentRef.createElement("video")
          : documentRef.createElement("img");
      element.src = mediaUrl;
      if (element.tagName === "VIDEO") {
        element.controls = true;
        element.muted = true;
        element.playsInline = true;
      } else {
        element.alt = "Post media";
        element.loading = "lazy";
      }
      media.append(element);
    }

    const footer = documentRef.createElement("div");
    footer.className = "visionx-post-footer";
    const metrics = post.metrics || {};
    footer.append(
      metric(documentRef, "Replies", metrics.replies),
      metric(documentRef, "Reposts", metrics.reposts),
      metric(documentRef, "Likes", metrics.likes),
      metric(documentRef, "Views", metrics.views),
    );
    const link = documentRef.createElement("a");
    const postUrl = safeHttpsUrl(post.url);
    if (postUrl) {
      link.href = postUrl;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.textContent = "View on X";
      footer.append(link);
    }

    body.append(header, text);
    if (media.childElementCount) body.append(media);
    body.append(footer);
    article.append(avatar, body);
    return article;
  }

  function metric(documentRef, label, value) {
    const span = documentRef.createElement("span");
    span.title = label;
    span.textContent = `${label} ${formatCount(value)}`;
    return span;
  }

  function renderFeed(documentRef, feed, posts, source) {
    removeFeed(documentRef);
    const container = documentRef.createElement("section");
    container.id = CONTAINER_ID;
    container.setAttribute("aria-label", `VisionX feed shared by ${source}`);

    const banner = documentRef.createElement("div");
    banner.className = "visionx-banner";
    banner.textContent = `VisionX shared feed · ${source}`;
    container.append(banner);

    const seen = new Set();
    for (const post of posts || []) {
      if (!post?.id || seen.has(post.id)) continue;
      seen.add(post.id);
      container.append(createPostElement(documentRef, post));
    }
    feed.prepend(container);
    return container;
  }

  function removeFeed(documentRef) {
    documentRef.getElementById(CONTAINER_ID)?.remove();
  }

  const api = {
    CONTAINER_ID,
    createPostElement,
    formatCount,
    removeFeed,
    renderFeed,
    safeHttpsUrl,
  };
  global.VisionXRenderer = api;
  if (typeof module !== "undefined" && module.exports) module.exports = api;
})(typeof globalThis !== "undefined" ? globalThis : window);
