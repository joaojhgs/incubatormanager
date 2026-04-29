"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { createUser, type UserCreatePayload } from "@/lib/api/users";

import { userKeys } from "./useUsers";

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: UserCreatePayload) => createUser(payload),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: userKeys.directorList() });
    },
  });
}
