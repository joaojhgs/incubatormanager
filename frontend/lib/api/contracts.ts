import { getDefaultApiClient } from "./client";

export interface Contract {
  id: string;
  company_id: string;
  space_id: string;
  status: string;
  area_sqm: string;
  rate_per_sqm: string;
  monthly_fee: string;
  start_date: string;
  end_date: string;
  termination_reason: string;
  created_at: string;
  updated_at: string;
}

const api = getDefaultApiClient;

export async function listContracts(): Promise<Contract[]> {
  const { data } = await api().get<Contract[]>("/contracts/");
  return data;
}

export async function listCompanyContracts(companyId: string): Promise<Contract[]> {
  const { data } = await api().get<Contract[]>(`/contracts/company/${companyId}/`);
  return data;
}
