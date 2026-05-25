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

export interface ContractCreatePayload {
  company_id: string;
  space_id: string;
  area_sqm: string;
  rate_per_sqm: string;
  start_date: string;
  end_date: string;
}

export type ContractUpdatePayload = Partial<ContractCreatePayload> & {
  status?: string;
};

export interface ContractTerminatePayload {
  reason?: string;
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

export async function createContract(payload: ContractCreatePayload): Promise<Contract> {
  const { data } = await api().post<Contract>("/contracts/", payload);
  return data;
}

export async function updateContract(
  contractId: string,
  payload: ContractUpdatePayload,
): Promise<Contract> {
  const { data } = await api().patch<Contract>(`/contracts/${contractId}/`, payload);
  return data;
}

export async function deleteContract(contractId: string): Promise<void> {
  await api().delete(`/contracts/${contractId}/`);
}

export async function activateContract(contractId: string): Promise<Contract> {
  const { data } = await api().patch<Contract>(`/contracts/${contractId}/activate/`);
  return data;
}

export async function terminateContract(
  contractId: string,
  payload: ContractTerminatePayload = {},
): Promise<Contract> {
  const { data } = await api().patch<Contract>(`/contracts/${contractId}/terminate/`, payload);
  return data;
}
