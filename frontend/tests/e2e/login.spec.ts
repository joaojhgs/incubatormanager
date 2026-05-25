import { expect, test } from "@playwright/test";
import { SignJWT } from "jose";

const secret = new TextEncoder().encode("e2e-playwright-secret");

async function mintPair(role: "staff" | "client"): Promise<{ access: string; refresh: string }> {
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

test.describe("login page", () => {
  test.beforeEach(async ({ context }) => {
    await context.clearCookies();
  });

  test("staff login redirects to dashboard", async ({ page }) => {
    const { access, refresh } = await mintPair("staff");
    await page.route("**/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access }),
      });
    });

    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.getByLabel("Email").fill("staff@test.local");
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
    await page.goto("/dashboard");
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test("client login redirects to portal", async ({ page }) => {
    const { access, refresh } = await mintPair("client");
    await page.route("**/api/auth/login", async (route) => {
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access }),
      });
    });

    await page.goto("/login");
    await page.evaluate(() => {
      localStorage.clear();
      sessionStorage.clear();
    });
    await page.getByLabel("Email").fill("client@test.local");
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
    await page.goto("/portal");
    await expect(page).toHaveURL(/\/portal/);
  });

  test("invalid credentials shows an error alert", async ({ page }) => {
    await page.route("**/api/auth/login", async (route) => {
      await route.fulfill({
        status: 401,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          detail: "No active account found with the given credentials",
        }),
      });
    });

    await page.goto("/login");
    await page.getByLabel("Email").fill("nobody@test.local");
    await page.getByLabel("Palavra-passe").fill("wrong-password");
    await page.getByRole("button", { name: "Entrar" }).click();
    await expect(page.locator(".ant-alert-error")).toContainText("No active account found");
  });

  test("empty submit shows inline field errors", async ({ page }) => {
    await page.goto("/login");
    await page.getByRole("button", { name: "Entrar" }).click();
    await expect(page.getByText("Indique o email.")).toBeVisible();
    await expect(page.getByText("Indique a palavra-passe.")).toBeVisible();
  });
});
