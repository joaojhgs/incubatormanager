import { getDefaultApiClient } from "./client";

/** Domain health payload returned by service `/health/` endpoints. */
export interface ServiceHealth {
  status: string;
}

export const SERVICE_HEALTH_DOMAINS = {
  contracts: "/contracts/health/",
  finance: "/finance/health/",
  spaces: "/spaces/health/",
  bookings: "/bookings/health/",
  inventory: "/inventory/health/",
  dashboard: "/dashboard/health/",
} as const;

export type ServiceHealthDomain = keyof typeof SERVICE_HEALTH_DOMAINS;

const api = getDefaultApiClient;

export async function getServiceHealth(domain: ServiceHealthDomain): Promise<ServiceHealth> {
  const { data } = await api().get<ServiceHealth>(SERVICE_HEALTH_DOMAINS[domain]);
  return data;
}
