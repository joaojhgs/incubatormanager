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
import { addTicketMessage, createTicket, getTicket } from "./tickets";

const BASE = "http://127.0.0.1:9";
const BASE_PATH = "/api";

const ticketResponse = {
  id: "7e4ec982-f8f7-407b-849b-3057f3a88180",
  company_id: "cb0d7550-2622-43c7-a8a9-5a0054e16e84",
  subject: "Air conditioning issue",
  description: "Room is too warm.",
  status: "Open",
  assigned_to: null,
  created_by_user_id: "aaa2ec43-cf90-49ee-9474-4c871b4604f3",
  created_by_role: "Client",
  created_at: "2026-05-25T10:00:00Z",
  updated_at: "2026-05-25T10:00:00Z",
  messages: [],
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

describe("ticket API", () => {
  it("POST /tickets/ with a client ticket payload", async () => {
    nock(BASE)
      .post(`${BASE_PATH}/tickets/`, {
        subject: ticketResponse.subject,
        description: ticketResponse.description,
      })
      .reply(201, ticketResponse);

    await expect(
      createTicket({ subject: ticketResponse.subject, description: ticketResponse.description }),
    ).resolves.toEqual(ticketResponse);
    expect(nock.isDone()).toBe(true);
  });

  it("GET /tickets/:id/ returns ticket detail with messages", async () => {
    const response = {
      ...ticketResponse,
      messages: [
        {
          id: "b6d9d3dd-5d70-4599-b2a7-2089eb51c12d",
          author_user_id: ticketResponse.created_by_user_id,
          author_role: "Client",
          content: "Initial question",
          created_at: "2026-05-25T10:01:00Z",
        },
      ],
    };
    nock(BASE).get(`${BASE_PATH}/tickets/${ticketResponse.id}/`).reply(200, response);

    await expect(getTicket(ticketResponse.id)).resolves.toEqual(response);
    expect(nock.isDone()).toBe(true);
  });

  it("POST /tickets/:id/messages/ appends a thread message", async () => {
    const response = {
      id: "b6d9d3dd-5d70-4599-b2a7-2089eb51c12d",
      author_user_id: ticketResponse.created_by_user_id,
      author_role: "Client",
      content: "Can you share an update?",
      created_at: "2026-05-25T10:05:00Z",
    };
    nock(BASE)
      .post(`${BASE_PATH}/tickets/${ticketResponse.id}/messages/`, {
        content: response.content,
      })
      .reply(201, response);

    await expect(
      addTicketMessage(ticketResponse.id, { content: response.content }),
    ).resolves.toEqual(response);
    expect(nock.isDone()).toBe(true);
  });
});
