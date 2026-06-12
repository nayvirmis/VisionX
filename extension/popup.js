const loadingView = document.getElementById("loading");
const authView = document.getElementById("auth-view");
const dashboard = document.getElementById("dashboard");
const messageBox = document.getElementById("message");

document.addEventListener("DOMContentLoaded", initialize);

async function initialize() {
  bindEvents();
  const auth = await background({ type: "getAuth" });
  if (!auth.authenticated) {
    showView("auth");
    return;
  }
  const profile = await api("/api/auth/me");
  if (!profile.ok) {
    await background({ type: "clearAuth" });
    showView("auth");
    showMessage(profile.error, true);
    return;
  }
  await showDashboard(profile.data);
}

function bindEvents() {
  document
    .getElementById("open-options")
    .addEventListener("click", () => background({ type: "openOptions" }));
  document
    .getElementById("login-tab")
    .addEventListener("click", () => showAuthForm("login"));
  document
    .getElementById("register-tab")
    .addEventListener("click", () => showAuthForm("register"));
  document.getElementById("login-form").addEventListener("submit", login);
  document.getElementById("register-form").addEventListener("submit", register);
  document.getElementById("logout").addEventListener("click", logout);
  document.getElementById("connect-x").addEventListener("click", connectX);
  document
    .getElementById("disconnect-x")
    .addEventListener("click", disconnectX);
  document.getElementById("share-form").addEventListener("submit", shareFeed);
  document
    .getElementById("outgoing-list")
    .addEventListener("click", handleOutgoing);
  document
    .getElementById("incoming-list")
    .addEventListener("click", handleIncoming);
  document
    .getElementById("restore-feed")
    .addEventListener("click", restoreFeed);
  document
    .getElementById("delete-form")
    .addEventListener("submit", deleteAccount);
}

async function login(event) {
  event.preventDefault();
  await authenticate("/api/auth/login", {
    username: document.getElementById("login-username").value.trim(),
    password: document.getElementById("login-password").value,
  });
}

async function register(event) {
  event.preventDefault();
  const password = document.getElementById("register-password").value;
  const confirmation = document.getElementById("register-confirm").value;
  if (password !== confirmation) {
    showMessage("Passwords do not match.", true);
    return;
  }
  if (
    password.length < 8 ||
    !/[A-Z]/.test(password) ||
    !/[a-z]/.test(password) ||
    !/\d/.test(password)
  ) {
    showMessage(
      "Password must be at least 8 characters with uppercase, lowercase, and a number.",
      true,
    );
    return;
  }
  await authenticate("/api/auth/register", {
    username: document.getElementById("register-username").value.trim(),
    email: document.getElementById("register-email").value.trim(),
    password,
  });
}

async function authenticate(path, body) {
  setBusy(true);
  const response = await api(path, { method: "POST", body, auth: false });
  setBusy(false);
  if (!response.ok) {
    showView("auth");
    showMessage(response.error, true);
    return;
  }
  await background({ type: "storeAuth", payload: response.data });
  await showDashboard(response.data.user);
  showMessage("Signed in successfully.");
}

async function logout() {
  const auth = await background({ type: "getAuth" });
  await api("/api/auth/logout", {
    method: "POST",
    body: { refresh_token: auth.refreshToken },
    auth: false,
  });
  await background({ type: "clearAuth" });
  showView("auth");
  showMessage("Logged out.");
}

async function showDashboard(profile) {
  document.getElementById("profile-username").textContent = profile.username;
  document.getElementById("profile-email").textContent = profile.email;
  updateXAccount(profile.x_account);
  showView("dashboard");
  await Promise.all([loadOutgoing(), loadIncoming()]);
}

function updateXAccount(account) {
  const status = document.getElementById("x-account-status");
  const connect = document.getElementById("connect-x");
  const disconnect = document.getElementById("disconnect-x");
  if (account) {
    status.textContent = `Connected to @${account.username}`;
    connect.hidden = true;
    disconnect.hidden = false;
  } else {
    status.textContent = "Connect a public X account before sharing posts.";
    connect.hidden = false;
    disconnect.hidden = true;
  }
}

async function connectX() {
  const response = await api("/api/x/oauth/start", { method: "POST" });
  if (!response.ok) {
    showMessage(response.error, true);
    return;
  }
  await chrome.tabs.create({ url: response.data.authorize_url });
  showMessage("Complete the X connection in the new tab, then reopen VisionX.");
}

async function disconnectX() {
  const response = await api("/api/x/account", { method: "DELETE" });
  if (!response.ok) {
    showMessage(response.error, true);
    return;
  }
  updateXAccount(null);
  showMessage("X account disconnected.");
}

async function shareFeed(event) {
  event.preventDefault();
  const input = document.getElementById("share-username");
  const response = await api("/api/shares", {
    method: "POST",
    body: { username: input.value.trim() },
  });
  if (!response.ok) {
    showMessage(response.error, true);
    return;
  }
  input.value = "";
  await loadOutgoing();
  showMessage(`Feed shared with ${response.data.username}.`);
}

async function loadOutgoing() {
  const response = await api("/api/shares/outgoing");
  if (response.ok) {
    renderOutgoing(response.data);
  }
}

async function loadIncoming() {
  const response = await api("/api/shares/incoming");
  if (response.ok) {
    renderIncoming(response.data);
  }
}

function renderOutgoing(users) {
  const list = document.getElementById("outgoing-list");
  list.replaceChildren();
  if (!users.length) {
    list.append(emptyState("No one has access yet."));
    return;
  }
  users.forEach((user) => {
    const row = listRow(user.username);
    row.actions.append(
      actionButton("Remove", "remove-share", user.username, true),
    );
    list.append(row.element);
  });
}

function renderIncoming(users) {
  const list = document.getElementById("incoming-list");
  list.replaceChildren();
  if (!users.length) {
    list.append(emptyState("No feeds have been shared with you."));
    return;
  }
  users.forEach((user) => {
    const label = user.x_username
      ? `${user.username} · @${user.x_username}`
      : `${user.username} · X not connected`;
    const row = listRow(label);
    const button = actionButton("Load", "load-feed", user.username);
    button.disabled = !user.x_connected;
    row.actions.append(button);
    list.append(row.element);
  });
}

function listRow(label) {
  const element = document.createElement("div");
  element.className = "list-row";
  const text = document.createElement("span");
  text.textContent = label;
  const actions = document.createElement("div");
  actions.className = "actions";
  element.append(text, actions);
  return { element, actions };
}

function actionButton(label, action, username, secondary = false) {
  const button = document.createElement("button");
  button.type = "button";
  button.textContent = label;
  button.dataset.action = action;
  button.dataset.username = username;
  if (secondary) button.className = "secondary";
  return button;
}

function emptyState(text) {
  const paragraph = document.createElement("p");
  paragraph.className = "muted";
  paragraph.textContent = text;
  return paragraph;
}

async function handleOutgoing(event) {
  const button = event.target.closest("[data-action='remove-share']");
  if (!button) return;
  const response = await api(
    `/api/shares/${encodeURIComponent(button.dataset.username)}`,
    {
      method: "DELETE",
    },
  );
  if (!response.ok) {
    showMessage(response.error, true);
    return;
  }
  await loadOutgoing();
  showMessage("Feed access removed.");
}

async function handleIncoming(event) {
  const button = event.target.closest("[data-action='load-feed']");
  if (!button) return;
  button.disabled = true;
  const response = await api(
    `/api/feeds/${encodeURIComponent(button.dataset.username)}`,
  );
  button.disabled = false;
  if (!response.ok) {
    showMessage(response.error, true);
    return;
  }
  const sent = await sendToActiveXTab({
    type: "VISIONX_LOAD_FEED",
    posts: response.data.posts,
    source: response.data.source_user,
  });
  if (!sent.ok) {
    showMessage(sent.error, true);
    return;
  }
  showMessage(
    `Loaded ${response.data.count} post${response.data.count === 1 ? "" : "s"} from ${button.dataset.username}.`,
  );
}

async function restoreFeed() {
  const result = await sendToActiveXTab({ type: "VISIONX_RESTORE_FEED" });
  showMessage(result.ok ? "Original feed restored." : result.error, !result.ok);
}

async function sendToActiveXTab(message) {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  if (!tab?.id || !tab.url?.startsWith("https://x.com/")) {
    return {
      ok: false,
      error: "Open an X.com tab before loading or restoring a feed.",
    };
  }
  try {
    const response = await chrome.tabs.sendMessage(tab.id, message);
    return response || { ok: true };
  } catch {
    return {
      ok: false,
      error: "VisionX cannot reach this X tab. Refresh the page and try again.",
    };
  }
}

async function deleteAccount(event) {
  event.preventDefault();
  const response = await api("/api/auth/account", {
    method: "DELETE",
    body: { password: document.getElementById("delete-password").value },
  });
  if (!response.ok) {
    showMessage(response.error, true);
    return;
  }
  await background({ type: "clearAuth" });
  showView("auth");
  showMessage("VisionX account deleted.");
}

function showAuthForm(name) {
  const login = name === "login";
  document.getElementById("login-form").hidden = !login;
  document.getElementById("register-form").hidden = login;
  document.getElementById("login-tab").classList.toggle("active", login);
  document.getElementById("register-tab").classList.toggle("active", !login);
}

function showView(name) {
  loadingView.hidden = true;
  authView.hidden = name !== "auth";
  dashboard.hidden = name !== "dashboard";
}

function setBusy(busy) {
  loadingView.hidden = !busy;
  if (busy) {
    authView.hidden = true;
    dashboard.hidden = true;
  }
  document.querySelectorAll("button").forEach((button) => {
    button.disabled = busy;
  });
}

function showMessage(text, error = false) {
  messageBox.textContent = text;
  messageBox.hidden = false;
  messageBox.classList.toggle("error", error);
}

function api(path, options = {}) {
  return background({ type: "apiRequest", path, options });
}

function background(message) {
  return chrome.runtime.sendMessage(message);
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = { sendToActiveXTab };
}
