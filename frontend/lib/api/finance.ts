import { getDefaultApiClient } from "./client";

export interface Payment {
  id: string;
  company_id: string;
  contract_id: string | null;
  booking_id: string | null;
  source: string;
  amount: string;
  currency: string;
  status: string;
  due_date: string | null;
  paid_at: string | null;
  period_start: string | null;
  period_end: string | null;
  reference_id: string;
  created_at: string;
  updated_at: string;
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
}

const api = getDefaultApiClient;

export async function listPayments(): Promise<Payment[]> {
  const { data } = await api().get<Payment[]>("/finance/payments/");
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
