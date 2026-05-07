"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  type UserUpdatePayload,
  deactivateUser,
  getUserById,
  listUsers,
  updateUser,
} from "@/lib/api/users";

export const userKeys = {
  all: ["users"] as const,
  lists: () => [...userKeys.all, "list"] as const,
  directorList: () => [...userKeys.lists(), "director"] as const,
  details: () => [...userKeys.all, "detail"] as const,
  detail: (id: string) => [...userKeys.details(), id] as const,
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

/** Single user for Director detail/edit (disabled when `enabled` is false). */
export function useUserDetail(userId: string, enabled: boolean) {
  return useQuery({
    queryKey: userKeys.detail(userId),
    queryFn: () => getUserById(userId),
    enabled: enabled && Boolean(userId),
    staleTime: 30_000,
    retry: 1,
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ userId, payload }: { userId: string; payload: UserUpdatePayload }) =>
      updateUser(userId, payload),
    onSuccess: (_data, variables) => {
      void queryClient.invalidateQueries({ queryKey: userKeys.directorList() });
      void queryClient.invalidateQueries({ queryKey: userKeys.detail(variables.userId) });
    },
  });
}

export function useDeactivateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (userId: string) => deactivateUser(userId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: userKeys.directorList() });
    },
  });
}
