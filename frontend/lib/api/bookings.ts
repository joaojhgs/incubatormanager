import { getDefaultApiClient } from "./client";

export interface Booking {
  id: string;
  company_id: string;
  space_id: string;
  created_by_user_id: string | null;
  created_by_role: string;
  is_public: boolean;
  requester_name: string;
  requester_email: string;
  requester_phone: string;
  start_time: string;
  end_time: string;
  quoted_price: string;
  equipment_ids: string[];
  status: string;
  notes: string;
  created_at: string;
  updated_at: string;
}

export interface BookingCreatePayload {
  company_id?: string;
  space_id: string;
  requester_name?: string;
  requester_email?: string;
  requester_phone?: string;
  start_time: string;
  end_time: string;
  quoted_price: string;
  equipment_ids?: string[];
  notes?: string;
}

const api = getDefaultApiClient;

export async function listBookings(): Promise<Booking[]> {
  const { data } = await api().get<Booking[]>("/bookings/");
  return data;
}

export async function listMyBookings(): Promise<Booking[]> {
  const { data } = await api().get<Booking[]>("/bookings/my/");
  return data;
}

export async function createBooking(payload: BookingCreatePayload): Promise<Booking> {
  const { data } = await api().post<Booking>("/bookings/", payload);
  return data;
}

export async function createPublicBooking(payload: BookingCreatePayload): Promise<Booking> {
  const { data } = await api().post<Booking>("/bookings/external/", payload);
  return data;
}

export async function approveBooking(id: string): Promise<Booking> {
  const { data } = await api().patch<Booking>(`/bookings/${id}/approve/`);
  return data;
}

export async function rejectBooking(id: string): Promise<Booking> {
  const { data } = await api().patch<Booking>(`/bookings/${id}/reject/`);
  return data;
}

export async function cancelBooking(id: string): Promise<Booking> {
  const { data } = await api().patch<Booking>(`/bookings/${id}/cancel/`);
  return data;
}
