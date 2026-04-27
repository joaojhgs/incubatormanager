"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  archiveCompany,
  getCompany,
  listCompanies,
  type CompanyListParams,
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

// ---------------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------------

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
