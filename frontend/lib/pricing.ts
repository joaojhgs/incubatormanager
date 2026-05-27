export type RentalCostUnit = "hour" | "day" | "fixed";

export interface PricedItem {
  rental_cost?: string | number | null;
  rental_cost_unit?: RentalCostUnit | string | null;
}

const currencyFormatter = new Intl.NumberFormat("pt-PT", {
  style: "currency",
  currency: "EUR",
  minimumFractionDigits: 2,
});

export function parseMoney(value: string | number | null | undefined): number {
  const parsed = Number(value ?? 0);
  return Number.isFinite(parsed) ? parsed : 0;
}

export function formatMoney(value: string | number | null | undefined): string {
  return currencyFormatter.format(parseMoney(value));
}

export function unitLabel(unit: string | null | undefined): string {
  if (unit === "day") return "dia";
  if (unit === "fixed") return "reserva";
  return "hora";
}

export function rateLabel(item: PricedItem | undefined): string {
  const amount = parseMoney(item?.rental_cost);
  if (amount <= 0) return "sem custo";
  return `${formatMoney(amount)}/${unitLabel(item?.rental_cost_unit)}`;
}

export function durationHours<
  T extends {
    diff: (other: T, unit: "minute") => number;
    isAfter: (other: T) => boolean;
  },
>(start: T | undefined, end: T | undefined): number {
  if (!start || !end || !end.isAfter(start)) return 0;
  return Math.round((end.diff(start, "minute") / 60) * 100) / 100;
}

export function calculateItemCost(item: PricedItem | undefined, hours: number): number {
  const amount = parseMoney(item?.rental_cost);
  if (amount <= 0 || hours <= 0) return 0;
  if (item?.rental_cost_unit === "fixed") return amount;
  if (item?.rental_cost_unit === "day") return amount * Math.max(1, Math.ceil(hours / 24));
  return amount * hours;
}

export function calculateRentalEstimate(
  space: PricedItem | undefined,
  equipment: PricedItem[],
  hours: number,
): { spaceCost: number; equipmentCost: number; total: number } {
  const spaceCost = calculateItemCost(space, hours);
  const equipmentCost = equipment.reduce(
    (total, item) => total + calculateItemCost(item, hours),
    0,
  );
  return { spaceCost, equipmentCost, total: Math.round((spaceCost + equipmentCost) * 100) / 100 };
}
