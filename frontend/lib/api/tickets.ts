import { getDefaultApiClient } from "./client";

/** Ticket record returned by ticket service list endpoints. */
export interface Ticket {
  id: string;
  company_id: string;
  subject: string;
  description: string;
  status: string;
  created_by_user_id: string;
  created_by_role: string;
  created_at: string;
  updated_at: string;
}

const api = getDefaultApiClient;

/** List all tickets visible to the authenticated caller (staff or scoped client). */
export async function listTickets(): Promise<Ticket[]> {
  const { data } = await api().get<Ticket[]>("/tickets/");
  return data;
}

/** List tickets owned by the authenticated client company (`X-Company-Id` scope). */
export async function listMyTickets(): Promise<Ticket[]> {
  const { data } = await api().get<Ticket[]>("/tickets/my/");
  return data;
}
