/**
 * Auth service — Director-scoped user directory (`GET /auth/users/`).
 */

import { getDefaultApiClient } from "./client";

const api = getDefaultApiClient;

/** Row shape from `GET /api/auth/users/` (see `services/auth-service/schema.yml` — `UserRead`). */
export interface UserRead {
  id: string;
  email: string;
  role: string;
  first_name: string;
  last_name: string;
  company_id: string | null;
  is_active: boolean;
}

/** List all incubator users (Director role only; others receive 403 from the API). */
export async function listUsers(): Promise<UserRead[]> {
  const { data } = await api().get<UserRead[]>("/auth/users/");
  return data;
}
