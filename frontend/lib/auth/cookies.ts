import { DEFAULT_REFRESH_TOKEN_COOKIE_NAME } from "./constants";

export function getRefreshTokenCookieName(): string {
  return process.env.AUTH_REFRESH_COOKIE_NAME?.trim() || DEFAULT_REFRESH_TOKEN_COOKIE_NAME;
}
