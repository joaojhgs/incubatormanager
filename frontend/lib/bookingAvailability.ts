import type { Dayjs } from "dayjs";
import dayjs from "dayjs";

export interface BookingWindow {
  space_id: string;
  start_time: string;
  end_time: string;
}

const SLOT_MINUTES = 30;

export function bookingWindowsForSpace(
  windows: BookingWindow[] | undefined,
  spaceId: string | undefined,
): BookingWindow[] {
  if (!spaceId) return [];
  return (windows ?? []).filter((window) => window.space_id === spaceId);
}

export function bookingRangeOverlaps(
  windows: BookingWindow[] | undefined,
  spaceId: string | undefined,
  start: Dayjs | undefined,
  end: Dayjs | undefined,
): boolean {
  if (!spaceId || !start || !end || !end.isAfter(start)) return false;
  const startMs = start.valueOf();
  const endMs = end.valueOf();
  return bookingWindowsForSpace(windows, spaceId).some((window) => {
    const windowStart = Date.parse(window.start_time);
    const windowEnd = Date.parse(window.end_time);
    return (
      Number.isFinite(windowStart) &&
      Number.isFinite(windowEnd) &&
      startMs < windowEnd &&
      endMs > windowStart
    );
  });
}

export function spaceHasOverlap(
  windows: BookingWindow[] | undefined,
  spaceId: string,
  start: Dayjs | undefined,
  end: Dayjs | undefined,
): boolean {
  return bookingRangeOverlaps(windows, spaceId, start, end);
}

export function disabledBookingDate(
  date: Dayjs,
  windows: BookingWindow[] | undefined,
  spaceId: string | undefined,
): boolean {
  const now = dayjs();
  const dayStart = date.startOf("day");
  if (dayStart.isBefore(now.startOf("day"))) return true;
  const dayEnd = dayStart.add(1, "day");
  for (
    let cursor = dayStart;
    cursor.isBefore(dayEnd);
    cursor = cursor.add(SLOT_MINUTES, "minute")
  ) {
    const slotEnd = cursor.add(SLOT_MINUTES, "minute");
    const isPast = !slotEnd.isAfter(now);
    if (!isPast && !bookingRangeOverlaps(windows, spaceId, cursor, slotEnd)) return false;
  }
  return true;
}

export function disabledBookingTime(
  date: Dayjs | null,
  windows: BookingWindow[] | undefined,
  spaceId: string | undefined,
) {
  const now = dayjs();
  const intervals = bookingWindowsForSpace(windows, spaceId);
  if (!date) return {};

  const disabledHours = () =>
    Array.from({ length: 24 }, (_, hour) => hour).filter((hour) => {
      const hourStart = date.hour(hour).minute(0).second(0).millisecond(0);
      return [0, 30].every((minute) => {
        const slotStart = hourStart.minute(minute);
        const slotEnd = slotStart.add(SLOT_MINUTES, "minute");
        return (
          !slotEnd.isAfter(now) || bookingRangeOverlaps(intervals, spaceId, slotStart, slotEnd)
        );
      });
    });

  const disabledMinutes = (selectedHour?: number) => {
    if (typeof selectedHour !== "number") return [];
    return [0, 30].filter((minute) => {
      const slotStart = date.hour(selectedHour).minute(minute).second(0).millisecond(0);
      const slotEnd = slotStart.add(SLOT_MINUTES, "minute");
      return !slotEnd.isAfter(now) || bookingRangeOverlaps(intervals, spaceId, slotStart, slotEnd);
    });
  };

  return { disabledHours, disabledMinutes };
}
