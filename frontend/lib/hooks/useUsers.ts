"use client";

import { useQuery } from "@tanstack/react-query";

import { listUsers } from "@/lib/api/users";

export const userKeys = {
  all: ["users"] as const,
  lists: () => [...userKeys.all, "list"] as const,
  directorList: () => [...userKeys.lists(), "director"] as const,
};

/** Full user list for Director UI (disabled when `enabled` is false). */
export function useUsersList(enabled: boolean) {
  return useQuery({
    queryKey: userKeys.directorList(),
    queryFn: () => listUsers(),
    enabled,
    staleTime: 30_000,
    retry: 1,
  });
}
