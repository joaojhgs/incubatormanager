"use client";

import { useQuery } from "@tanstack/react-query";

import { getServiceHealth, type ServiceHealthDomain } from "@/lib/api/serviceHealth";

export const serviceHealthKeys = {
  all: ["serviceHealth"] as const,
  domain: (domain: ServiceHealthDomain) => [...serviceHealthKeys.all, domain] as const,
};

export function useServiceHealth(domain: ServiceHealthDomain) {
  return useQuery({
    queryKey: serviceHealthKeys.domain(domain),
    queryFn: () => getServiceHealth(domain),
    staleTime: 30_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}
