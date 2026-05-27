import dayjs from "dayjs";
import { describe, expect, it } from "vitest";

import {
  bookingRangeOverlaps,
  disabledBookingDate,
  disabledBookingTime,
} from "./bookingAvailability";

const SPACE_ID = "22222222-2222-4222-8222-222222222201";
const OTHER_SPACE_ID = "22222222-2222-4222-8222-222222222202";

describe("bookingAvailability", () => {
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

    const disabledTime = disabledBookingTime(
      dayjs("2026-06-18T00:00:00.000Z"),
      windows,
      SPACE_ID,
    );
    expect(disabledTime.disabledHours?.()).toEqual(expect.arrayContaining([9, 14]));
    expect(disabledTime.disabledHours?.()).not.toContain(10);
    expect(disabledTime.disabledMinutes?.(9)).toEqual([0, 30]);
    expect(disabledTime.disabledMinutes?.(10)).toEqual([]);
  });
});
