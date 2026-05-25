"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  archiveCompany,
  createCompany,
  getCompany,
  getCompanyStats,
  listCAECodes,
  listCompanies,
  listMaturityStages,
  updateCompany,
  type CompanyCreatePayload,
  type CompanyListParams,
  type CompanyUpdatePayload,
} from "@/lib/api/companies";
import { message } from "antd";
import { tCompany } from "@/lib/i18n/companies";

// ---------------------------------------------------------------------------
// Query keys
// ---------------------------------------------------------------------------

export const companyKeys = {
  all: ["companies"] as const,
  lists: () => [...companyKeys.all, "list"] as const,
  list: (params?: CompanyListParams) => [...companyKeys.lists(), params] as const,
  details: () => [...companyKeys.all, "detail"] as const,
  detail: (id: string) => [...companyKeys.details(), id] as const,
  cae: () => [...companyKeys.all, "cae"] as const,
  maturityStages: () => [...companyKeys.all, "maturityStages"] as const,
  stats: () => [...companyKeys.all, "stats"] as const,
};

// ---------------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------------

/** Fetch a paginated, filterable list of companies. */
export function useCompanies(params?: CompanyListParams) {
  return useQuery({
    queryKey: companyKeys.list(params),
    queryFn: () => listCompanies(params),
  });
}

/** Fetch a single company by ID. */
export function useCompany(id: string) {
  return useQuery({
    queryKey: companyKeys.detail(id),
    queryFn: () => getCompany(id),
    enabled: Boolean(id),
  });
}

export function useCAECodes() {
  return useQuery({
    queryKey: companyKeys.cae(),
    queryFn: listCAECodes,
    staleTime: 60_000,
  });
}

export function useMaturityStages() {
  return useQuery({
    queryKey: companyKeys.maturityStages(),
    queryFn: listMaturityStages,
    staleTime: 60_000,
  });
}

export function useCompanyStats() {
  return useQuery({
    queryKey: companyKeys.stats(),
    queryFn: getCompanyStats,
    staleTime: 30_000,
  });
}

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

export function useCreateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: CompanyCreatePayload) => createCompany(payload),
    onSuccess: (company) => {
      void queryClient.invalidateQueries({ queryKey: companyKeys.all });
      message.success(tCompany("formCreateSuccess"));
      return company;
    },
    onError: () => {
      message.error(tCompany("formSaveError"));
    },
  });
}

export function useUpdateCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, payload }: { id: string; payload: CompanyUpdatePayload }) =>
      updateCompany(id, payload),
    onSuccess: (company, variables) => {
      void queryClient.invalidateQueries({ queryKey: companyKeys.all });
      void queryClient.invalidateQueries({ queryKey: companyKeys.detail(variables.id) });
      message.success(tCompany("formUpdateSuccess"));
      return company;
    },
    onError: () => {
      message.error(tCompany("formSaveError"));
    },
  });
}

/** Archive (soft-delete) a company. */
export function useArchiveCompany() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: archiveCompany,
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: companyKeys.all });
      message.success(tCompany("listArchiveSuccess"));
    },
    onError: () => {
      message.error(tCompany("listArchiveError"));
    },
  });
}
