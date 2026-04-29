import type { AxiosProgressEvent } from "axios";

import { getDefaultApiClient } from "./client";

export const DOCUMENT_UPLOAD_MAX_BYTES = 20 * 1024 * 1024;

export const ALLOWED_DOCUMENT_MIME_TYPES = [
  "application/pdf",
  "image/jpeg",
  "image/png",
  "image/webp",
  "text/plain",
  "application/msword",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.openxmlformats-officedocument.presentationml.presentation",
] as const;

export type DocumentMimeType = (typeof ALLOWED_DOCUMENT_MIME_TYPES)[number];

export type DocumentEntityType = "Company" | "Contract";

export interface DocumentMetadata {
  id: string;
  entity_type: DocumentEntityType;
  entity_id: string;
  file_name: string;
  file_size: number;
  mime_type: string;
  description?: string;
  uploaded_by?: string | null;
  uploaded_at: string;
}

export interface UploadDocumentPayload {
  entityType: DocumentEntityType;
  entityId: string;
  file: File;
  description?: string;
  onUploadProgress?: (event: AxiosProgressEvent) => void;
}

const api = getDefaultApiClient;

export function isSupportedDocumentMimeType(mimeType: string): mimeType is DocumentMimeType {
  return ALLOWED_DOCUMENT_MIME_TYPES.includes(mimeType as DocumentMimeType);
}

export function isSupportedDocumentSize(
  sizeInBytes: number,
  maxBytes = DOCUMENT_UPLOAD_MAX_BYTES,
): boolean {
  return sizeInBytes <= maxBytes;
}

/** Upload a single document and return persisted metadata (includes generated id). */
export async function uploadDocument(payload: UploadDocumentPayload): Promise<DocumentMetadata> {
  const formData = new FormData();
  formData.append("file", payload.file);
  formData.append("entity_type", payload.entityType);
  formData.append("entity_id", payload.entityId);
  if (payload.description?.trim()) {
    formData.append("description", payload.description.trim());
  }

  const { data } = await api().post<DocumentMetadata>("/documents/upload/", formData, {
    onUploadProgress: payload.onUploadProgress,
  });
  return data;
}
