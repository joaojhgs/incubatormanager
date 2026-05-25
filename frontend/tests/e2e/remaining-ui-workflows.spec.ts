import { expect, test, type BrowserContext, type Page, type Route } from "@playwright/test";
import { SignJWT } from "jose";

const secret = new TextEncoder().encode("e2e-playwright-secret");
const refreshCookieName = "ilb.refresh_token";
const accessStorageKey = "ilb.access_token";

async function mintPair(role: "director" | "client"): Promise<{ access: string; refresh: string }> {
  const access = await new SignJWT({ role, token_type: "access" })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject("00000000-0000-4000-8000-000000000123")
    .setExpirationTime("15m")
    .sign(secret);
  const refresh = await new SignJWT({ role, token_type: "refresh" })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject("00000000-0000-4000-8000-000000000123")
    .setExpirationTime("7d")
    .sign(secret);
  return { access, refresh };
}

async function seedSession(page: Page, context: BrowserContext): Promise<void> {
  const { access, refresh } = await mintPair("director");
  await page.addInitScript(({ key, token }) => window.localStorage.setItem(key, token), {
    key: accessStorageKey,
    token: access,
  });
  await context.addCookies([
    {
      name: refreshCookieName,
      value: refresh,
      sameSite: "Lax",
      httpOnly: true,
      url: "http://localhost:3000",
    },
  ]);
}

async function fulfillJson(route: Route, body: unknown, status = 200): Promise<void> {
  await route.fulfill({
    status,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

const ticket = {
  id: "ticket-1",
  company_id: "company-1",
  subject: "Porta bloqueada",
  description: "A equipa não consegue entrar.",
  status: "Open",
  assigned_to: null,
  created_by_user_id: "client-user-1",
  created_by_role: "Client",
  created_at: "2026-05-25T10:00:00Z",
  updated_at: "2026-05-25T10:00:00Z",
  messages: [
    {
      id: "message-1",
      author_user_id: "client-user-1",
      author_role: "Client",
      content: "Precisamos de ajuda.",
      created_at: "2026-05-25T10:01:00Z",
    },
  ],
};

test.describe("remaining UI workflow coverage", () => {
  test.beforeEach(async ({ context }) => {
    await context.clearCookies();
  });

  test("staff can open, assign, and reply to support tickets", async ({ context, page }) => {
    await seedSession(page, context);
    let patchSeen = false;
    let replySeen = false;

    await page.route("**/api/tickets/", (route) => fulfillJson(route, [ticket]));
    await page.route("**/api/tickets/ticket-1/", async (route) => {
      if (route.request().method() === "PATCH") {
        patchSeen = true;
        return fulfillJson(route, { ...ticket, assigned_to: "staff-user-1" });
      }
      return fulfillJson(route, ticket);
    });
    await page.route("**/api/tickets/ticket-1/messages/", async (route) => {
      replySeen = true;
      return fulfillJson(
        route,
        {
          id: "message-2",
          author_user_id: "staff-user-1",
          author_role: "Staff",
          content: "Vamos verificar.",
          created_at: "2026-05-25T10:05:00Z",
        },
        201,
      );
    });
    await page.route("**/api/auth/users/", (route) =>
      fulfillJson(route, [
        {
          id: "staff-user-1",
          email: "staff@test.local",
          role: "Staff",
          first_name: "Staff",
          last_name: "One",
          company_id: null,
          is_active: true,
        },
      ]),
    );

    await page.goto("/tickets?status=Open");
    await expect(page.getByRole("cell", { name: "Porta bloqueada" })).toBeVisible();
    await page.getByRole("button", { name: "Abrir" }).click();
    await expect(page.getByRole("heading", { name: "Porta bloqueada" })).toBeVisible();

    await page.getByRole("combobox", { name: "Atribuir colaborador" }).click();
    await page.getByText("Staff One").click();
    await page.getByRole("button", { name: "Atualizar" }).click();
    await expect.poll(() => patchSeen).toBe(true);

    await page.getByPlaceholder("Escrever resposta…").fill("Vamos verificar.");
    await page.getByRole("button", { name: "Enviar resposta" }).click();
    await expect.poll(() => replySeen).toBe(true);
  });
});
