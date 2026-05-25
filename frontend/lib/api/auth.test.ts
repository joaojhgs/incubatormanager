import nock from "nock";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("./client")>();
  return {
    ...mod,
    getDefaultApiClient: vi.fn(),
  };
});

import { logoutSession, redirectToCookieClearingLogout } from "./auth";
import { createApiClient, getDefaultApiClient } from "./client";

const BASE = "http://127.0.0.1:9";
const BASE_PATH = "/api";

afterEach(() => {
  nock.cleanAll();
  nock.enableNetConnect();
  vi.unstubAllGlobals();
});

beforeEach(() => {
  nock.disableNetConnect();
  const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });
  vi.mocked(getDefaultApiClient).mockReturnValue(client);
});

describe("logoutSession", () => {
  it("POST /auth/logout/", async () => {
    nock(BASE).post(`${BASE_PATH}/auth/logout/`, {}).reply(204);

    await expect(logoutSession()).resolves.toBeUndefined();
    expect(nock.isDone()).toBe(true);
  });
});

describe("redirectToCookieClearingLogout", () => {
  it("uses the canonical trailing-slash logout endpoint", () => {
    const assign = vi.fn();
    vi.stubGlobal("window", { location: { assign } });

    redirectToCookieClearingLogout("/staff");

    expect(assign).toHaveBeenCalledWith("/api/auth/logout/?next=%2Fstaff");
  });
});
