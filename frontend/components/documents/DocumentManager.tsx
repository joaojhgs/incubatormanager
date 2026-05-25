"use client";

import { Space } from "antd";
import { useQueryClient } from "@tanstack/react-query";

import { DocumentList } from "./DocumentList";
import { DocumentUpload } from "./DocumentUpload";
import type { DocumentEntityType } from "@/lib/api/documents";

interface DocumentManagerProps {
  entityType: DocumentEntityType;
  entityId: string;
  readOnly?: boolean;
}

export function DocumentManager({ entityType, entityId, readOnly = false }: DocumentManagerProps) {
  const queryClient = useQueryClient();
  const refresh = () => {
    void queryClient.invalidateQueries({ queryKey: ["documents", entityType, entityId] });
  };

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      {readOnly ? null : (
        <DocumentUpload entityType={entityType} entityId={entityId} onUploaded={refresh} />
      )}
      <DocumentList entityType={entityType} entityId={entityId} readOnly={readOnly} />
    </Space>
  );
}
