import { getDefaultApiClient } from "./client";

export interface Space {
  id: string;
  name: string;
  space_type: string | null;
  capacity: number;
  rental_cost: string | null;
  rental_cost_unit: "hour" | "day" | "fixed";
  status: string;
  company_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SpaceType {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface SpaceCreatePayload {
  name: string;
  space_type?: string | null;
  capacity: number;
  rental_cost?: string | null;
  rental_cost_unit?: "hour" | "day" | "fixed";
  status?: string;
  company_id?: string | null;
  is_active?: boolean;
}

export type SpaceUpdatePayload = Partial<SpaceCreatePayload>;

export interface SpaceTypePayload {
  name: string;
  is_active?: boolean;
}

export interface SpaceOccupancy {
  space_id: string;
  space_name: string;
  capacity: number;
  occupied: number;
  occupancy_percent: string;
  status: string;
}

export interface SpaceBookingRecord {
  id: string;
  space_id: string;
  company_id: string;
  status: string;
  start_time: string | null;
  end_time: string | null;
  quoted_price: string | null;
  equipment_ids: string[];
}

const api = getDefaultApiClient;

export async function listSpaces(): Promise<Space[]> {
  const { data } = await api().get<Space[]>("/spaces/");
  return data;
}

export async function listPublicSpaces(): Promise<Space[]> {
  const { data } = await api().get<Space[]>("/public/spaces/");
  return data;
}

export async function createSpace(payload: SpaceCreatePayload): Promise<Space> {
  const { data } = await api().post<Space>("/spaces/", payload);
  return data;
}

export async function updateSpace(spaceId: string, payload: SpaceUpdatePayload): Promise<Space> {
  const { data } = await api().patch<Space>(`/spaces/${spaceId}/`, payload);
  return data;
}

export async function deleteSpace(spaceId: string): Promise<void> {
  await api().delete(`/spaces/${spaceId}/`);
}

export async function listSpaceTypes(): Promise<SpaceType[]> {
  const { data } = await api().get<SpaceType[]>("/space-types/");
  return data;
}

export async function createSpaceType(payload: SpaceTypePayload): Promise<SpaceType> {
  const { data } = await api().post<SpaceType>("/space-types/", payload);
  return data;
}

export async function updateSpaceType(
  spaceTypeId: string,
  payload: Partial<SpaceTypePayload>,
): Promise<SpaceType> {
  const { data } = await api().patch<SpaceType>(`/space-types/${spaceTypeId}/`, payload);
  return data;
}

export async function deleteSpaceType(spaceTypeId: string): Promise<void> {
  await api().delete(`/space-types/${spaceTypeId}/`);
}

export async function listSpaceOccupancy(): Promise<SpaceOccupancy[]> {
  const { data } = await api().get<SpaceOccupancy[]>("/spaces/occupancy-map/");
  return data;
}

export async function listSpaceBookingRecords(): Promise<SpaceBookingRecord[]> {
  const { data } = await api().get<SpaceBookingRecord[]>("/spaces/bookings/records/");
  return data;
}
