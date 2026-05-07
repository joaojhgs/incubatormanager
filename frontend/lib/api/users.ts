/**
 * Auth service — Director-scoped user directory (`GET|POST /auth/users/`,
 * `GET|PATCH|DELETE /auth/users/{id}/`).
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

/** API role values accepted by `PATCH /auth/users/{id}/` (see auth-service `RoleEnum`). */
export type UserAdminRole = "Director" | "Staff" | "Client";

/** Writable fields for Director `PATCH /auth/users/{id}/` (partial). */
export interface UserUpdatePayload {
  first_name?: string;
  last_name?: string;
  role?: UserAdminRole;
  company_id?: string | null;
  is_active?: boolean;
  /** When set, replaces the password (Director-only reset; omitted to leave unchanged). */
  password?: string;
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

/** Load a single user by id (Director only). */
export async function getUserById(userId: string): Promise<UserRead> {
  const { data } = await api().get<UserRead>(`/auth/users/${encodeURIComponent(userId)}/`);
  return data;
}

/** Partially update a user (Director only). */
export async function updateUser(userId: string, payload: UserUpdatePayload): Promise<UserRead> {
  const { data } = await api().patch<UserRead>(
    `/auth/users/${encodeURIComponent(userId)}/`,
    payload,
  );
  return data;
}

/** Soft-delete: sets `is_active` to false (Director only). `DELETE /auth/users/{id}/` → 204. */
export async function deactivateUser(userId: string): Promise<void> {
  await api().delete(`/auth/users/${encodeURIComponent(userId)}/`);
}
