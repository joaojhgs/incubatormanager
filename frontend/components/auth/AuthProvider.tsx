"use client";

import type { ReactNode } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { decodeAccessTokenPayload } from "@/lib/auth/accessTokenClaims";
import type { AuthUser } from "@/lib/auth/types";
import { ACCESS_TOKEN_STORAGE_KEY } from "@/lib/api/constants";
import { clearAccessToken, getAccessToken } from "@/lib/api/tokenStorage";

interface AuthContextValue {
  user: AuthUser | null;
  isAuthenticated: boolean;
  /** True until the first client-side read of token storage completes. */
  isReady: boolean;
  /** Re-reads the access token from storage into React state (e.g. after login). */
  syncAuthFromStorage: () => void;
  /** Clears the access token and resets auth state (logout UI). */
  logoutLocal: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

function claimsToUser(claims: ReturnType<typeof decodeAccessTokenPayload>): AuthUser | null {
  if (!claims?.role || typeof claims.role !== "string") return null;
  const id = typeof claims.sub === "string" && claims.sub ? claims.sub : "";
  if (!id) return null;
  return {
    id,
    email: typeof claims.email === "string" ? claims.email : undefined,
    role: claims.role,
    companyId: claims.company_id ?? null,
  };
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [isReady, setIsReady] = useState(false);

  const refreshFromStorage = useCallback(() => {
    const token = getAccessToken();
    setUser(claimsToUser(decodeAccessTokenPayload(token)));
  }, []);

  useEffect(() => {
    refreshFromStorage();
    setIsReady(true);
  }, [refreshFromStorage]);

  useEffect(() => {
    function onStorage(ev: StorageEvent) {
      if (ev.key === null || ev.key === ACCESS_TOKEN_STORAGE_KEY) {
        refreshFromStorage();
      }
    }
    window.addEventListener("storage", onStorage);
    return () => window.removeEventListener("storage", onStorage);
  }, [refreshFromStorage]);

  const logoutLocal = useCallback(() => {
    clearAccessToken();
    setUser(null);
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: Boolean(user),
      isReady,
      syncAuthFromStorage: refreshFromStorage,
      logoutLocal,
    }),
    [user, isReady, refreshFromStorage, logoutLocal],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return ctx;
}
