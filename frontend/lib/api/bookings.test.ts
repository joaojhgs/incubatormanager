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
import { createPublicBooking } from "./bookings";

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

describe("createPublicBooking", () => {
  it("POST /bookings/external/ with public booking payload", async () => {
    const response = {
      id: "7e4ec982-f8f7-407b-849b-3057f3a88180",
      company_id: "cb0d7550-2622-43c7-a8a9-5a0054e16e84",
      space_id: "d8fdf6f0-e006-45a8-bf72-76a516d51d11",
      created_by_user_id: null,
      created_by_role: "Public",
      is_public: true,
      requester_name: "Ana Silva",
      requester_email: "ana@example.test",
      requester_phone: "+351910000000",
      start_time: "2026-06-01T10:00:00.000Z",
      end_time: "2026-06-01T12:00:00.000Z",
      quoted_price: "25.00",
      equipment_ids: [],
      status: "Pending",
      notes: "Open day",
      created_at: "2026-05-25T10:00:00Z",
      updated_at: "2026-05-25T10:00:00Z",
    };

    nock(BASE)
      .post(`${BASE_PATH}/bookings/external/`, {
        company_id: response.company_id,
        space_id: response.space_id,
        requester_name: response.requester_name,
        requester_email: response.requester_email,
        requester_phone: response.requester_phone,
        start_time: response.start_time,
        end_time: response.end_time,
        quoted_price: "25.00",
        notes: "Open day",
      })
      .reply(201, response);

    await expect(
      createPublicBooking({
        company_id: response.company_id,
        space_id: response.space_id,
        requester_name: response.requester_name,
        requester_email: response.requester_email,
        requester_phone: response.requester_phone,
        start_time: response.start_time,
        end_time: response.end_time,
        quoted_price: "25.00",
        notes: "Open day",
      }),
    ).resolves.toEqual(response);
    expect(nock.isDone()).toBe(true);
  });
});
