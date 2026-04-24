import axios, { type AxiosError, type AxiosInstance, type InternalAxiosRequestConfig } from "axios";
import { AUTH_LOGIN_PATH, AUTH_REFRESH_PATH, DEFAULT_API_BASE_URL } from "./constants";
import { clearAccessToken, getAccessToken, setAccessToken } from "./tokenStorage";

export interface CreateApiClientOptions {
  /** Base URL for REST calls (defaults to `NEXT_PUBLIC_API_URL` or localhost gateway). */
  baseURL?: string;
}

type RetryableConfig = InternalAxiosRequestConfig & { _retry?: boolean };

function resolveBaseURL(override?: string): string {
  if (override) return override;
  if (typeof process !== "undefined" && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  return DEFAULT_API_BASE_URL;
}

/**
 * Resolves the request path (no query string) for auth-refresh gating, e.g.
 * `http://host/api` + `/auth/refresh` → path ending with `/auth/refresh`.
 */
function getNormalizedRequestPath(config: InternalAxiosRequestConfig): string {
  const raw = config.url ?? "";
  if (raw.startsWith("http://") || raw.startsWith("https://")) {
    try {
      return new URL(raw).pathname;
    } catch {
      return raw.split("?")[0] ?? raw;
    }
  }
  let basePath = "";
  const base = config.baseURL ?? "";
  if (base) {
    try {
      basePath = new URL(base).pathname.replace(/\/$/, "");
    } catch {
      basePath = "";
    }
  }
  const rel = (raw.startsWith("/") ? raw : `/${raw}`).split("?")[0] ?? "";
  const joined = `${basePath}${rel}`.replace(/\/{2,}/g, "/");
  return joined || rel;
}

function shouldSkipAuthRefresh(config: InternalAxiosRequestConfig): boolean {
  const path = getNormalizedRequestPath(config);
  if (!path) return true;
  return path.endsWith(AUTH_LOGIN_PATH) || path.endsWith(AUTH_REFRESH_PATH);
}

/**
 * Axios instance with:
 * - env-driven `baseURL` and `withCredentials` (refresh `httpOnly` cookie)
 * - `Authorization: Bearer` from hybrid token storage
 * - single coalesced `POST /auth/refresh` on `401`, then one retry of the original request
 */
export function createApiClient(options?: CreateApiClientOptions): AxiosInstance {
  const baseURL = resolveBaseURL(options?.baseURL);

  const refreshClient = axios.create({
    baseURL,
    withCredentials: true,
  });

  const api = axios.create({
    baseURL,
    withCredentials: true,
  });

  let refreshInFlight: Promise<void> | null = null;

  async function refreshAccessTokenOnce(): Promise<void> {
    const { data } = await refreshClient.post<{ access_token?: string }>(AUTH_REFRESH_PATH, {});
    const next = data.access_token;
    if (!next || typeof next !== "string") {
      throw new Error("Refresh response missing access_token");
    }
    setAccessToken(next);
  }

  function coalescedRefresh(): Promise<void> {
    if (refreshInFlight) return refreshInFlight;
    refreshInFlight = refreshAccessTokenOnce().finally(() => {
      refreshInFlight = null;
    });
    return refreshInFlight;
  }

  api.interceptors.request.use((config) => {
    const token = getAccessToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  api.interceptors.response.use(
    (response) => response,
    async (error: AxiosError) => {
      const original = error.config as RetryableConfig | undefined;
      const status = error.response?.status;

      if (!original || original._retry) {
        return Promise.reject(error);
      }
      if (status !== 401) {
        return Promise.reject(error);
      }
      if (shouldSkipAuthRefresh(original)) {
        return Promise.reject(error);
      }

      original._retry = true;

      try {
        await coalescedRefresh();
      } catch {
        clearAccessToken();
        return Promise.reject(error);
      }

      return api(original);
    },
  );

  return api;
}

let defaultClient: AxiosInstance | null = null;

/** Shared browser/client singleton; creates lazily with env-driven base URL. */
export function getDefaultApiClient(): AxiosInstance {
  if (!defaultClient) {
    defaultClient = createApiClient();
  }
  return defaultClient;
}
