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
import { createUser, getUserById, listUsers, updateUser, type UserUpdatePayload } from "./users";

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

describe("createUser", () => {
  it("POST /auth/users/", async () => {
    const created = {
      id: "22222222-2222-4222-8222-222222222222",
      email: "new@example.com",
      role: "Staff",
      first_name: "N",
      last_name: "User",
      company_id: null,
      is_active: true,
    };
    nock(BASE)
      .post(`${BASE_PATH}/auth/users/`, {
        email: "new@example.com",
        password: "longpass1",
        first_name: "N",
        last_name: "User",
        role: "Staff",
      })
      .reply(201, created);

    await expect(
      createUser({
        email: "new@example.com",
        password: "longpass1",
        first_name: "N",
        last_name: "User",
        role: "Staff",
      }),
    ).resolves.toEqual(created);
    expect(nock.isDone()).toBe(true);
  });
});

describe("getUserById", () => {
  it("GET /auth/users/{id}/", async () => {
    const row = {
      id: "11111111-1111-1111-1111-111111111111",
      email: "a@example.com",
      role: "Staff",
      first_name: "A",
      last_name: "B",
      company_id: null,
      is_active: true,
    };
    nock(BASE)
      .get(`${BASE_PATH}/auth/users/${encodeURIComponent(row.id)}/`)
      .reply(200, row);

    await expect(getUserById(row.id)).resolves.toEqual(row);
    expect(nock.isDone()).toBe(true);
  });
});

describe("updateUser", () => {
  it("PATCH /auth/users/{id}/", async () => {
    const id = "11111111-1111-1111-1111-111111111111";
    const payload: UserUpdatePayload = { first_name: "X" };
    const response = {
      id,
      email: "a@example.com",
      role: "Staff",
      first_name: "X",
      last_name: "B",
      company_id: null,
      is_active: true,
    };
    nock(BASE)
      .patch(
        `${BASE_PATH}/auth/users/${encodeURIComponent(id)}/`,
        (body: Record<string, unknown>) => body.first_name === "X",
      )
      .reply(200, response);

    await expect(updateUser(id, payload)).resolves.toEqual(response);
    expect(nock.isDone()).toBe(true);
  });
});
