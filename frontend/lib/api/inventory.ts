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
  rental_cost_unit: "hour" | "day" | "fixed";
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

export interface EquipmentTypePayload {
  name: string;
  is_active?: boolean;
}

export interface EquipmentCreatePayload {
  name: string;
  equipment_type: string;
  serial_number?: string;
  assigned_space_id?: string | null;
  rental_cost?: string | null;
  rental_cost_unit?: "hour" | "day" | "fixed";
  status?: string;
  notes?: string;
  is_active?: boolean;
}

export type EquipmentUpdatePayload = Partial<EquipmentCreatePayload>;

export interface EquipmentAssignPayload {
  booking_id?: string;
  company_id?: string;
  assigned_space_id?: string | null;
}

export interface EquipmentReleasePayload {
  booking_id: string;
}

const api = getDefaultApiClient;

export async function listEquipment(): Promise<Equipment[]> {
  const { data } = await api().get<Equipment[]>("/inventory/equipment/");
  return data;
}

export async function listPublicEquipment(): Promise<Equipment[]> {
  const { data } = await api().get<Equipment[]>("/public/inventory/equipment/");
  return data;
}

export async function listEquipmentTypes(): Promise<EquipmentType[]> {
  const { data } = await api().get<EquipmentType[]>("/inventory/equipment-types/");
  return data;
}

export async function createEquipmentType(payload: EquipmentTypePayload): Promise<EquipmentType> {
  const { data } = await api().post<EquipmentType>("/inventory/equipment-types/", payload);
  return data;
}

export async function updateEquipmentType(
  equipmentTypeId: string,
  payload: Partial<EquipmentTypePayload>,
): Promise<EquipmentType> {
  const { data } = await api().patch<EquipmentType>(
    `/inventory/equipment-types/${equipmentTypeId}/`,
    payload,
  );
  return data;
}

export async function deleteEquipmentType(equipmentTypeId: string): Promise<void> {
  await api().delete(`/inventory/equipment-types/${equipmentTypeId}/`);
}

export async function createEquipment(payload: EquipmentCreatePayload): Promise<Equipment> {
  const { data } = await api().post<Equipment>("/inventory/equipment/", payload);
  return data;
}

export async function updateEquipment(
  equipmentId: string,
  payload: EquipmentUpdatePayload,
): Promise<Equipment> {
  const { data } = await api().patch<Equipment>(`/inventory/equipment/${equipmentId}/`, payload);
  return data;
}

export async function deleteEquipment(equipmentId: string): Promise<void> {
  await api().delete(`/inventory/equipment/${equipmentId}/`);
}

export async function assignEquipment(
  equipmentId: string,
  payload: EquipmentAssignPayload,
): Promise<Equipment> {
  const { data } = await api().post<Equipment>(
    `/inventory/equipment/${equipmentId}/assign/`,
    payload,
  );
  return data;
}

export async function releaseEquipment(
  equipmentId: string,
  payload: EquipmentReleasePayload,
): Promise<Equipment> {
  const { data } = await api().post<Equipment>(
    `/inventory/equipment/${equipmentId}/release/`,
    payload,
  );
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
