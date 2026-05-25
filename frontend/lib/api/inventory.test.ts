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
import {
  assignEquipment,
  createEquipment,
  createEquipmentType,
  listEquipmentAssignments,
  releaseEquipment,
  updateEquipment,
} from "./inventory";

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

describe("listEquipmentAssignments", () => {
  it("GET /inventory/assignments/ with booking and equipment filters", async () => {
    const response = [
      {
        id: "assignment-1",
        equipment_id: "equipment-1",
        equipment_name: "Projetor QA",
        booking_id: "booking-1",
        company_id: "company-1",
        assigned_space_id: "space-1",
        status: "Assigned",
        created_at: "2026-05-25T10:00:00Z",
        updated_at: "2026-05-25T11:00:00Z",
      },
    ];

    nock(BASE)
      .get(`${BASE_PATH}/inventory/assignments/`)
      .query({ booking: "booking-1", equipment: "equipment-1" })
      .reply(200, response);

    await expect(
      listEquipmentAssignments({ bookingId: "booking-1", equipmentId: "equipment-1" }),
    ).resolves.toEqual(response);
    expect(nock.isDone()).toBe(true);
  });

  it("writes equipment, types, assignments, and releases", async () => {
    nock(BASE)
      .post(`${BASE_PATH}/inventory/equipment-types/`, { name: "Projetor", is_active: true })
      .reply(201, { id: "type-1", name: "Projetor", is_active: true })
      .post(`${BASE_PATH}/inventory/equipment/`, {
        name: "Projetor A",
        equipment_type: "type-1",
        status: "Available",
      })
      .reply(201, { id: "equipment-1", name: "Projetor A", equipment_type: "type-1" })
      .patch(`${BASE_PATH}/inventory/equipment/equipment-1/`, { status: "Maintenance" })
      .reply(200, { id: "equipment-1", status: "Maintenance" })
      .post(`${BASE_PATH}/inventory/equipment/equipment-1/assign/`, {
        assigned_space_id: "space-1",
      })
      .reply(200, { id: "equipment-1", assigned_space_id: "space-1", status: "In use" })
      .post(`${BASE_PATH}/inventory/equipment/equipment-1/release/`, { booking_id: "booking-1" })
      .reply(200, { id: "equipment-1", assigned_space_id: null, status: "Available" });

    await expect(createEquipmentType({ name: "Projetor", is_active: true })).resolves.toMatchObject(
      {
        id: "type-1",
      },
    );
    await expect(
      createEquipment({ name: "Projetor A", equipment_type: "type-1", status: "Available" }),
    ).resolves.toMatchObject({ id: "equipment-1" });
    await expect(updateEquipment("equipment-1", { status: "Maintenance" })).resolves.toMatchObject({
      status: "Maintenance",
    });
    await expect(
      assignEquipment("equipment-1", { assigned_space_id: "space-1" }),
    ).resolves.toMatchObject({
      status: "In use",
    });
    await expect(
      releaseEquipment("equipment-1", { booking_id: "booking-1" }),
    ).resolves.toMatchObject({
      status: "Available",
    });
    expect(nock.isDone()).toBe(true);
  });
});
