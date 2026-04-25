import { defineConfig, devices } from "@playwright/test";

const e2eJwtSecret = "e2e-playwright-secret";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  reporter: "list",
  use: {
    baseURL: "http://127.0.0.1:3000",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: `AUTH_JWT_SECRET=${e2eJwtSecret} npm run build && AUTH_JWT_SECRET=${e2eJwtSecret} npm run start -- -p 3000`,
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
    stdout: "pipe",
    stderr: "pipe",
  },
});
