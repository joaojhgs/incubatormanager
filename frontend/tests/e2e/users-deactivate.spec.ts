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

const DIRECTOR_EMAIL = "director-deactivate@test.local";

const SUB_DIRECTOR = "00000000-0000-4000-8000-000000000099";
const SUB_STAFF = "00000000-0000-4000-8000-000000000098";

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

type ListedUser = {
  id: string;
  email: string;
  role: string;
  first_name: string;
  last_name: string;
  company_id: null;
  is_active: boolean;
};

test.describe("users list: show inactive toggle + deactivate", () => {
  test.beforeEach(async ({ context }) => {
    await context.clearCookies();
  });

  test("inactive hidden by default; toggle shows inactive; deactivate hides row", async ({
    page,
  }) => {
    let rows: ListedUser[] = [
      {
        id: SUB_DIRECTOR,
        email: DIRECTOR_EMAIL,
        role: "Director",
        first_name: "Dir",
        last_name: "One",
        company_id: null,
        is_active: true,
      },
      {
        id: SUB_STAFF,
        email: "staff-to-deactivate@example.com",
        role: "Staff",
        first_name: "Staff",
        last_name: "Two",
        company_id: null,
        is_active: true,
      },
      {
        id: "33333333-3333-4333-8333-333333333333",
        email: "inactive@example.com",
        role: "Staff",
        first_name: "Old",
        last_name: "Inactive",
        company_id: null,
        is_active: false,
      },
    ];

    await page.route("**/api/auth/refresh**", async (route) => {
      if (route.request().method() !== "POST") {
        await route.continue();
        return;
      }
      const { access } = await mintPair("director", SUB_DIRECTOR);
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
      const sub = email === DIRECTOR_EMAIL ? SUB_DIRECTOR : SUB_STAFF;
      const { access } = await mintPair("director", sub);
      await route.fulfill({
        status: 200,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ access }),
      });
    });

    await page.route(/\/api\/auth\/users/, async (route) => {
      const req = route.request();
      const method = req.method();
      const url = new URL(req.url());
      const pathMatch = url.pathname.match(/\/auth\/users\/([^/]+)\/?$/);

      if (method === "GET" && url.pathname.endsWith("/auth/users/")) {
        await route.fulfill({
          status: 200,
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(rows),
        });
        return;
      }

      if (method === "DELETE" && pathMatch) {
        const id = pathMatch[1];
        rows = rows.map((r) => (r.id === id ? { ...r, is_active: false } : r));
        await route.fulfill({ status: 204 });
        return;
      }

      await route.continue();
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

    await gotoAfterSessionCookie(page, "/users");
    await expect(page.getByRole("heading", { name: "Utilizadores" })).toBeVisible();

    await expect(page.getByRole("cell", { name: "inactive@example.com" })).not.toBeVisible();

    await page.getByRole("switch", { name: "Mostrar contas inativas" }).click();
    await expect(page.getByRole("cell", { name: "inactive@example.com" })).toBeVisible();

    await page.getByRole("switch", { name: "Mostrar contas inativas" }).click();

    await page
      .getByRole("row", { name: /staff-to-deactivate@example\.com/ })
      .getByRole("button", { name: "Desativar" })
      .click();
    await page.locator(".ant-popconfirm").getByRole("button", { name: "Desativar" }).click();

    await expect(
      page.getByRole("cell", { name: "staff-to-deactivate@example.com" }),
    ).not.toBeVisible();

    await page.getByRole("switch", { name: "Mostrar contas inativas" }).click();
    await expect(page.getByRole("cell", { name: "staff-to-deactivate@example.com" })).toBeVisible();
    await expect(
      page.getByRole("row", { name: /staff-to-deactivate@example\.com/ }).getByText("Inativo"),
    ).toBeVisible();
  });
});
