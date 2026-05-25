import nock from "nock";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./client", async (importOriginal) => {
  const mod = await importOriginal<typeof import("./client")>();
  return {
    ...mod,
    getDefaultApiClient: vi.fn(),
  };
});

import { createApiClient, getDefaultApiClient } from "./client";
import {
  createCompany,
  getCompany,
  listCAECodes,
  listCompanies,
  listMaturityStages,
} from "./companies";

const BASE = "http://127.0.0.1:9";
const BASE_PATH = "/api";

const cae = {
  id: "11111111-1111-4111-8111-111111111111",
  code: "62010",
  description: "Atividades de programação informática",
};
const stage = {
  id: "22222222-2222-4222-8222-222222222222",
  name: "Startup",
  rate_per_sqm: 12,
  description: "Early stage",
  display_order: 2,
};
const companyApiRow = {
  id: "33333333-3333-4333-8333-333333333333",
  name: "Acme Labs",
  tax_id: "PT123456789",
  address: "Rua Um",
  phone: "+351910000000",
  email: "hello@acme.test",
  legal_representative: "Ana Silva",
  description: "Incubated company",
  is_active: true,
  created_at: "2026-05-25T10:00:00Z",
  updated_at: "2026-05-25T10:00:00Z",
  cae,
  maturity_stage: stage,
};

afterEach(() => {
  nock.cleanAll();
  nock.enableNetConnect();
});

beforeEach(() => {
  nock.disableNetConnect();
  const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });
  vi.mocked(getDefaultApiClient).mockReturnValue(client);
});

describe("listCompanies", () => {
  it("GET /companies/ maps staff filters to backend query names and normalizes nested fields", async () => {
    nock(BASE)
      .get(`${BASE_PATH}/companies/`)
      .query({ page: "2", page_size: "20", cae: cae.id, maturity: stage.id, is_active: "true" })
      .reply(200, { count: 1, next: null, previous: null, results: [companyApiRow] });

    await expect(
      listCompanies({
        page: 2,
        page_size: 20,
        cae_id: cae.id,
        maturity_stage_id: stage.id,
        is_active: true,
      }),
    ).resolves.toMatchObject({
      count: 1,
      results: [
        {
          id: companyApiRow.id,
          cae_id: cae.id,
          cae_description: `${cae.code} — ${cae.description}`,
          maturity_stage_id: stage.id,
          maturity_stage_name: stage.name,
        },
      ],
    });
    expect(nock.isDone()).toBe(true);
  });
});

describe("getCompany", () => {
  it("GET /companies/{id}/ returns detail rows with employees", async () => {
    const response = {
      ...companyApiRow,
      employees: [
        {
          id: "44444444-4444-4444-8444-444444444444",
          name: "Bruno Costa",
          type: "Founder",
          start_date: "2026-01-01",
          end_date: null,
          is_active: true,
        },
      ],
    };
    nock(BASE).get(`${BASE_PATH}/companies/${companyApiRow.id}/`).reply(200, response);

    await expect(getCompany(companyApiRow.id)).resolves.toMatchObject({
      id: companyApiRow.id,
      employees: response.employees,
      cae_id: cae.id,
      maturity_stage_id: stage.id,
    });
    expect(nock.isDone()).toBe(true);
  });
});

describe("createCompany", () => {
  it("POST /companies/ translates frontend id fields to writable backend relation fields", async () => {
    nock(BASE)
      .post(`${BASE_PATH}/companies/`, {
        name: "Acme Labs",
        tax_id: "PT123456789",
        legal_representative: "Ana Silva",
        cae: cae.id,
        maturity_stage: stage.id,
        email: "hello@acme.test",
      })
      .reply(201, companyApiRow);

    await expect(
      createCompany({
        name: "Acme Labs",
        tax_id: "PT123456789",
        legal_representative: "Ana Silva",
        cae_id: cae.id,
        maturity_stage_id: stage.id,
        email: "hello@acme.test",
      }),
    ).resolves.toMatchObject({ id: companyApiRow.id, cae_id: cae.id, maturity_stage_id: stage.id });
    expect(nock.isDone()).toBe(true);
  });
});

describe("company option endpoints", () => {
  it("loads CAE and maturity-stage option lists from company-service paths", async () => {
    nock(BASE).get(`${BASE_PATH}/companies/cae/`).reply(200, [cae]);
    nock(BASE).get(`${BASE_PATH}/companies/maturity-stages/`).reply(200, [stage]);

    await expect(listCAECodes()).resolves.toEqual([cae]);
    await expect(listMaturityStages()).resolves.toEqual([stage]);
    expect(nock.isDone()).toBe(true);
  });
});
