"use client";

import { UploadOutlined } from "@ant-design/icons";
import type { UploadRequestOption } from "rc-upload/lib/interface";
import { Button, Upload, message } from "antd";
import type { UploadProps } from "antd";

import {
  ALLOWED_DOCUMENT_MIME_TYPES,
  DOCUMENT_UPLOAD_MAX_BYTES,
  isSupportedDocumentMimeType,
  isSupportedDocumentSize,
  type DocumentEntityType,
  type DocumentMetadata,
  uploadDocument,
} from "@/lib/api/documents";
import { tDocuments } from "@/lib/i18n/documents";

interface DocumentUploadProps {
  entityType: DocumentEntityType;
  entityId: string;
  description?: string;
  disabled?: boolean;
  maxBytes?: number;
  onUploaded?: (documentId: string, document: DocumentMetadata) => void;
}

function toMbLabel(bytes: number): string {
  return `${Math.round(bytes / (1024 * 1024))} MB`;
}

function parseApiError(err: unknown): string | null {
  if (!err || typeof err !== "object" || !("response" in err)) return null;
  const data = (err as { response?: { data?: unknown } }).response?.data;
  if (!data || typeof data !== "object" || !("detail" in data)) return null;
  const detail = (data as { detail?: unknown }).detail;
  return typeof detail === "string" && detail.trim() ? detail : null;
}

export function DocumentUpload({
  entityType,
  entityId,
  description,
  disabled = false,
  maxBytes = DOCUMENT_UPLOAD_MAX_BYTES,
  onUploaded,
}: DocumentUploadProps) {
  const accept = ALLOWED_DOCUMENT_MIME_TYPES.join(",");

  const beforeUpload: UploadProps["beforeUpload"] = (file) => {
    if (!isSupportedDocumentMimeType(file.type)) {
      message.error(tDocuments("uploadErrorMime"));
      return Upload.LIST_IGNORE;
    }
    if (!isSupportedDocumentSize(file.size, maxBytes)) {
      message.error(tDocuments("uploadErrorTooLarge").replace("{maxSize}", toMbLabel(maxBytes)));
      return Upload.LIST_IGNORE;
    }
    return true;
  };

  const customRequest = async (options: UploadRequestOption) => {
    const uploadFile = options.file as File;
    if (!isSupportedDocumentMimeType(uploadFile.type)) {
      const err = new Error(tDocuments("uploadErrorMime"));
      message.error(err.message);
      options.onError?.(err);
      return;
    }
    if (!isSupportedDocumentSize(uploadFile.size, maxBytes)) {
      const err = new Error(
        tDocuments("uploadErrorTooLarge").replace("{maxSize}", toMbLabel(maxBytes)),
      );
      message.error(err.message);
      options.onError?.(err);
      return;
    }

    try {
      const document = await uploadDocument({
        entityType,
        entityId,
        file: uploadFile,
        description,
        onUploadProgress: (event) => {
          const total = event.total ?? uploadFile.size;
          if (!total) return;
          const percent = Math.round((event.loaded / total) * 100);
          options.onProgress?.({ percent });
        },
      });
      message.success(tDocuments("uploadSuccess"));
      options.onSuccess?.(document);
      onUploaded?.(document.id, document);
    } catch (err) {
      const detail = parseApiError(err);
      message.error(detail ?? tDocuments("uploadErrorGeneric"));
      options.onError?.(err as Error);
    }
  };

  return (
    <Upload
      accept={accept}
      maxCount={1}
      showUploadList={{ showRemoveIcon: false }}
      beforeUpload={beforeUpload}
      customRequest={(opts) => {
        void customRequest(opts);
      }}
      disabled={disabled}
    >
      <Button icon={<UploadOutlined aria-hidden />} disabled={disabled}>
        {tDocuments("uploadButton")}
      </Button>
    </Upload>
  );
}
