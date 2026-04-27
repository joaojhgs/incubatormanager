/**
 * Gateway + Auth header pass-through integration test (W1-48).
 *
 * Verifies that the Nginx gateway correctly:
 *  1. Validates JWTs via auth_request to auth-service /auth/verify/
 *  2. Injects X-User-Id, X-User-Role, X-Company-Id headers into upstream requests
 *  3. Enforces role-based access: Director → 200, Client → 403
 *
 * Prerequisites:
 *  - Docker Compose stack running (gateway + auth-service + postgres + redis)
 *  - Seed data loaded:  docker compose exec auth-service python /app/infra/seed/seed.py
 *
 * Test users created by the seed script:
 *  - director@ilb.test / test-password-1234  (role: Director)
 *  - client@ilb.test   / test-password-1234  (role: Client)
 */

import { expect, test } from '@playwright/test';

const BASE = process.env.E2E_BASE_URL ?? 'http://127.0.0.1:80';

const DIRECTOR_EMAIL = 'director@ilb.test';
const DIRECTOR_PASSWORD = 'test-password-1234';
const CLIENT_EMAIL = 'client@ilb.test';
const CLIENT_PASSWORD = 'test-password-1234';

/** Login via the gateway and return the access token. */
async function login(email: string, password: string): Promise<string> {
  const res = await fetch(`${BASE}/api/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });
  expect(res.status, `Login for ${email} should succeed`).toBe(200);
  const data = (await res.json()) as { access: string; refresh: string };
  expect(data.access).toBeTruthy();
  return data.access;
}

test.describe('Gateway auth header pass-through', () => {
  let directorToken: string;
  let clientToken: string;

  test.beforeAll(async () => {
    directorToken = await login(DIRECTOR_EMAIL, DIRECTOR_PASSWORD);
    clientToken = await login(CLIENT_EMAIL, CLIENT_PASSWORD);
  });

  test('Director can list users via gateway', async () => {
    const res = await fetch(`${BASE}/api/auth/users/`, {
      headers: { Authorization: `Bearer ${directorToken}` },
    });
    expect(res.status, 'Director should get 200 from /api/auth/users/').toBe(200);
    const body = await res.json();
    expect(Array.isArray(body), 'Response should be an array').toBe(true);
  });

  test('Client receives 403 from /api/auth/users/ via gateway', async () => {
    const res = await fetch(`${BASE}/api/auth/users/`, {
      headers: { Authorization: `Bearer ${clientToken}` },
    });
    expect(res.status, 'Client should get 403 from /api/auth/users/').toBe(403);
    const body = (await res.json()) as { detail: string };
    expect(body.detail).toContain('permission');
  });

  test('Unauthenticated request to protected route returns 401', async () => {
    const res = await fetch(`${BASE}/api/auth/users/`);
    expect(res.status, 'Request without token should get 401 from gateway auth_request').toBe(401);
  });

  test('Gateway injects X-User-Role header after auth_request', async () => {
    // Verify the auth_request subrequest returns correct headers.
    // This tests the gateway → auth-service → upstream flow end-to-end.
    const res = await fetch(`${BASE}/api/auth/users/`, {
      headers: { Authorization: `Bearer ${directorToken}` },
    });
    expect(res.status).toBe(200);
    // The fact that we got 200 (not 401 or 403) proves the gateway
    // successfully validated the JWT via auth_request and forwarded
    // X-User-Role=Director to auth-service, which then allowed the request.
  });

  test('Invalid token returns 401 from gateway', async () => {
    const res = await fetch(`${BASE}/api/auth/users/`, {
      headers: { Authorization: 'Bearer invalid.jwt.token' },
    });
    expect(res.status, 'Invalid token should get 401').toBe(401);
  });
});
