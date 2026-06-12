const assert = require("node:assert/strict");
const test = require("node:test");

function loadBackground(initial = {}) {
  const local = { ...initial };
  const sync = { apiUrl: "https://api.example.com" };
  global.chrome = {
    runtime: {
      onInstalled: { addListener() {} },
      onMessage: { addListener() {} },
      openOptionsPage: async () => {},
    },
    storage: {
      local: {
        async get(keys) {
          return Object.fromEntries(keys.map((key) => [key, local[key]]));
        },
        async set(values) {
          Object.assign(local, values);
        },
        async remove(keys) {
          keys.forEach((key) => delete local[key]);
        },
      },
      sync: {
        async get() {
          return sync;
        },
        async set(values) {
          Object.assign(sync, values);
        },
      },
    },
  };
  delete require.cache[require.resolve("../background.js")];
  return { api: require("../background.js"), local };
}

test("refreshes an expired access token and retries the API request", async () => {
  const { api, local } = loadBackground({
    accessToken: "expired",
    refreshToken: "refresh-one",
  });
  const calls = [];
  global.fetch = async (url, options) => {
    calls.push({ url, options });
    if (calls.length === 1) {
      return Response.json({ error: { message: "Expired" } }, { status: 401 });
    }
    if (calls.length === 2) {
      return Response.json({
        access_token: "access-two",
        refresh_token: "refresh-two",
      });
    }
    return Response.json({ value: "ok" });
  };

  const response = await api.apiRequest("/api/auth/me", {});

  assert.equal(response.ok, true);
  assert.equal(response.data.value, "ok");
  assert.equal(local.accessToken, "access-two");
  assert.equal(local.refreshToken, "refresh-two");
  assert.equal(calls[2].options.headers.Authorization, "Bearer access-two");
});

test("returns a useful error when the backend cannot be reached", async () => {
  const { api } = loadBackground();
  global.fetch = async () => {
    throw new Error("offline");
  };

  const response = await api.apiRequest("/health/live", { auth: false });

  assert.equal(response.ok, false);
  assert.equal(response.status, 0);
  assert.match(response.error, /Cannot reach/);
});
