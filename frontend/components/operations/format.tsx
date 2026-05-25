import { Tag } from "antd";

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-PT", { dateStyle: "short", timeStyle: "short" });
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-PT");
}

export function formatCurrency(value: string | number | null | undefined): string {
  const amount = Number(value ?? 0);
  return new Intl.NumberFormat("pt-PT", { style: "currency", currency: "EUR" }).format(amount);
}

export function statusTag(status: string) {
  const normalized = status.toLowerCase();
  const color = normalized.includes("active") || normalized.includes("approved") || normalized.includes("paid")
    ? "green"
    : normalized.includes("pending")
      ? "gold"
      : normalized.includes("overdue") || normalized.includes("rejected")
        ? "red"
        : normalized.includes("cancel") || normalized.includes("closed")
          ? "default"
          : normalized.includes("use") || normalized.includes("occupied") || normalized.includes("reserved")
            ? "blue"
            : "default";
  return <Tag color={color}>{status}</Tag>;
}
