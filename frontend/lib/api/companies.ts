/**
 * Company Service API client.
 *
 * Endpoints (proxied through Nginx gateway):
 *   GET    /companies/              — list companies (filterable)
 *   POST   /companies/              — register a new company
 *   GET    /companies/:id/          — get company profile
 *   PATCH  /companies/:id/          — update company profile
 *   PATCH  /companies/:id/maturity-stage/ — change maturity stage
 *   DELETE /companies/:id/          — archive/deactivate company
 *   GET    /companies/:id/employees/ — list employees
 *   POST   /companies/:id/employees/ — add employee
 *   GET    /companies/cae/          — list CAE codes
 *   GET    /companies/maturity-stages/ — list maturity stages with rates
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

export interface Employee {
  id: string;
  name: string;
  type: string;
  start_date: string;
  end_date: string | null;
  is_active: boolean;
}

export interface EmployeePayload {
  name: string;
  type: string;
  start_date: string;
  end_date?: string | null;
  is_active: boolean;
}

export interface CompanyStats {
  total: number;
  active: number;
  inactive: number;
  by_maturity: Record<string, number>;
  by_cae: Record<string, number>;
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
  cae?: CAECode;
  maturity_stage_id: string;
  maturity_stage_name?: string;
  maturity_stage?: MaturityStage;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface CompanyDetail extends Company {
  employees: Employee[];
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

interface CompanyApiPayload {
  id: string;
  name: string;
  tax_id: string;
  address: string | null;
  phone: string | null;
  email: string | null;
  legal_representative: string;
  description: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  cae?: CAECode;
  maturity_stage?: MaturityStage;
  employees?: Employee[];
}

type CompanyWriteApiPayload = Omit<CompanyCreatePayload, "cae_id" | "maturity_stage_id"> & {
  cae: string;
  maturity_stage: string;
};

type CompanyPatchApiPayload = Partial<CompanyWriteApiPayload>;

// ---------------------------------------------------------------------------
// API functions
// ---------------------------------------------------------------------------

const api = getDefaultApiClient;

function normalizeCompany<T extends CompanyApiPayload>(raw: T): Company & Pick<T, "employees"> {
  return {
    ...raw,
    cae_id: raw.cae?.id ?? "",
    cae_description: raw.cae ? `${raw.cae.code} — ${raw.cae.description}` : undefined,
    maturity_stage_id: raw.maturity_stage?.id ?? "",
    maturity_stage_name: raw.maturity_stage?.name,
  };
}

function normalizeCompanyPage(
  page: PaginatedResponse<CompanyApiPayload>,
): PaginatedResponse<Company> {
  return { ...page, results: page.results.map((row) => normalizeCompany(row)) };
}

function toBackendListParams(params?: CompanyListParams): Record<string, unknown> | undefined {
  if (!params) return undefined;
  const { cae_id, maturity_stage_id, ...rest } = params;
  return {
    ...rest,
    ...(cae_id ? { cae: cae_id } : {}),
    ...(maturity_stage_id ? { maturity: maturity_stage_id } : {}),
  };
}

function toBackendCreatePayload(payload: CompanyCreatePayload): CompanyWriteApiPayload {
  const { cae_id, maturity_stage_id, ...rest } = payload;
  return { ...rest, cae: cae_id, maturity_stage: maturity_stage_id };
}

function toBackendUpdatePayload(payload: CompanyUpdatePayload): CompanyPatchApiPayload {
  const { cae_id, maturity_stage_id, ...rest } = payload;
  return {
    ...rest,
    ...(cae_id ? { cae: cae_id } : {}),
    ...(maturity_stage_id ? { maturity_stage: maturity_stage_id } : {}),
  };
}

/** List companies with optional filters. */
export async function listCompanies(
  params?: CompanyListParams,
): Promise<PaginatedResponse<Company>> {
  const { data } = await api().get<PaginatedResponse<CompanyApiPayload>>("/companies/", {
    params: toBackendListParams(params),
  });
  return normalizeCompanyPage(data);
}

/** Get a single company by ID. */
export async function getCompany(id: string): Promise<CompanyDetail> {
  const { data } = await api().get<CompanyApiPayload>(`/companies/${encodeURIComponent(id)}/`);
  return normalizeCompany(data) as CompanyDetail;
}

/** Register a new company. */
export async function createCompany(payload: CompanyCreatePayload): Promise<Company> {
  const { data } = await api().post<CompanyApiPayload>(
    "/companies/",
    toBackendCreatePayload(payload),
  );
  return normalizeCompany(data);
}

/** Update company profile fields. */
export async function updateCompany(id: string, payload: CompanyUpdatePayload): Promise<Company> {
  const { data } = await api().patch<CompanyApiPayload>(
    `/companies/${encodeURIComponent(id)}/`,
    toBackendUpdatePayload(payload),
  );
  return normalizeCompany(data);
}

/** Archive (soft-delete) a company. */
export async function archiveCompany(id: string): Promise<void> {
  await api().delete(`/companies/${encodeURIComponent(id)}/`);
}

/** Change a company's maturity stage. */
export async function changeMaturityStage(id: string, maturityStageId: string): Promise<Company> {
  const { data } = await api().patch<CompanyApiPayload>(
    `/companies/${encodeURIComponent(id)}/maturity-stage/`,
    { maturity_stage: maturityStageId },
  );
  return normalizeCompany(data);
}

/** List all employees for one company. */
export async function listCompanyEmployees(companyId: string): Promise<Employee[]> {
  const { data } = await api().get<Employee[]>(
    `/companies/${encodeURIComponent(companyId)}/employees/`,
  );
  return data;
}

/** Add an employee to a company. */
export async function createCompanyEmployee(
  companyId: string,
  payload: EmployeePayload,
): Promise<Employee> {
  const { data } = await api().post<Employee>(
    `/companies/${encodeURIComponent(companyId)}/employees/`,
    payload,
  );
  return data;
}

/** Update one company employee. */
export async function updateCompanyEmployee(
  companyId: string,
  employeeId: string,
  payload: EmployeePayload,
): Promise<Employee> {
  const { data } = await api().patch<Employee>(
    `/companies/${encodeURIComponent(companyId)}/employees/${encodeURIComponent(employeeId)}/`,
    payload,
  );
  return data;
}

/** Remove one company employee. */
export async function deleteCompanyEmployee(companyId: string, employeeId: string): Promise<void> {
  await api().delete(
    `/companies/${encodeURIComponent(companyId)}/employees/${encodeURIComponent(employeeId)}/`,
  );
}

/** Company-level aggregate statistics. */
export async function getCompanyStats(): Promise<CompanyStats> {
  const { data } = await api().get<CompanyStats>("/companies/stats/");
  return data;
}

/** List all CAE codes. */
export async function listCAECodes(): Promise<CAECode[]> {
  const { data } = await api().get<CAECode[]>("/companies/cae/");
  return data;
}

/** List all maturity stages. */
export async function listMaturityStages(): Promise<MaturityStage[]> {
  const { data } = await api().get<MaturityStage[]>("/companies/maturity-stages/");
  return data;
}
