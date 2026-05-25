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
import { listSpaceBookingRecords } from "./spaces";

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

describe("listSpaceBookingRecords", () => {
  it("GET /spaces/bookings/records/", async () => {
    const response = [
      {
        id: "booking-1",
        space_id: "space-1",
        company_id: "company-1",
        status: "Approved",
        start_time: "2026-05-26T10:00:00Z",
        end_time: "2026-05-26T11:00:00Z",
        quoted_price: "25.00",
        equipment_ids: ["equipment-1"],
      },
    ];

    nock(BASE).get(`${BASE_PATH}/spaces/bookings/records/`).reply(200, response);

    await expect(listSpaceBookingRecords()).resolves.toEqual(response);
    expect(nock.isDone()).toBe(true);
  });
});
