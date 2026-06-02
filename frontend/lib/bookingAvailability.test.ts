import dayjs from "dayjs";
import { afterEach, describe, expect, it, vi } from "vitest";

import {
  bookingRangeOverlaps,
  disabledBookingDate,
  disabledBookingEndDate,
  disabledBookingEndTime,
  disabledBookingTime,
} from "./bookingAvailability";

const SPACE_ID = "22222222-2222-4222-8222-222222222201";
const OTHER_SPACE_ID = "22222222-2222-4222-8222-222222222202";

describe("bookingAvailability", () => {
  afterEach(() => {
    vi.useRealTimers();
  });

  it("detects overlaps across multiple reservation windows for the selected space only", () => {
    const windows = [
      {
        space_id: SPACE_ID,
        start_time: "2026-06-15T09:00:00.000Z",
        end_time: "2026-06-15T11:00:00.000Z",
      },
      {
        space_id: SPACE_ID,
        start_time: "2026-06-15T14:00:00.000Z",
        end_time: "2026-06-15T16:00:00.000Z",
      },
      {
        space_id: OTHER_SPACE_ID,
        start_time: "2026-06-15T12:00:00.000Z",
        end_time: "2026-06-15T13:00:00.000Z",
      },
    ];

    expect(
      bookingRangeOverlaps(
        windows,
        SPACE_ID,
        dayjs("2026-06-15T09:30:00.000Z"),
        dayjs("2026-06-15T10:00:00.000Z"),
      ),
    ).toBe(true);
    expect(
      bookingRangeOverlaps(
        windows,
        SPACE_ID,
        dayjs("2026-06-15T13:00:00.000Z"),
        dayjs("2026-06-15T14:00:00.000Z"),
      ),
    ).toBe(false);
  });

  it("blocks fully reserved days and each reserved half-hour slot", () => {
    vi.setSystemTime(new Date("2026-06-01T00:00:00.000Z"));
    const windows = [
      {
        space_id: SPACE_ID,
        start_time: "2026-06-16T00:00:00.000Z",
        end_time: "2026-06-17T00:00:00.000Z",
      },
      {
        space_id: SPACE_ID,
        start_time: "2026-06-18T09:00:00.000Z",
        end_time: "2026-06-18T10:00:00.000Z",
      },
      {
        space_id: SPACE_ID,
        start_time: "2026-06-18T14:00:00.000Z",
        end_time: "2026-06-18T15:00:00.000Z",
      },
    ];

    expect(disabledBookingDate(dayjs("2026-06-16T12:00:00.000Z"), windows, SPACE_ID)).toBe(true);
    expect(disabledBookingDate(dayjs("2026-06-18T12:00:00.000Z"), windows, SPACE_ID)).toBe(false);

    const disabledTime = disabledBookingTime(dayjs("2026-06-18T00:00:00.000Z"), windows, SPACE_ID);
    expect(disabledTime.disabledHours?.()).toEqual(expect.arrayContaining([9, 14]));
    expect(disabledTime.disabledHours?.()).not.toContain(10);
    expect(disabledTime.disabledMinutes?.(9)).toEqual([0, 30]);
    expect(disabledTime.disabledMinutes?.(10)).toEqual([]);
  });

  it("blocks end dates and times when the full selected range crosses a booking window", () => {
    vi.setSystemTime(new Date("2026-06-02T00:00:00.000Z"));
    const demoSpaceTwo = "3c0f371a-71de-5647-89e2-bfbdc5c8bb72";
    const windows = [
      {
        space_id: demoSpaceTwo,
        start_time: "2026-06-03T11:00:00.000Z",
        end_time: "2026-06-03T15:00:00.000Z",
      },
    ];

    const startBeforeBookedWindow = dayjs("2026-06-03T10:00:00.000Z");
    expect(
      disabledBookingEndDate(
        dayjs("2026-06-04T00:00:00.000Z"),
        windows,
        demoSpaceTwo,
        startBeforeBookedWindow,
      ),
    ).toBe(true);
    expect(
      disabledBookingEndTime(
        dayjs("2026-06-03T00:00:00.000Z"),
        windows,
        demoSpaceTwo,
        startBeforeBookedWindow,
      ).disabledMinutes?.(11),
    ).toEqual([30]);
    expect(
      disabledBookingEndTime(
        dayjs("2026-06-03T00:00:00.000Z"),
        windows,
        demoSpaceTwo,
        startBeforeBookedWindow,
      ).disabledHours?.(),
    ).toEqual(expect.arrayContaining([12, 13, 14, 15]));

    const startAfterBookedWindow = dayjs("2026-06-03T15:00:00.000Z");
    expect(
      disabledBookingEndDate(
        dayjs("2026-06-04T00:00:00.000Z"),
        windows,
        demoSpaceTwo,
        startAfterBookedWindow,
      ),
    ).toBe(false);
    expect(
      bookingRangeOverlaps(
        windows,
        demoSpaceTwo,
        startAfterBookedWindow,
        dayjs("2026-06-04T09:00:00.000Z"),
      ),
    ).toBe(false);
  });
});
