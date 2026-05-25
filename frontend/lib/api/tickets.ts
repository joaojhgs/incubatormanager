import { getDefaultApiClient } from "./client";

/** Ticket record returned by ticket service list endpoints. */
export interface Ticket {
  id: string;
  company_id: string;
  subject: string;
  description: string;
  status: string;
  assigned_to: string | null;
  created_by_user_id: string;
  created_by_role: string;
  created_at: string;
  updated_at: string;
  messages: TicketMessage[];
}

export interface TicketMessage {
  id: string;
  author_user_id: string;
  author_role: string;
  content: string;
  created_at: string;
}

export interface TicketCreatePayload {
  company_id?: string;
  subject: string;
  description?: string;
}

export interface TicketMessageCreatePayload {
  content: string;
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

/** Create a support ticket. Client callers are scoped to their bound company by the API. */
export async function createTicket(payload: TicketCreatePayload): Promise<Ticket> {
  const { data } = await api().post<Ticket>("/tickets/", payload);
  return data;
}

/** Retrieve one ticket and its ordered message thread. */
export async function getTicket(ticketId: string): Promise<Ticket> {
  const { data } = await api().get<Ticket>(`/tickets/${ticketId}/`);
  return data;
}

/** Append a message to a ticket thread. */
export async function addTicketMessage(
  ticketId: string,
  payload: TicketMessageCreatePayload,
): Promise<TicketMessage> {
  const { data } = await api().post<TicketMessage>(`/tickets/${ticketId}/messages/`, payload);
  return data;
}
