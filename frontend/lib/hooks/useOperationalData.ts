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
  listPublicBookingWindows,
  rejectBooking,
  type BookingApprovePayload,
  type BookingCreatePayload,
} from "@/lib/api/bookings";
import {
  activateContract,
  createContract,
  deleteContract,
  listCompanyContracts,
  listContracts,
  terminateContract,
  updateContract,
  type ContractCreatePayload,
  type ContractTerminatePayload,
  type ContractUpdatePayload,
} from "@/lib/api/contracts";
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
  assignEquipment,
  createEquipment,
  createEquipmentType,
  deleteEquipment,
  deleteEquipmentType,
  listEquipment,
  listEquipmentAssignments,
  listEquipmentTypes,
  listMyAssignedEquipment,
  listPublicEquipment,
  releaseEquipment,
  updateEquipment,
  updateEquipmentType,
  type EquipmentAssignPayload,
  type EquipmentAssignmentFilters,
  type EquipmentCreatePayload,
  type EquipmentReleasePayload,
  type EquipmentTypePayload,
  type EquipmentUpdatePayload,
} from "@/lib/api/inventory";
import {
  createSpace,
  createSpaceType,
  deleteSpace,
  deleteSpaceType,
  listSpaceBookingRecords,
  listSpaceOccupancy,
  listPublicSpaces,
  listSpaces,
  listSpaceTypes,
  updateSpace,
  updateSpaceType,
  type SpaceCreatePayload,
  type SpaceTypePayload,
  type SpaceUpdatePayload,
} from "@/lib/api/spaces";
import { tStaff } from "@/lib/i18n/staffNav";
import { tClient } from "@/lib/i18n/clientPortal";

export type QueryControls = {
  enabled?: boolean;
  retry?: boolean | number;
  refetchOnMount?: boolean | "always";
  refetchOnReconnect?: boolean | "always";
  staleTime?: number;
};

const operationalKeys = {
  bookings: ["bookings"] as const,
  bookingCalendar: ["bookings", "calendar"] as const,
  publicBookingWindows: ["bookings", "publicWindows"] as const,
  myBookings: ["bookings", "mine"] as const,
  contracts: ["contracts"] as const,
  companyContracts: (companyId: string) => ["contracts", "company", companyId] as const,
  dashboardFinance: ["finance", "dashboard"] as const,
  payments: (filters?: PaymentListFilters) => ["finance", "payments", filters ?? {}] as const,
  companyPayments: (companyId: string) => ["finance", "payments", "company", companyId] as const,
  financeReport: (filters?: FinanceReportFilters) => ["finance", "reports", filters ?? {}] as const,
  nextDuePayment: ["finance", "payments", "nextDue"] as const,
  equipment: ["inventory", "equipment"] as const,
  publicEquipment: ["inventory", "publicEquipment"] as const,
  equipmentTypes: ["inventory", "equipmentTypes"] as const,
  equipmentAssignments: (filters?: EquipmentAssignmentFilters) =>
    ["inventory", "assignments", filters?.bookingId ?? null, filters?.equipmentId ?? null] as const,
  myAssignedEquipment: (bookingId?: string) => ["inventory", "myAssignments", bookingId] as const,
  spaces: ["spaces"] as const,
  publicSpaces: ["spaces", "public"] as const,
  spaceTypes: ["spaces", "types"] as const,
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

export function usePublicBookingWindows() {
  return useQuery({
    queryKey: operationalKeys.publicBookingWindows,
    queryFn: listPublicBookingWindows,
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

export function useContractActions() {
  const queryClient = useQueryClient();
  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: operationalKeys.contracts });
    void queryClient.invalidateQueries({ queryKey: ["contracts"] });
    void queryClient.invalidateQueries({ queryKey: ["finance"] });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.spaces });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.spaceBookingRecords });
  };
  return {
    create: useMutation({
      mutationFn: (payload: ContractCreatePayload) => createContract(payload),
      onSuccess: () => {
        invalidate();
        message.success("Contrato guardado.");
      },
      onError: () => message.error("Não foi possível guardar o contrato."),
    }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: ContractUpdatePayload }) =>
        updateContract(id, payload),
      onSuccess: () => {
        invalidate();
        message.success("Contrato atualizado.");
      },
      onError: () => message.error("Não foi possível atualizar o contrato."),
    }),
    remove: useMutation({
      mutationFn: deleteContract,
      onSuccess: () => {
        invalidate();
        message.success("Contrato removido.");
      },
      onError: () => message.error("Não foi possível remover o contrato."),
    }),
    activate: useMutation({
      mutationFn: activateContract,
      onSuccess: () => {
        invalidate();
        message.success("Contrato ativado.");
      },
      onError: () => message.error("Não foi possível ativar o contrato."),
    }),
    terminate: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload?: ContractTerminatePayload }) =>
        terminateContract(id, payload),
      onSuccess: () => {
        invalidate();
        message.success("Contrato terminado.");
      },
      onError: () => message.error("Não foi possível terminar o contrato."),
    }),
  };
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

export function usePublicEquipment() {
  return useQuery({
    queryKey: operationalKeys.publicEquipment,
    queryFn: listPublicEquipment,
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

export function useEquipmentActions() {
  const queryClient = useQueryClient();
  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: operationalKeys.equipment });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.equipmentTypes });
    void queryClient.invalidateQueries({ queryKey: ["inventory"] });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.spaces });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.spaceBookingRecords });
  };
  return {
    create: useMutation({
      mutationFn: (payload: EquipmentCreatePayload) => createEquipment(payload),
      onSuccess: () => {
        invalidate();
        message.success("Equipamento guardado.");
      },
      onError: () => message.error("Não foi possível guardar o equipamento."),
    }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: EquipmentUpdatePayload }) =>
        updateEquipment(id, payload),
      onSuccess: () => {
        invalidate();
        message.success("Equipamento atualizado.");
      },
      onError: () => message.error("Não foi possível atualizar o equipamento."),
    }),
    remove: useMutation({
      mutationFn: deleteEquipment,
      onSuccess: () => {
        invalidate();
        message.success("Equipamento removido.");
      },
      onError: () => message.error("Não foi possível remover o equipamento."),
    }),
    createType: useMutation({
      mutationFn: (payload: EquipmentTypePayload) => createEquipmentType(payload),
      onSuccess: () => {
        invalidate();
        message.success("Tipo de equipamento guardado.");
      },
      onError: () => message.error("Não foi possível guardar o tipo de equipamento."),
    }),
    updateType: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: Partial<EquipmentTypePayload> }) =>
        updateEquipmentType(id, payload),
      onSuccess: () => {
        invalidate();
        message.success("Tipo de equipamento atualizado.");
      },
      onError: () => message.error("Não foi possível atualizar o tipo de equipamento."),
    }),
    deleteType: useMutation({
      mutationFn: deleteEquipmentType,
      onSuccess: () => {
        invalidate();
        message.success("Tipo de equipamento removido.");
      },
      onError: () => message.error("Não foi possível remover o tipo de equipamento."),
    }),
    assign: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: EquipmentAssignPayload }) =>
        assignEquipment(id, payload),
      onSuccess: () => {
        invalidate();
        message.success("Equipamento atribuído.");
      },
      onError: () => message.error("Não foi possível atribuir o equipamento."),
    }),
    release: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: EquipmentReleasePayload }) =>
        releaseEquipment(id, payload),
      onSuccess: () => {
        invalidate();
        message.success("Equipamento libertado.");
      },
      onError: () => message.error("Não foi possível libertar o equipamento."),
    }),
  };
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

export function useSpaces(options: QueryControls = {}) {
  return useQuery({
    queryKey: operationalKeys.spaces,
    queryFn: listSpaces,
    staleTime: 30_000,
    ...options,
  });
}

export function usePublicSpaces(options: QueryControls = {}) {
  return useQuery({
    queryKey: operationalKeys.publicSpaces,
    queryFn: listPublicSpaces,
    staleTime: 30_000,
    ...options,
  });
}

export function useSpaceTypes(options: QueryControls = {}) {
  return useQuery({
    queryKey: operationalKeys.spaceTypes,
    queryFn: listSpaceTypes,
    staleTime: 60_000,
    ...options,
  });
}

export function useSpaceActions() {
  const queryClient = useQueryClient();
  const invalidate = () => {
    void queryClient.invalidateQueries({ queryKey: operationalKeys.spaces });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.spaceTypes });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.occupancy });
    void queryClient.invalidateQueries({ queryKey: operationalKeys.spaceBookingRecords });
  };
  return {
    create: useMutation({
      mutationFn: (payload: SpaceCreatePayload) => createSpace(payload),
      onSuccess: () => {
        invalidate();
        message.success("Espaço guardado.");
      },
      onError: () => message.error("Não foi possível guardar o espaço."),
    }),
    update: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: SpaceUpdatePayload }) =>
        updateSpace(id, payload),
      onSuccess: () => {
        invalidate();
        message.success("Espaço atualizado.");
      },
      onError: () => message.error("Não foi possível atualizar o espaço."),
    }),
    remove: useMutation({
      mutationFn: deleteSpace,
      onSuccess: () => {
        invalidate();
        message.success("Espaço removido.");
      },
      onError: () => message.error("Não foi possível remover o espaço."),
    }),
    createType: useMutation({
      mutationFn: (payload: SpaceTypePayload) => createSpaceType(payload),
      onSuccess: () => {
        invalidate();
        message.success("Tipo de espaço guardado.");
      },
      onError: () => message.error("Não foi possível guardar o tipo de espaço."),
    }),
    updateType: useMutation({
      mutationFn: ({ id, payload }: { id: string; payload: Partial<SpaceTypePayload> }) =>
        updateSpaceType(id, payload),
      onSuccess: () => {
        invalidate();
        message.success("Tipo de espaço atualizado.");
      },
      onError: () => message.error("Não foi possível atualizar o tipo de espaço."),
    }),
    deleteType: useMutation({
      mutationFn: deleteSpaceType,
      onSuccess: () => {
        invalidate();
        message.success("Tipo de espaço removido.");
      },
      onError: () => message.error("Não foi possível remover o tipo de espaço."),
    }),
  };
}

export function useSpaceOccupancy(options: QueryControls = {}) {
  return useQuery({
    queryKey: operationalKeys.occupancy,
    queryFn: listSpaceOccupancy,
    staleTime: 30_000,
    ...options,
  });
}

export function useSpaceBookingRecords(options: QueryControls = {}) {
  return useQuery({
    queryKey: operationalKeys.spaceBookingRecords,
    queryFn: listSpaceBookingRecords,
    staleTime: 30_000,
    ...options,
  });
}
