import { expect, test, type BrowserContext, type Page, type Route } from "@playwright/test";
import { SignJWT } from "jose";

const secret = new TextEncoder().encode("e2e-playwright-secret");
const refreshCookieName = "ilb.refresh_token";
const accessStorageKey = "ilb.access_token";
const companyId = "company-qa-001";

async function mintPair(
  role: "director" | "client",
  claims: Record<string, string> = {},
): Promise<{ access: string; refresh: string }> {
  const sub = claims.sub ?? "00000000-0000-4000-8000-000000000099";
  const access = await new SignJWT({ role, token_type: "access", ...claims })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(sub)
    .setExpirationTime("15m")
    .sign(secret);
  const refresh = await new SignJWT({ role, token_type: "refresh", ...claims })
    .setProtectedHeader({ alg: "HS256" })
    .setSubject(sub)
    .setExpirationTime("7d")
    .sign(secret);
  return { access, refresh };
}

async function seedSession(
  page: Page,
  context: BrowserContext,
  role: "director" | "client",
  claims: Record<string, string> = {},
): Promise<void> {
  const { access, refresh } = await mintPair(role, claims);
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

async function fulfillJson(route: Route, body: unknown): Promise<void> {
  await route.fulfill({
    status: 200,
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

test.describe("QA hardening smoke coverage", () => {
  test.beforeEach(async ({ context }) => {
    await context.clearCookies();
  });

  test("staff dashboard renders cross-service aggregates from mocked gateway APIs", async ({
    context,
    page,
  }) => {
    await seedSession(page, context, "director", { email: "director@test.local" });

    await page.route(/\/api\/companies\/(?:\?|$)/, (route) =>
      fulfillJson(route, { count: 2, next: null, previous: null, results: [] }),
    );
    await page.route("**/api/contracts/", (route) =>
      fulfillJson(route, [
        {
          id: "contract-1",
          company_id: companyId,
          space_id: "space-1",
          status: "Active",
          area_sqm: "32.00",
          rate_per_sqm: "20.00",
          monthly_fee: "640.00",
          start_date: "2026-05-01",
          end_date: "2027-05-01",
          termination_reason: "",
          created_at: "2026-05-01T09:00:00Z",
          updated_at: "2026-05-01T09:00:00Z",
        },
      ]),
    );
    await page.route("**/api/bookings/", (route) =>
      fulfillJson(route, [
        {
          id: "booking-1",
          company_id: companyId,
          space_id: "space-1",
          created_by_user_id: null,
          created_by_role: "Client",
          is_public: false,
          requester_name: "QA Client",
          requester_email: "client@test.local",
          requester_phone: "+351900000001",
          start_time: "2026-05-26T10:00:00Z",
          end_time: "2026-05-26T11:00:00Z",
          quoted_price: "25.00",
          equipment_ids: [],
          status: "Pending",
          notes: "",
          created_at: "2026-05-20T09:00:00Z",
          updated_at: "2026-05-20T09:00:00Z",
        },
      ]),
    );
    await page.route("**/api/spaces/occupancy-map/", (route) =>
      fulfillJson(route, [
        {
          space_id: "space-1",
          space_name: "Sala 1",
          capacity: 8,
          occupied: 4,
          occupancy_percent: "50.00",
          status: "Occupied",
        },
      ]),
    );
    await page.route("**/api/inventory/equipment/", (route) =>
      fulfillJson(route, [
        {
          id: "equipment-1",
          name: "Projetor QA",
          equipment_type: "Projector",
          serial_number: "QA-001",
          assigned_space_id: "space-1",
          rental_cost: "10.00",
          status: "Available",
          notes: "",
          is_active: true,
          created_at: "2026-05-20T09:00:00Z",
          updated_at: "2026-05-20T09:00:00Z",
        },
      ]),
    );
    await page.route("**/api/tickets/", (route) =>
      fulfillJson(route, [
        {
          id: "ticket-1",
          company_id: companyId,
          subject: "Acesso à sala",
          description: "Precisa de validação.",
          status: "Open",
          created_by_user_id: "client-user-1",
          created_by_role: "Client",
          created_at: "2026-05-20T09:00:00Z",
          updated_at: "2026-05-20T09:00:00Z",
        },
      ]),
    );
    await page.route("**/api/finance/dashboard/", (route) =>
      fulfillJson(route, {
        total_payments: 3,
        total_amount: "1250.00",
        paid: 1,
        paid_amount: "500.00",
        pending: 1,
        pending_amount: "250.00",
        overdue: 1,
        overdue_amount: "500.00",
      }),
    );

    await page.goto("/dashboard");

    await expect(page.getByText("Resumo financeiro")).toBeVisible();
    await expect(page.getByText("Reservas pendentes")).toBeVisible();
    await expect(page.getByText("Pedidos abertos")).toBeVisible();
    await expect(page.getByText("Valor em atraso")).toBeVisible();
    await expect(page.getByText("500.00").first()).toBeVisible();
  });

  test("client portal keeps company-scoped requests on the authenticated company id", async ({
    context,
    page,
  }) => {
    await seedSession(page, context, "client", {
      email: "client@test.local",
      company_id: companyId,
    });

    const requestedUrls: string[] = [];
    await page.route("**/api/contracts/company/**", (route) => {
      requestedUrls.push(route.request().url());
      return fulfillJson(route, [
        {
          id: "contract-1",
          company_id: companyId,
          space_id: "space-1",
          status: "Active",
          area_sqm: "32.00",
          rate_per_sqm: "20.00",
          monthly_fee: "640.00",
          start_date: "2026-05-01",
          end_date: "2027-05-01",
          termination_reason: "",
          created_at: "2026-05-01T09:00:00Z",
          updated_at: "2026-05-01T09:00:00Z",
        },
      ]);
    });
    await page.route("**/api/finance/payments/company/**", (route) => {
      requestedUrls.push(route.request().url());
      return fulfillJson(route, [
        {
          id: "payment-1",
          company_id: companyId,
          contract_id: "contract-1",
          booking_id: null,
          source: "Monthly billing",
          amount: "640.00",
          currency: "EUR",
          status: "Pending",
          due_date: "2026-06-01",
          paid_at: null,
          period_start: "2026-06-01",
          period_end: "2026-06-30",
          reference_id: "invoice-1",
          created_at: "2026-05-20T09:00:00Z",
          updated_at: "2026-05-20T09:00:00Z",
        },
      ]);
    });
    await page.route("**/api/bookings/my/", (route) => fulfillJson(route, []));
    await page.route("**/api/tickets/my/", (route) => fulfillJson(route, []));
    await page.route("**/api/spaces/", (route) =>
      fulfillJson(route, [
        {
          id: "space-1",
          name: "Sala de Reunião",
          space_type: "type-1",
          capacity: 8,
          status: "Available",
          company_id: null,
          is_active: true,
          created_at: "2026-05-01T09:00:00Z",
          updated_at: "2026-05-01T09:00:00Z",
        },
      ]),
    );

    await page.goto("/portal");

    await expect(page.getByText("Bem-vindo, client")).toBeVisible();
    await expect(page.getByText(companyId)).toBeVisible();
    await expect(page.getByText("Mensalidade").first()).toBeVisible();
    expect(requestedUrls).toEqual(
      expect.arrayContaining([
        expect.stringContaining(`/api/contracts/company/${companyId}/`),
        expect.stringContaining(`/api/finance/payments/company/${companyId}/`),
      ]),
    );
  });

  test("staff inventory correlates spaces, booking records, and equipment assignments", async ({
    context,
    page,
  }) => {
    await seedSession(page, context, "director", { email: "director@test.local" });

    await page.route("**/api/inventory/equipment/", (route) =>
      fulfillJson(route, [
        {
          id: "equipment-1",
          name: "Projetor QA",
          equipment_type: "Projector",
          serial_number: "QA-001",
          assigned_space_id: "space-1",
          rental_cost: "10.00",
          status: "In use",
          notes: "Reservado para demonstrações",
          is_active: true,
          created_at: "2026-05-20T09:00:00Z",
          updated_at: "2026-05-25T11:00:00Z",
        },
      ]),
    );
    await page.route("**/api/inventory/equipment-types/", (route) =>
      fulfillJson(route, [
        {
          id: "type-1",
          name: "Projector",
          is_active: true,
          created_at: "2026-05-20T09:00:00Z",
          updated_at: "2026-05-20T09:00:00Z",
        },
      ]),
    );
    await page.route("**/api/spaces/", (route) =>
      fulfillJson(route, [
        {
          id: "space-1",
          name: "Sala 1",
          space_type: "Meeting",
          capacity: 8,
          status: "Reserved",
          company_id: companyId,
          is_active: true,
          created_at: "2026-05-20T09:00:00Z",
          updated_at: "2026-05-25T09:00:00Z",
        },
      ]),
    );
    await page.route(/\/api\/companies\/(?:\?|$)/, (route) =>
      fulfillJson(route, {
        count: 1,
        next: null,
        previous: null,
        results: [
          {
            id: companyId,
            name: "Empresa QA",
            tax_id: "501000001",
            address: null,
            phone: null,
            email: null,
            legal_representative: "QA Rep",
            description: null,
            is_active: true,
            created_at: "2026-05-20T09:00:00Z",
            updated_at: "2026-05-20T09:00:00Z",
            cae: { id: "cae-1", code: "62010", description: "Software" },
            maturity_stage: {
              id: "stage-1",
              name: "Startup",
              rate_per_sqm: 10,
              description: "Startup",
              display_order: 1,
            },
          },
        ],
      }),
    );
    await page.route("**/api/spaces/bookings/records/", (route) =>
      fulfillJson(route, [
        {
          id: "booking-1",
          space_id: "space-1",
          company_id: companyId,
          status: "Approved",
          start_time: "2026-05-26T10:00:00Z",
          end_time: "2026-05-26T11:00:00Z",
          quoted_price: "25.00",
          equipment_ids: ["equipment-1"],
        },
      ]),
    );
    await page.route("**/api/inventory/assignments/", (route) =>
      fulfillJson(route, [
        {
          id: "assignment-1",
          equipment_id: "equipment-1",
          equipment_name: "Projetor QA",
          booking_id: "booking-1",
          company_id: companyId,
          assigned_space_id: "space-1",
          status: "Assigned",
          created_at: "2026-05-25T10:00:00Z",
          updated_at: "2026-05-25T11:00:00Z",
        },
      ]),
    );

    await page.goto("/inventory");

    await expect(page.getByText("Inventário por espaço e reservas")).toBeVisible({
      timeout: 15_000,
    });
    await expect(page.getByText("Sala 1").first()).toBeVisible();
    await expect(page.getByText("Projetor QA").first()).toBeVisible();
    await expect(page.getByText("Histórico recente de atribuições")).toBeVisible();
    await expect(page.getByRole("link", { name: /Sala 1/ })).toBeVisible();
    await expect(page.getByRole("link", { name: /Empresa QA/ })).toHaveAttribute(
      "href",
      /\/bookings\?booking=booking-1/,
    );
  });

  test("public booking request remains unauthenticated and validates required fields", async ({
    page,
  }) => {
    await page.route("**/api/public/spaces/", (route) =>
      fulfillJson(route, [
        {
          id: "space-1",
          name: "Sala de Reunião",
          space_type: "Meeting",
          capacity: 8,
          rental_cost: "12.00",
          rental_cost_unit: "hour",
          status: "Available",
          company_id: null,
          is_active: true,
          created_at: "2026-05-20T09:00:00Z",
          updated_at: "2026-05-20T09:00:00Z",
        },
      ]),
    );
    await page.route("**/api/public/inventory/equipment/", (route) => fulfillJson(route, []));
    await page.route("**/api/bookings/public-calendar/", (route) => fulfillJson(route, []));

    await page.goto("/booking-request");

    await expect(page.getByText("Pedido público de reserva")).toBeVisible();
    await expect(
      page.getByText("Submeta um pedido de reserva para análise pela equipa da incubadora."),
    ).toBeVisible();
    await page.getByRole("combobox", { name: "Espaço" }).click();
    await expect(page.getByText(/Sala de Reunião .* 8 pessoas/)).toBeVisible();

    await page.getByRole("button", { name: "Submeter pedido" }).click();

    await expect(page.getByText("Indique o nome do requerente.")).toBeVisible();
  });
});
