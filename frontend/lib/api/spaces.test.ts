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
import { createSpace, createSpaceType, listSpaceBookingRecords, updateSpace } from "./spaces";

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

  it("writes spaces and space types through service endpoints", async () => {
    nock(BASE)
      .post(`${BASE_PATH}/space-types/`, { name: "Lab", is_active: true })
      .reply(201, { id: "type-1", name: "Lab", is_active: true })
      .post(`${BASE_PATH}/spaces/`, {
        name: "Room 1",
        space_type: "type-1",
        capacity: 8,
        status: "Available",
      })
      .reply(201, { id: "space-1", name: "Room 1", space_type: "type-1", capacity: 8 })
      .patch(`${BASE_PATH}/spaces/space-1/`, { status: "Maintenance" })
      .reply(200, { id: "space-1", status: "Maintenance" });

    await expect(createSpaceType({ name: "Lab", is_active: true })).resolves.toMatchObject({
      id: "type-1",
    });
    await expect(
      createSpace({ name: "Room 1", space_type: "type-1", capacity: 8, status: "Available" }),
    ).resolves.toMatchObject({ id: "space-1" });
    await expect(updateSpace("space-1", { status: "Maintenance" })).resolves.toMatchObject({
      status: "Maintenance",
    });
    expect(nock.isDone()).toBe(true);
  });
});
