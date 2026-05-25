import { getDefaultApiClient } from "./client";

export type PaymentStatus = "pending" | "paid" | "overdue";
export type PaymentSource = "contract" | "booking";
export type PaymentType = "monthly" | "rental";

export interface Payment {
  id: string;
  company_id: string;
  contract_id: string | null;
  booking_id: string | null;
  source: PaymentSource | string;
  payment_type: PaymentType | string;
  amount: string;
  currency: string;
  status: PaymentStatus | string;
  due_date: string | null;
  paid_at: string | null;
  period_start: string | null;
  period_end: string | null;
  reference_id: string;
  created_at: string;
  updated_at: string;
}

export interface FinanceBreakdownRow {
  count: number;
  amount: string;
  status?: string;
  source?: string;
  payment_type?: string;
  sector?: string;
}

export interface FinanceDashboard {
  total_payments: number;
  total_amount: string;
  paid: number;
  paid_amount: string;
  pending: number;
  pending_amount: string;
  overdue: number;
  overdue_amount: string;
  status_breakdown?: FinanceBreakdownRow[];
  source_breakdown?: FinanceBreakdownRow[];
  payment_type_breakdown?: FinanceBreakdownRow[];
  by_sector?: FinanceBreakdownRow[];
}

export interface PaymentListFilters {
  status?: PaymentStatus;
  source?: PaymentSource;
  payment_type?: PaymentType;
  company_id?: string;
  date_from?: string;
  date_to?: string;
}

export type FinanceReportType =
  | "revenue_by_company"
  | "revenue_by_maturity"
  | "payment_status_summary"
  | "cash_flow_trend";

export type FinanceReportGroupBy = "day" | "month";

export interface FinanceReportFilters {
  type?: FinanceReportType;
  group_by?: FinanceReportGroupBy;
  date_from?: string;
  date_to?: string;
}

export interface FinanceReportRow {
  [key: string]: string | number | null | undefined;
}

export interface FinanceReportResponse {
  type: FinanceReportType;
  group_by?: FinanceReportGroupBy;
  results: FinanceReportRow[];
}

export interface NextDuePayment {
  payment_id: string | null;
  company_id: string | null;
  due_date: string | null;
  amount: string | null;
  status: string;
  source: string;
  payment_type: string;
}

export interface PaymentPatchPayload {
  status: PaymentStatus;
  paid_at?: string | null;
  reference_id?: string;
}

const api = getDefaultApiClient;

export async function listPayments(filters?: PaymentListFilters): Promise<Payment[]> {
  const { data } = await api().get<Payment[]>("/finance/payments/", { params: filters });
  return data;
}

export async function listCompanyPayments(companyId: string): Promise<Payment[]> {
  const { data } = await api().get<Payment[]>(`/finance/payments/company/${companyId}/`);
  return data;
}

export async function getFinanceDashboard(): Promise<FinanceDashboard> {
  const { data } = await api().get<FinanceDashboard>("/finance/dashboard/");
  return data;
}

export async function getFinanceReport(
  filters?: FinanceReportFilters,
): Promise<FinanceReportResponse> {
  const { data } = await api().get<FinanceReportResponse>("/finance/reports/", {
    params: filters,
  });
  return data;
}

export async function getNextDuePayment(): Promise<NextDuePayment> {
  const { data } = await api().get<NextDuePayment>("/finance/payments/next-due/");
  return data;
}

export async function updatePayment(
  paymentId: string,
  payload: PaymentPatchPayload,
): Promise<Payment> {
  const { data } = await api().patch<Payment>(`/finance/payments/${paymentId}/`, payload);
  return data;
}
