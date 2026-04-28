import nock from "nock";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("./client")>();
  return {
    ...mod,
    getDefaultApiClient: vi.fn(),
  };
});

import { createApiClient, getDefaultApiClient } from "./client";
import { listUsers } from "./users";

const BASE = "http://127.0.0.1:9";
const BASE_PATH = "/api";

afterEach(() => {
  nock.cleanAll();
  nock.enableNetConnect();
});

beforeEach(() => {
  nock.disableNetConnect();
  const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });
  vi.mocked(getDefaultApiClient).mockReturnValue(client);
});

describe("listUsers", () => {
  it("GET /auth/users/", async () => {
    const rows = [
      {
        id: "11111111-1111-1111-1111-111111111111",
        email: "a@example.com",
        role: "director",
        first_name: "A",
        last_name: "B",
        company_id: null,
        is_active: true,
      },
    ];
    nock(BASE).get(`${BASE_PATH}/auth/users/`).reply(200, rows);

    await expect(listUsers()).resolves.toEqual(rows);
    expect(nock.isDone()).toBe(true);
  });
});
