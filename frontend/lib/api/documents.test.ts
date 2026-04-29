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
  DOCUMENT_UPLOAD_MAX_BYTES,
  isSupportedDocumentMimeType,
  isSupportedDocumentSize,
  uploadDocument,
} from "./documents";

const BASE = "http://127.0.0.1:9";
const BASE_PATH = "/api";

afterEach(() => {
  nock.cleanAll();
  nock.enableNetConnect();
});

beforeEach(() => {
  nock.disableNetConnect();
  const client = createApiClient({ baseURL: `${BASE}${BASE_PATH}` });
  vi.mocked(getDefaultApiClient).mockReturnValue(client);
});

describe("uploadDocument", () => {
  it("POST /documents/upload/", async () => {
    const response = {
      id: "6d767fd5-7e21-4f07-8965-5e6c6fe2a2dc",
      entity_type: "Company",
      entity_id: "0458f113-bef8-46fd-b327-7d260f5daa52",
      file_name: "terms.pdf",
      file_size: 4,
      mime_type: "application/pdf",
      uploaded_at: "2026-04-29T10:00:00Z",
    };
    nock(BASE).post(`${BASE_PATH}/documents/upload/`).reply(201, response);

    const file = new Blob(["pdf"], { type: "application/pdf" }) as File;
    Object.defineProperty(file, "name", { value: "terms.pdf" });
    await expect(
      uploadDocument({
        entityType: "Company",
        entityId: "0458f113-bef8-46fd-b327-7d260f5daa52",
        file,
      }),
    ).resolves.toEqual(response);
    expect(nock.isDone()).toBe(true);
  });
});

describe("document client validation helpers", () => {
  it("accepts allowed document MIME types", () => {
    expect(isSupportedDocumentMimeType("application/pdf")).toBe(true);
    expect(isSupportedDocumentMimeType("image/png")).toBe(true);
    expect(isSupportedDocumentMimeType("application/json")).toBe(false);
  });

  it("enforces max payload size", () => {
    expect(isSupportedDocumentSize(DOCUMENT_UPLOAD_MAX_BYTES)).toBe(true);
    expect(isSupportedDocumentSize(DOCUMENT_UPLOAD_MAX_BYTES + 1)).toBe(false);
  });
});
