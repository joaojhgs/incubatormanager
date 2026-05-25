import { Tag } from "antd";

import { normalizeStatus, statusLabel } from "@/lib/i18n/status";

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

const positiveStatuses = new Set(["active", "approved", "paid", "resolved", "completed"]);
const warningStatuses = new Set(["pending", "draft", "waiting response"]);
const dangerStatuses = new Set([
  "overdue",
  "rejected",
  "maintenance",
  "blocked",
  "terminated",
  "expired",
]);
const neutralStatuses = new Set(["cancelled", "canceled", "closed", "inactive", "released"]);
const progressStatuses = new Set(["in use", "occupied", "reserved", "assigned", "in progress"]);

export function statusColor(status: string): string {
  const normalized = normalizeStatus(status);
  if (positiveStatuses.has(normalized)) return "green";
  if (warningStatuses.has(normalized)) return "gold";
  if (dangerStatuses.has(normalized)) return "red";
  if (progressStatuses.has(normalized)) return "blue";
  if (neutralStatuses.has(normalized)) return "default";
  return "default";
}

export function statusTag(status: string) {
  return <Tag color={statusColor(status)}>{statusLabel(status)}</Tag>;
}
