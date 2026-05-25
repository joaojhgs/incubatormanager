import nock from "nock";
import { afterEach, beforeEach, describe, expect, it } from "vitest";

const BASE = "http://127.0.0.1:9";
const BASE_PATH = "/api";

beforeEach(() => {
  nock.disableNetConnect();
  process.env.NEXT_PUBLIC_API_URL = `${BASE}${BASE_PATH}`;
});

afterEach(() => {
  nock.cleanAll();
  nock.enableNetConnect();
  delete process.env.NEXT_PUBLIC_API_URL;
});

describe("finance api", () => {
  it("passes payment filters through to the finance payments endpoint", async () => {
    const { listPayments } = await import("./finance");
    const scope = nock(BASE)
      .get(`${BASE_PATH}/finance/payments/`)
      .query({ status: "pending", source: "contract", payment_type: "monthly" })
      .reply(200, []);

    await expect(
      listPayments({ status: "pending", source: "contract", payment_type: "monthly" }),
    ).resolves.toEqual([]);
    expect(scope.isDone()).toBe(true);
  });

  it("loads report data and updates payments through dedicated finance endpoints", async () => {
    const { getFinanceReport, updatePayment } = await import("./finance");
    const scope = nock(BASE)
      .get(`${BASE_PATH}/finance/reports/`)
      .query({ type: "cash_flow_trend", group_by: "day" })
      .reply(200, { type: "cash_flow_trend", group_by: "day", results: [] })
      .patch(`${BASE_PATH}/finance/payments/payment-1/`, {
        status: "paid",
        paid_at: "2026-05-25T12:00:00.000Z",
      })
      .reply(200, { id: "payment-1", status: "paid" });

    await expect(getFinanceReport({ type: "cash_flow_trend", group_by: "day" })).resolves.toEqual({
      type: "cash_flow_trend",
      group_by: "day",
      results: [],
    });
    await expect(
      updatePayment("payment-1", { status: "paid", paid_at: "2026-05-25T12:00:00.000Z" }),
    ).resolves.toMatchObject({ id: "payment-1", status: "paid" });
    expect(scope.isDone()).toBe(true);
  });
});
