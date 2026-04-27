/**
 * Company Service API client.
 *
 * Endpoints (proxied through Nginx gateway):
 *   GET    /companies              — list companies (filterable)
 *   POST   /companies              — register a new company
 *   GET    /companies/:id          — get company profile
 *   PATCH  /companies/:id          — update company profile
 *   PATCH  /companies/:id/maturity-stage — change maturity stage
 *   DELETE /companies/:id          — archive/deactivate company
 *   GET    /companies/:id/employees — list employees
 *   POST   /companies/:id/employees — add employee
 *   GET    /cae                    — list CAE codes
 *   GET    /maturity-stages        — list maturity stages with rates
 */

import { getDefaultApiClient } from "./client";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface MaturityStage {
  id: string;
  name: string;
  rate_per_sqm: number;
  description: string;
  display_order: number;
}

export interface CAECode {
  id: string;
  code: string;
  description: string;
}

export interface Company {
  id: string;
  name: string;
  tax_id: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  legal_representative: string;
  cae_id: string;
  cae_description?: string;
  maturity_stage_id: string;
  maturity_stage_name?: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyListParams {
  page?: number;
  page_size?: number;
  search?: string;
  is_active?: boolean;
  maturity_stage_id?: string;
  cae_id?: string;
  ordering?: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CompanyCreatePayload {
  name: string;
  tax_id: string;
  legal_representative: string;
  cae_id: string;
  maturity_stage_id: string;
  address?: string;
  phone?: string;
  email?: string;
  description?: string;
}

export interface CompanyUpdatePayload {
  name?: string;
  address?: string;
  phone?: string;
  email?: string;
  legal_representative?: string;
  cae_id?: string;
  maturity_stage_id?: string;
  description?: string;
}

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

// Store the factory function reference — getDefaultApiClient() returns a
// lazily-created singleton AxiosInstance, so calling api() each time is
// equivalent to importing and calling getDefaultApiClient() directly.
const api = getDefaultApiClient;

/** List companies with optional filters. */
export async function listCompanies(
  params?: CompanyListParams,
): Promise<PaginatedResponse<Company>> {
  const { data } = await api().get<PaginatedResponse<Company>>("/companies", {
    params,
  });
  return data;
}

/** Get a single company by ID. */
export async function getCompany(id: string): Promise<Company> {
  const { data } = await api().get<Company>(`/companies/${id}`);
  return data;
}

/** Register a new company. */
export async function createCompany(payload: CompanyCreatePayload): Promise<Company> {
  const { data } = await api().post<Company>("/companies", payload);
  return data;
}

/** Update company profile fields. */
export async function updateCompany(id: string, payload: CompanyUpdatePayload): Promise<Company> {
  const { data } = await api().patch<Company>(`/companies/${id}`, payload);
  return data;
}

/** Archive (soft-delete) a company. */
export async function archiveCompany(id: string): Promise<void> {
  await api().delete(`/companies/${id}`);
}

/** Change a company's maturity stage. */
export async function changeMaturityStage(id: string, maturityStageId: string): Promise<Company> {
  const { data } = await api().patch<Company>(`/companies/${id}/maturity-stage`, {
    maturity_stage_id: maturityStageId,
  });
  return data;
}

/** List all CAE codes. */
export async function listCAECodes(): Promise<CAECode[]> {
  const { data } = await api().get<CAECode[]>("/cae");
  return data;
}

/** List all maturity stages. */
export async function listMaturityStages(): Promise<MaturityStage[]> {
  const { data } = await api().get<MaturityStage[]>("/maturity-stages");
  return data;
}
