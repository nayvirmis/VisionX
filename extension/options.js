const DEFAULT_API_URL = "http://localhost:5000";
const form = document.getElementById("options-form");
const input = document.getElementById("api-url");
const status = document.getElementById("status");

document.addEventListener("DOMContentLoaded", async () => {
  const { apiUrl } = await chrome.storage.sync.get("apiUrl");
  input.value = apiUrl || DEFAULT_API_URL;
});

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  let url;
  try {
    url = new URL(input.value.trim());
  } catch {
    status.textContent = "Enter a valid backend URL.";
    return;
  }
  if (!["http:", "https:"].includes(url.protocol)) {
    status.textContent = "Use an HTTP or HTTPS URL.";
    return;
  }
  if (
    url.protocol !== "https:" &&
    !["localhost", "127.0.0.1"].includes(url.hostname)
  ) {
    status.textContent = "Deployed backends must use HTTPS.";
    return;
  }

  const originPattern = `${url.protocol}//${url.hostname}/*`;
  const granted = await chrome.permissions.request({
    origins: [originPattern],
  });
  if (!granted) {
    status.textContent = "Host access is required to use this backend.";
    return;
  }

  await chrome.storage.sync.set({ apiUrl: url.origin });
  status.textContent = "Backend saved.";
});
