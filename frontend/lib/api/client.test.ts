import nock from "nock";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { createApiClient } from "./client";
import { ACCESS_TOKEN_STORAGE_KEY } from "./constants";
import { clearAccessToken, getAccessToken, setAccessToken } from "./tokenStorage";

const BASE = "http://127.0.0.1:9";
const BASE_PATH = "/api";

afterEach(() => {
  nock.cleanAll();
  nock.enableNetConnect();
  clearAccessToken();
});

beforeEach(() => {
  nock.disableNetConnect();
});

describe("createApiClient", () => {
  it("sends Bearer token from hybrid storage", async () => {
    setAccessToken("alpha");
    const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });

    nock(BASE).get(`${BASE_PATH}/whoami`).reply(200, { id: 1 });

    const { data } = await client.get("/whoami");
    expect(data).toEqual({ id: 1 });
    expect(nock.isDone()).toBe(true);
  });

  it("refreshes on 401 then retries once with new token", async () => {
    setAccessToken("expired");
    const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });

    nock(BASE)
      .get(`${BASE_PATH}/resource`)
      .reply(401)
      .post(`${BASE_PATH}/auth/refresh`)
      .reply(200, { access_token: "fresh" })
      .get(`${BASE_PATH}/resource`)
      .reply(200, { ok: true });

    const { data } = await client.get("/resource");
    expect(data).toEqual({ ok: true });
    expect(getAccessToken()).toBe("fresh");
    expect(nock.isDone()).toBe(true);
  });

  it("clears session when refresh is exhausted (401)", async () => {
    setAccessToken("expired");
    const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });

    nock(BASE).get(`${BASE_PATH}/resource`).reply(401);
    nock(BASE).post(`${BASE_PATH}/auth/refresh`).reply(401, {});

    await expect(client.get("/resource")).rejects.toMatchObject({
      response: { status: 401 },
    });

    expect(getAccessToken()).toBeNull();
    expect(window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY)).toBeNull();
  });

  it("does not loop when the failing request is the refresh endpoint", async () => {
    setAccessToken("x");
    const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });

    nock(BASE).post(`${BASE_PATH}/auth/refresh`).reply(401, {});

    await expect(client.post("/auth/refresh", {})).rejects.toMatchObject({
      response: { status: 401 },
    });
    expect(nock.pendingMocks()).toHaveLength(0);
  });

  it("does not refresh on login 401", async () => {
    const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });

    nock(BASE).post(`${BASE_PATH}/auth/login`, { user: "u" }).reply(401, {});

    await expect(client.post("/auth/login", { user: "u" })).rejects.toMatchObject({
      response: { status: 401 },
    });
    expect(nock.pendingMocks()).toHaveLength(0);
  });

  it("coalesces concurrent 401s into a single refresh", async () => {
    setAccessToken("expired");
    const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });

    let refreshCount = 0;
    nock(BASE).get(`${BASE_PATH}/a`).times(2).reply(401);
    nock(BASE)
      .post(`${BASE_PATH}/auth/refresh`)
      .reply(() => {
        refreshCount += 1;
        return [200, { access_token: "renewed" }];
      });
    nock(BASE).get(`${BASE_PATH}/a`).times(2).reply(200, { ok: true });

    const [first, second] = await Promise.all([client.get("/a"), client.get("/a")]);
    expect(first.data).toEqual({ ok: true });
    expect(second.data).toEqual({ ok: true });
    expect(refreshCount).toBe(1);
    expect(getAccessToken()).toBe("renewed");
  });

  it("does not refresh again after a failed retry still returns 401", async () => {
    setAccessToken("expired");
    const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });

    nock(BASE).get(`${BASE_PATH}/denied`).reply(401);
    nock(BASE).post(`${BASE_PATH}/auth/refresh`).reply(200, { access_token: "new" });
    nock(BASE).get(`${BASE_PATH}/denied`).reply(401);

    await expect(client.get("/denied")).rejects.toMatchObject({
      response: { status: 401 },
    });
    expect(getAccessToken()).toBe("new");
  });
});
