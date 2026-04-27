import { defineConfig } from '@playwright/test';

/**
 * Playwright config for cross-service integration tests.
 *
 * These tests run against a live Docker Compose stack (gateway + services).
 * Start the stack first:  docker compose up -d   (or tilt up)
 * Then run:               npm run test:e2e
 */
export default defineConfig({
  testDir: '.',
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: 'list',
  timeout: 30_000,
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://127.0.0.1:80',
    extraHTTPHeaders: {
      'Content-Type': 'application/json',
    },
  },
  projects: [{ name: 'gateway-auth', testDir: '.' }],
});
