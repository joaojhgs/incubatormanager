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
import { activateContract, createContract, terminateContract, updateContract } from "./contracts";

const BASE = "http://127.0.0.1:9";
const BASE_PATH = "/api";

const contractResponse = {
  id: "contract-1",
  company_id: "company-1",
  space_id: "space-1",
  status: "draft",
  area_sqm: "20.00",
  rate_per_sqm: "10.00",
  monthly_fee: "200.00",
  start_date: "2026-06-01",
  end_date: "2027-05-31",
  termination_reason: "",
  created_at: "2026-05-25T10:00:00Z",
  updated_at: "2026-05-25T10:00:00Z",
};

afterEach(() => {
  nock.cleanAll();
  nock.enableNetConnect();
});

beforeEach(() => {
  nock.disableNetConnect();
  const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });
  vi.mocked(getDefaultApiClient).mockReturnValue(client);
});

describe("contract API actions", () => {
  it("creates and updates contracts through contract service endpoints", async () => {
    const createPayload = {
      company_id: "company-1",
      space_id: "space-1",
      area_sqm: "20.00",
      rate_per_sqm: "10.00",
      start_date: "2026-06-01",
      end_date: "2027-05-31",
    };
    nock(BASE)
      .post(`${BASE_PATH}/contracts/`, createPayload)
      .reply(201, contractResponse)
      .patch(`${BASE_PATH}/contracts/contract-1/`, { end_date: "2027-06-30" })
      .reply(200, { ...contractResponse, end_date: "2027-06-30" });

    await expect(createContract(createPayload)).resolves.toEqual(contractResponse);
    await expect(updateContract("contract-1", { end_date: "2027-06-30" })).resolves.toMatchObject({
      end_date: "2027-06-30",
    });
    expect(nock.isDone()).toBe(true);
  });

  it("activates and terminates contract lifecycle actions", async () => {
    nock(BASE)
      .patch(`${BASE_PATH}/contracts/contract-1/activate/`)
      .reply(200, { ...contractResponse, status: "active" })
      .patch(`${BASE_PATH}/contracts/contract-1/terminate/`, { reason: "Ended" })
      .reply(200, { ...contractResponse, status: "terminated", termination_reason: "Ended" });

    await expect(activateContract("contract-1")).resolves.toMatchObject({ status: "active" });
    await expect(terminateContract("contract-1", { reason: "Ended" })).resolves.toMatchObject({
      status: "terminated",
      termination_reason: "Ended",
    });
    expect(nock.isDone()).toBe(true);
  });
});
