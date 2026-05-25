import { expect, test } from "@playwright/test";
import { SignJWT } from "jose";

const secret = new TextEncoder().encode("e2e-playwright-secret");

async function gotoAfterSessionCookie(
  page: import("@playwright/test").Page,
  path: string,
): Promise<void> {
  try {
    await page.goto(path);
  } catch (error) {
    if (!String(error).includes("ERR_ABORTED")) throw error;
    await page.goto(path);
  }
}

async function mintPair(
  role: "staff" | "client" | "director",
): Promise<{ access: string; refresh: string }> {
  const sub = "00000000-0000-4000-8000-000000000099";
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

test.describe("create user page", () => {
  test.beforeEach(async ({ context }) => {
    await context.clearCookies();
  });

  test("director can submit create-user form with mocked API", async ({ page }) => {
    const { access, refresh } = await mintPair("director");

    await page.route("**/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access }),
      });
    });

    /** Axios POST /auth/refresh — prevents interceptor from clearing the session when refresh cannot reach cross-origin localhost/api with cookies. */
    await page.route("**/api/auth/refresh", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access }),
      });
    });

    let postedBody: Record<string, unknown> | null = null;

    await page.route(/\/api\/auth\/users/, async (route) => {
      const method = route.request().method();
      if (method === "GET") {
        await route.fulfill({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify([]),
        });
        return;
      }
      if (method !== "POST") {
        await route.continue();
        return;
      }
      const raw = route.request().postData();
      postedBody = raw ? (JSON.parse(raw) as Record<string, unknown>) : null;
      await route.fulfill({
        status: 201,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: "11111111-1111-4111-8111-111111111111",
          email: postedBody?.email,
          role: "Staff",
          first_name: postedBody?.first_name,
          last_name: postedBody?.last_name,
          company_id: null,
          is_active: true,
        }),
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

    await page.getByLabel("Email").fill("director@test.local");
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

    await page.context().addCookies([
      {
        name: "ilb.refresh_token",
        value: refresh,
        sameSite: "Lax",
        httpOnly: true,
        url: "http://localhost:3000",
      },
    ]);

    await gotoAfterSessionCookie(page, "/users/new");
    await expect(page).toHaveURL(/\/users\/new/);

    await expect(page.locator('input[autocomplete="given-name"]')).toBeVisible({ timeout: 15_000 });

    await page.locator('input[autocomplete="given-name"]').fill("Maria");
    await page.locator('input[autocomplete="family-name"]').fill("Silva");
    await page.locator('input[autocomplete="email"]').fill("maria.silva@example.com");

    const pwInputs = page.locator('input[autocomplete="new-password"]');
    await pwInputs.nth(0).fill("TempPass99!");
    await pwInputs.nth(1).fill("TempPass99!");

    await page.getByRole("button", { name: "Criar utilizador" }).click();

    await expect(page).toHaveURL(/\/users$/);
    expect(postedBody).toMatchObject({
      email: "maria.silva@example.com",
      first_name: "Maria",
      last_name: "Silva",
      password: "TempPass99!",
      role: "Staff",
    });
    expect(postedBody).not.toHaveProperty("company_id");
  });
});
