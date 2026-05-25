"use client";

import { useQuery } from "@tanstack/react-query";

import { listMyTickets, listTickets, type Ticket } from "@/lib/api/tickets";

export const ticketKeys = {
  all: ["tickets"] as const,
  list: () => [...ticketKeys.all, "list"] as const,
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
    queryKey: [...ticketKeys.list(), "mine"] as const,
    queryFn: () => listMyTickets(),
    staleTime: 30_000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}

export type { Ticket };
