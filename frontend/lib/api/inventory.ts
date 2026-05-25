import { getDefaultApiClient } from "./client";

export interface EquipmentType {
  id: string;
  name: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Equipment {
  id: string;
  name: string;
  equipment_type: string;
  serial_number: string;
  status: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const api = getDefaultApiClient;

export async function listEquipment(): Promise<Equipment[]> {
  const { data } = await api().get<Equipment[]>("/inventory/equipment/");
  return data;
}

export async function listEquipmentTypes(): Promise<EquipmentType[]> {
  const { data } = await api().get<EquipmentType[]>("/inventory/equipment-types/");
  return data;
}

export async function listMyAssignedEquipment(bookingId?: string): Promise<Equipment[]> {
  const { data } = await api().get<Equipment[]>("/inventory/my-assignments/", {
    params: bookingId ? { booking: bookingId } : undefined,
  });
  return data;
}
