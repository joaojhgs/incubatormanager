"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { message } from "antd";

import {
  approveBooking,
  cancelBooking,
  createBooking,
  createPublicBooking,
  listBookingCalendar,
  listBookings,
  listMyBookings,
  rejectBooking,
  type BookingApprovePayload,
  type BookingCreatePayload,
} from "@/lib/api/bookings";
import { listCompanyContracts, listContracts } from "@/lib/api/contracts";
import {
  getFinanceDashboard,
  getFinanceReport,
  getNextDuePayment,
  listCompanyPayments,
  listPayments,
  updatePayment,
  type FinanceReportFilters,
  type PaymentListFilters,
  type PaymentPatchPayload,
} from "@/lib/api/finance";
import {
  listEquipment,
  listEquipmentAssignments,
  listEquipmentTypes,
  listMyAssignedEquipment,
  type EquipmentAssignmentFilters,
} from "@/lib/api/inventory";
import { listSpaceBookingRecords, listSpaceOccupancy, listSpaces } from "@/lib/api/spaces";
import { tStaff } from "@/lib/i18n/staffNav";
import { tClient } from "@/lib/i18n/clientPortal";

export const operationalKeys = {
  bookings: ["bookings"] as const,
  bookingCalendar: ["bookings", "calendar"] as const,
  myBookings: ["bookings", "mine"] as const,
  contracts: ["contracts"] as const,
  companyContracts: (companyId: string) => ["contracts", "company", companyId] as const,
  dashboardFinance: ["finance", "dashboard"] as const,
  payments: (filters?: PaymentListFilters) => ["finance", "payments", filters ?? {}] as const,
  companyPayments: (companyId: string) => ["finance", "payments", "company", companyId] as const,
  financeReport: (filters?: FinanceReportFilters) => ["finance", "reports", filters ?? {}] as const,
  nextDuePayment: ["finance", "payments", "nextDue"] as const,
  equipment: ["inventory", "equipment"] as const,
  equipmentTypes: ["inventory", "equipmentTypes"] as const,
  equipmentAssignments: (filters?: EquipmentAssignmentFilters) =>
    ["inventory", "assignments", filters?.bookingId ?? null, filters?.equipmentId ?? null] as const,
  myAssignedEquipment: (bookingId?: string) => ["inventory", "myAssignments", bookingId] as const,
  spaces: ["spaces"] as const,
  occupancy: ["spaces", "occupancy"] as const,
  spaceBookingRecords: ["spaces", "bookings", "records"] as const,
};

export function useBookings() {
  return useQuery({ queryKey: operationalKeys.bookings, queryFn: listBookings, staleTime: 30_000 });
}

export function useBookingCalendar() {
  return useQuery({
    queryKey: operationalKeys.bookingCalendar,
    queryFn: listBookingCalendar,
    staleTime: 30_000,
  });
}

export function useMyBookings() {
  return useQuery({
    queryKey: operationalKeys.myBookings,
    queryFn: listMyBookings,
    staleTime: 30_000,
  });
}

export function useCreateBooking() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: BookingCreatePayload) => createBooking(payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: operationalKeys.myBookings });
      void queryClient.invalidateQueries({ queryKey: operationalKeys.bookings });
      message.success(tClient("bookingCreateSuccess"));
    },
    onError: () => message.error(tClient("bookingCreateError")),
  });
}

export function useCreatePublicBooking() {
  return useMutation({
    mutationFn: (payload: BookingCreatePayload) => createPublicBooking(payload),
  });
}

export function useBookingActions() {
  const queryClient = useQueryClient();
  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: operationalKeys.bookings });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.myBookings });
  };
  return {
    approve: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload?: BookingApprovePayload }) =>
        approveBooking(id, payload),
      onSuccess: () => {
        invalidate();
        message.success(tStaff("bookingActionSuccess"));
      },
      onError: () => message.error(tStaff("bookingActionError")),
    }),
    reject: useMutation({
      mutationFn: rejectBooking,
      onSuccess: () => {
        invalidate();
        message.success(tStaff("bookingActionSuccess"));
      },
      onError: () => message.error(tStaff("bookingActionError")),
    }),
    cancel: useMutation({
      mutationFn: cancelBooking,
      onSuccess: () => {
        invalidate();
        message.success(tStaff("bookingActionSuccess"));
      },
      onError: () => message.error(tStaff("bookingActionError")),
    }),
  };
}

export function useContracts() {
  return useQuery({
    queryKey: operationalKeys.contracts,
    queryFn: listContracts,
    staleTime: 30_000,
  });
}

export function useCompanyContracts(companyId: string | null | undefined) {
  return useQuery({
    queryKey: operationalKeys.companyContracts(companyId ?? ""),
    queryFn: () => listCompanyContracts(companyId ?? ""),
    enabled: Boolean(companyId),
    staleTime: 30_000,
  });
}

export function usePayments(filters?: PaymentListFilters) {
  return useQuery({
    queryKey: operationalKeys.payments(filters),
    queryFn: () => listPayments(filters),
    staleTime: 30_000,
  });
}

export function useCompanyPayments(companyId: string | null | undefined) {
  return useQuery({
    queryKey: operationalKeys.companyPayments(companyId ?? ""),
    queryFn: () => listCompanyPayments(companyId ?? ""),
    enabled: Boolean(companyId),
    staleTime: 30_000,
  });
}

export function useFinanceDashboard() {
  return useQuery({
    queryKey: operationalKeys.dashboardFinance,
    queryFn: getFinanceDashboard,
    staleTime: 30_000,
  });
}

export function useFinanceReport(filters?: FinanceReportFilters) {
  return useQuery({
    queryKey: operationalKeys.financeReport(filters),
    queryFn: () => getFinanceReport(filters),
    staleTime: 30_000,
  });
}

export function useNextDuePayment() {
  return useQuery({
    queryKey: operationalKeys.nextDuePayment,
    queryFn: getNextDuePayment,
    staleTime: 30_000,
  });
}

export function usePaymentActions() {
  const queryClient = useQueryClient();
  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: ["finance"] });
  };
  return {
    update: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: PaymentPatchPayload }) =>
        updatePayment(id, payload),
      onSuccess: () => {
        invalidate();
        message.success(tStaff("paymentActionSuccess"));
      },
      onError: () => message.error(tStaff("paymentActionError")),
    }),
  };
}

export function useEquipment() {
  return useQuery({
    queryKey: operationalKeys.equipment,
    queryFn: listEquipment,
    staleTime: 30_000,
  });
}

export function useEquipmentTypes() {
  return useQuery({
    queryKey: operationalKeys.equipmentTypes,
    queryFn: listEquipmentTypes,
    staleTime: 60_000,
  });
}

export function useMyAssignedEquipment(bookingId?: string) {
  return useQuery({
    queryKey: operationalKeys.myAssignedEquipment(bookingId),
    queryFn: () => listMyAssignedEquipment(bookingId),
    staleTime: 30_000,
  });
}

export function useEquipmentAssignments(filters: EquipmentAssignmentFilters = {}) {
  return useQuery({
    queryKey: operationalKeys.equipmentAssignments(filters),
    queryFn: () => listEquipmentAssignments(filters),
    staleTime: 30_000,
  });
}

export function useSpaces() {
  return useQuery({ queryKey: operationalKeys.spaces, queryFn: listSpaces, staleTime: 30_000 });
}

export function useSpaceOccupancy() {
  return useQuery({
    queryKey: operationalKeys.occupancy,
    queryFn: listSpaceOccupancy,
    staleTime: 30_000,
  });
}

export function useSpaceBookingRecords() {
  return useQuery({
    queryKey: operationalKeys.spaceBookingRecords,
    queryFn: listSpaceBookingRecords,
    staleTime: 30_000,
  });
}
