import { getDefaultApiClient } from "./client";

export interface Space {
  id: string;
  name: string;
  space_type: string | null;
  capacity: number;
  status: string;
  company_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
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

export async function listSpaceOccupancy(): Promise<SpaceOccupancy[]> {
  const { data } = await api().get<SpaceOccupancy[]>("/spaces/occupancy-map/");
  return data;
}

export async function listSpaceBookingRecords(): Promise<SpaceBookingRecord[]> {
  const { data } = await api().get<SpaceBookingRecord[]>("/spaces/bookings/records/");
  return data;
}
