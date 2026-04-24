import { ACCESS_TOKEN_STORAGE_KEY } from "./constants";

let memoryAccessToken: string | null = null;

function readFromLocalStorage(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(ACCESS_TOKEN_STORAGE_KEY);
}

/**
 * Returns the current access token, preferring the in-memory copy and
 * falling back to `localStorage` on the client (hybrid persistence).
 */
export function getAccessToken(): string | null {
  if (memoryAccessToken) return memoryAccessToken;
  const stored = readFromLocalStorage();
  memoryAccessToken = stored;
  return stored;
}

/**
 * Persists the access token in memory and `localStorage` (browser only).
 * Pass `null` to clear both.
 */
export function setAccessToken(token: string | null): void {
  memoryAccessToken = token;
  if (typeof window === "undefined") return;
  if (token) {
    window.localStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, token);
  } else {
    window.localStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  }
}

export function clearAccessToken(): void {
  setAccessToken(null);
}
