import { expect, test } from "@playwright/test";
import { SignJWT } from "jose";

const secret = new TextEncoder().encode("e2e-playwright-secret");

const DIRECTOR_EMAIL = "director-smoke@test.local";
const NEW_STAFF_EMAIL = "staff-created-smoke@example.com";

const SUB_DIRECTOR = "00000000-0000-4000-8000-000000000001";
const SUB_NEW_STAFF = "00000000-0000-4000-8000-000000000002";

async function mintPair(
  role: "staff" | "director",
  sub: string,
): Promise<{ access: string; refresh: string }> {
  const access = await new SignJWT({ role, token_type: "access" })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(sub)
    .setExpirationTime("15m")
    .sign(secret);
  const refresh = await new SignJWT({ role, token_type: "refresh" })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(sub)
    .setExpirationTime("7d")
    .sign(secret);
  return { access, refresh };
}

test.describe("smoke: login → users list → create user → re-login", () => {
  test.beforeEach(async ({ context }) => {
    await context.clearCookies();
  });

  test("full flow with mocked auth API", async ({ page }) => {
    let refreshRole: "director" | "staff" = "director";

    await page.route("**/api/auth/refresh", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const sub = refreshRole === "director" ? SUB_DIRECTOR : SUB_NEW_STAFF;
      const { access } = await mintPair(refreshRole, sub);
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access }),
      });
    });

    await page.route("**/api/auth/login", async (route) => {
      const raw = route.request().postData();
      const body = raw ? (JSON.parse(raw) as { email?: string }) : {};
      const email = body.email ?? "";
      const isDirector = email === DIRECTOR_EMAIL;
      const role = isDirector ? "director" : "staff";
      const sub = isDirector ? SUB_DIRECTOR : SUB_NEW_STAFF;
      const { access } = await mintPair(role, sub);
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access }),
      });
    });

    type ListedUser = {
      id: string;
      email: string;
      role: string;
      first_name: string;
      last_name: string;
      company_id: null;
      is_active: boolean;
    };

    const listedUsers: ListedUser[] = [];

    await page.route(/\/api\/auth\/users/, async (route) => {
      const method = route.request().method();
      if (method === "GET") {
        await route.fulfill({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(listedUsers),
        });
        return;
      }
      if (method !== "POST") {
        await route.continue();
        return;
      }
      const raw = route.request().postData();
      const posted = raw ? (JSON.parse(raw) as Record<string, unknown>) : {};
      const row: ListedUser = {
        id: "11111111-1111-4111-8111-111111111111",
        email: String(posted.email ?? ""),
        role: typeof posted.role === "string" ? posted.role : "Staff",
        first_name: String(posted.first_name ?? ""),
        last_name: String(posted.last_name ?? ""),
        company_id: null,
        is_active: true,
      };
      listedUsers.push(row);
      await route.fulfill({
        status: 201,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(row),
      });
    });

    await page.goto("/login");
    await page.evaluate(() => {
      try {
        localStorage.clear();
      } catch {
        /* ignore */
      }
    });

    await page.getByLabel("Email").fill(DIRECTOR_EMAIL);
    await page.getByLabel("Palavra-passe").fill("Password123!");
    await page.getByRole("button", { name: "Entrar" }).click();

    await expect
      .poll(async () => {
        try {
          return await page.evaluate(() => localStorage.getItem("ilb.access_token"));
        } catch {
          return null;
        }
      })
      .toMatch(/^ey/);

    const directorTokens = await mintPair("director", SUB_DIRECTOR);
    await page.context().addCookies([
      {
        name: "ilb.refresh_token",
        value: directorTokens.refresh,
        sameSite: "Lax",
        httpOnly: true,
        url: "http://localhost:3000",
      },
    ]);

    await page.goto("/users");
    await expect(page).toHaveURL(/\/users$/);
    await expect(page.getByRole("heading", { name: "Utilizadores" })).toBeVisible();

    await page.getByRole("link", { name: "Novo utilizador" }).click();
    await expect(page).toHaveURL(/\/users\/new/);

    await page.locator('input[autocomplete="given-name"]').fill("Smoke");
    await page.locator('input[autocomplete="family-name"]').fill("StaffUser");
    await page.locator('input[autocomplete="email"]').fill(NEW_STAFF_EMAIL);
    const pwInputs = page.locator('input[autocomplete="new-password"]');
    await pwInputs.nth(0).fill("TempPass99!");
    await pwInputs.nth(1).fill("TempPass99!");
    await page.getByRole("button", { name: "Criar utilizador" }).click();

    await expect(page).toHaveURL(/\/users$/);
    await expect(page.getByRole("cell", { name: NEW_STAFF_EMAIL })).toBeVisible();

    refreshRole = "staff";
    await page.evaluate(() => {
      try {
        localStorage.clear();
      } catch {
        /* ignore */
      }
    });
    await page.context().clearCookies();

    await page.goto("/login");
    await page.getByLabel("Email").fill(NEW_STAFF_EMAIL);
    await page.getByLabel("Palavra-passe").fill("TempPass99!");
    await page.getByRole("button", { name: "Entrar" }).click();

    await expect
      .poll(async () => {
        try {
          return await page.evaluate(() => localStorage.getItem("ilb.access_token"));
        } catch {
          return null;
        }
      })
      .toMatch(/^ey/);

    const staffTokens = await mintPair("staff", SUB_NEW_STAFF);
    await page.context().addCookies([
      {
        name: "ilb.refresh_token",
        value: staffTokens.refresh,
        sameSite: "Lax",
        httpOnly: true,
        url: "http://localhost:3000",
      },
    ]);

    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
