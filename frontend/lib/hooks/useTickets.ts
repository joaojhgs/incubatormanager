"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { message } from "antd";

import {
  addTicketMessage,
  createTicket,
  getTicket,
  listMyTickets,
  listTickets,
  type Ticket,
  type TicketCreatePayload,
  type TicketMessageCreatePayload,
} from "@/lib/api/tickets";
import { tClient } from "@/lib/i18n/clientPortal";

export const ticketKeys = {
  all: ["tickets"] as const,
  list: () => [...ticketKeys.all, "list"] as const,
  mine: () => [...ticketKeys.list(), "mine"] as const,
  detail: (ticketId: string) => [...ticketKeys.all, "detail", ticketId] as const,
};

export function useTickets() {
  return useQuery({
    queryKey: ticketKeys.list(),
    queryFn: () => listTickets(),
    staleTime: 30_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}

export function useMyTickets() {
  return useQuery({
    queryKey: ticketKeys.mine(),
    queryFn: () => listMyTickets(),
    staleTime: 30_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}

export function useTicketDetail(ticketId: string) {
  return useQuery({
    queryKey: ticketKeys.detail(ticketId),
    queryFn: () => getTicket(ticketId),
    enabled: Boolean(ticketId),
    staleTime: 30_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}

export function useCreateTicket() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketCreatePayload) => createTicket(payload),
    onSuccess: (ticket) => {
      void queryClient.invalidateQueries({ queryKey: ticketKeys.mine() });
      void queryClient.invalidateQueries({ queryKey: ticketKeys.list() });
      void queryClient.setQueryData(ticketKeys.detail(ticket.id), ticket);
      message.success(tClient("portalTicketCreateSuccess"));
    },
    onError: () => message.error(tClient("portalTicketCreateError")),
  });
}

export function useAddTicketMessage(ticketId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: TicketMessageCreatePayload) => addTicketMessage(ticketId, payload),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ticketKeys.detail(ticketId) });
      void queryClient.invalidateQueries({ queryKey: ticketKeys.mine() });
      message.success(tClient("portalTicketMessageSuccess"));
    },
    onError: () => message.error(tClient("portalTicketMessageError")),
  });
}

export type { Ticket };
