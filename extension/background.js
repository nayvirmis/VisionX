const DEFAULT_API_URL = "http://localhost:5000";

chrome.runtime.onInstalled.addListener(async () => {
  const { apiUrl } = await chrome.storage.sync.get("apiUrl");
  if (!apiUrl) {
    await chrome.storage.sync.set({ apiUrl: DEFAULT_API_URL });
  }
});

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  handleMessage(message)
    .then(sendResponse)
    .catch((error) => {
      sendResponse({
        ok: false,
        error: error.message || "Unexpected extension error.",
      });
    });
  return true;
});

async function handleMessage(message) {
  switch (message.type) {
    case "apiRequest":
      return apiRequest(message.path, message.options || {});
    case "getAuth":
      return getAuthState();
    case "storeAuth":
      await storeAuth(message.payload);
      return { ok: true };
    case "clearAuth":
      await clearAuth();
      return { ok: true };
    case "getConfig":
      return { ok: true, apiUrl: await getApiUrl() };
    case "openOptions":
      await chrome.runtime.openOptionsPage();
      return { ok: true };
    default:
      return { ok: false, error: "Unknown background request." };
  }
}

async function getApiUrl() {
  const { apiUrl } = await chrome.storage.sync.get("apiUrl");
  return (apiUrl || DEFAULT_API_URL).replace(/\/+$/, "");
}

async function getAuthState() {
  const values = await chrome.storage.local.get([
    "accessToken",
    "refreshToken",
    "currentUser",
  ]);
  return {
    ok: true,
    authenticated: Boolean(values.accessToken && values.refreshToken),
    accessToken: values.accessToken || null,
    refreshToken: values.refreshToken || null,
    user: values.currentUser || null,
  };
}

async function storeAuth(payload) {
  await chrome.storage.local.set({
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
    currentUser: payload.user || null,
  });
}

async function clearAuth() {
  await chrome.storage.local.remove([
    "accessToken",
    "refreshToken",
    "currentUser",
  ]);
}

async function refreshAccessToken(apiUrl, refreshToken) {
  const response = await fetch(`${apiUrl}/api/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
  });
  const payload = await parseResponse(response);
  if (!response.ok) {
    await clearAuth();
    throw new Error(payload.error?.message || "Your session has expired.");
  }
  await chrome.storage.local.set({
    accessToken: payload.access_token,
    refreshToken: payload.refresh_token,
  });
  return payload.access_token;
}

async function apiRequest(path, options) {
  const apiUrl = await getApiUrl();
  const auth = await getAuthState();
  const requestOptions = {
    method: options.method || "GET",
    headers: { ...(options.headers || {}) },
  };
  if (options.body !== undefined) {
    requestOptions.headers["Content-Type"] = "application/json";
    requestOptions.body = JSON.stringify(options.body);
  }
  if (options.auth !== false && auth.accessToken) {
    requestOptions.headers.Authorization = `Bearer ${auth.accessToken}`;
  }

  let response;
  try {
    response = await fetch(`${apiUrl}${path}`, requestOptions);
  } catch {
    return {
      ok: false,
      status: 0,
      error: "Cannot reach the VisionX backend. Check the extension options.",
    };
  }

  if (response.status === 401 && options.auth !== false && auth.refreshToken) {
    try {
      const token = await refreshAccessToken(apiUrl, auth.refreshToken);
      requestOptions.headers.Authorization = `Bearer ${token}`;
      response = await fetch(`${apiUrl}${path}`, requestOptions);
    } catch (error) {
      return { ok: false, status: 401, error: error.message };
    }
  }

  const payload = await parseResponse(response);
  return {
    ok: response.ok,
    status: response.status,
    data: response.ok ? payload : null,
    error: response.ok
      ? null
      : payload.error?.message ||
        `Request failed with status ${response.status}.`,
  };
}

async function parseResponse(response) {
  if (response.status === 204) {
    return {};
  }
  const contentType = response.headers.get("content-type") || "";
  return contentType.includes("application/json") ? response.json() : {};
}

if (typeof module !== "undefined" && module.exports) {
  module.exports = {
    apiRequest,
    clearAuth,
    getAuthState,
    parseResponse,
    storeAuth,
  };
}
