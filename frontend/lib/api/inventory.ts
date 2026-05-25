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
  assigned_space_id: string | null;
  rental_cost: string | null;
  status: string;
  notes: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface EquipmentAssignment {
  id: string;
  equipment_id: string;
  equipment_name: string;
  booking_id: string;
  company_id: string;
  assigned_space_id: string | null;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface EquipmentAssignmentFilters {
  bookingId?: string;
  equipmentId?: string;
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

export async function listEquipmentAssignments(
  filters: EquipmentAssignmentFilters = {},
): Promise<EquipmentAssignment[]> {
  const { data } = await api().get<EquipmentAssignment[]>("/inventory/assignments/", {
    params: {
      ...(filters.bookingId ? { booking: filters.bookingId } : {}),
      ...(filters.equipmentId ? { equipment: filters.equipmentId } : {}),
    },
  });
  return data;
}
