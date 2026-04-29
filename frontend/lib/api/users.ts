/**
 * Auth service — Director-scoped user directory (`GET /auth/users/`, `POST /auth/users/`).
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

/** Values accepted by `POST /api/auth/users/` (`UserCreateSerializer` in auth-service). */
export type UserCreateRole = "Director" | "Staff" | "Client";

export interface UserCreatePayload {
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  role: UserCreateRole;
  /** Required when `role` is `Client`; must be omitted or null for other roles. */
  company_id?: string | null;
}

/** List all incubator users (Director role only; others receive 403 from the API). */
export async function listUsers(): Promise<UserRead[]> {
  const { data } = await api().get<UserRead[]>("/auth/users/");
  return data;
}

/** Create a user account (Director only). */
export async function createUser(payload: UserCreatePayload): Promise<UserRead> {
  const { data } = await api().post<UserRead>("/auth/users/", payload);
  return data;
}
