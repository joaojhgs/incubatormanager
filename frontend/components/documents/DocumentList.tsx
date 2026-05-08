"use client";

import { DeleteOutlined, DownloadOutlined, FileOutlined } from "@ant-design/icons";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Button, Popconfirm, Skeleton, Space, Table, Tooltip, Typography, message } from "antd";
import type { ColumnsType } from "antd/es/table";
import dayjs from "dayjs";
import { useState } from "react";

import {
  deleteDocument,
  downloadDocumentBlob,
  listDocuments,
  type DocumentEntityType,
  type DocumentMetadata,
} from "@/lib/api/documents";
import { tDocuments } from "@/lib/i18n/documents";

interface DocumentListProps {
  entityType: DocumentEntityType;
  entityId: string;
  /** Hide the delete action (e.g. for Client portal read-only views). */
  readOnly?: boolean;
  /** Called after a successful delete so the parent can react. */
  onDeleted?: (documentId: string) => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatDate(isoString: string): string {
  const d = dayjs(isoString);
  return d.isValid() ? d.format("DD/MM/YYYY HH:mm") : isoString;
}

function triggerBrowserDownload(blob: Blob, fileName: string): void {
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = fileName;
  document.body.appendChild(anchor);
  anchor.click();
  document.body.removeChild(anchor);
  URL.revokeObjectURL(url);
}

/** Table of documents for a company or contract; staff (or client read-only via `readOnly`). */
export function DocumentList({
  entityType,
  entityId,
  readOnly = false,
  onDeleted,
}: DocumentListProps) {
  const queryClient = useQueryClient();
  const queryKey = ["documents", entityType, entityId] as const;
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const { data, isLoading, isError } = useQuery({
    queryKey,
    queryFn: () => listDocuments({ entityType, entityId }),
    staleTime: 30_000,
    retry: 1,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteDocument(id),
    onSuccess: (_data, id) => {
      void queryClient.invalidateQueries({ queryKey });
      message.success(tDocuments("deleteSuccess"));
      onDeleted?.(id);
    },
    onError: () => {
      message.error(tDocuments("deleteError"));
    },
  });

  const handleDownload = async (doc: DocumentMetadata) => {
    setDownloadingId(doc.id);
    try {
      const { blob, fileName } = await downloadDocumentBlob(doc.id);
      triggerBrowserDownload(blob, fileName || doc.file_name);
    } catch {
      message.error(tDocuments("downloadError"));
    } finally {
      setDownloadingId(null);
    }
  };

  const columns: ColumnsType<DocumentMetadata> = [
    {
      title: tDocuments("colName"),
      dataIndex: "file_name",
      key: "file_name",
      ellipsis: true,
      render: (name: string) => (
        <Space>
          <FileOutlined aria-hidden />
          <Typography.Text ellipsis>{name}</Typography.Text>
        </Space>
      ),
    },
    {
      title: tDocuments("colSize"),
      dataIndex: "file_size",
      key: "file_size",
      width: 100,
      render: (size: number) => formatBytes(size),
    },
    {
      title: tDocuments("colDescription"),
      dataIndex: "description",
      key: "description",
      ellipsis: true,
      render: (desc?: string) => desc ?? tDocuments("valueEmpty"),
    },
    {
      title: tDocuments("colUploadedAt"),
      dataIndex: "uploaded_at",
      key: "uploaded_at",
      width: 140,
      render: (date: string) => formatDate(date),
    },
    {
      title: tDocuments("colActions"),
      key: "actions",
      width: readOnly ? 80 : 130,
      render: (_: unknown, doc: DocumentMetadata) => (
        <Space size="small">
          <Tooltip title={tDocuments("actionDownload")}>
            <Button
              type="text"
              size="small"
              icon={<DownloadOutlined aria-label={tDocuments("actionDownload")} />}
              loading={downloadingId === doc.id}
              onClick={() => {
                void handleDownload(doc);
              }}
            />
          </Tooltip>
          {!readOnly && (
            <Popconfirm
              title={tDocuments("deleteConfirm")}
              okText={tDocuments("deleteOk")}
              cancelText={tDocuments("deleteCancel")}
              okButtonProps={{ danger: true }}
              onConfirm={() => {
                deleteMutation.mutate(doc.id);
              }}
            >
              <Tooltip title={tDocuments("actionDelete")}>
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined aria-label={tDocuments("actionDelete")} />}
                  loading={deleteMutation.isPending && deleteMutation.variables === doc.id}
                />
              </Tooltip>
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  if (isLoading) {
    return <Skeleton active paragraph={{ rows: 3 }} />;
  }

  if (isError) {
    return <Typography.Text type="danger">{tDocuments("listLoadError")}</Typography.Text>;
  }

  return (
    <Table<DocumentMetadata>
      rowKey="id"
      columns={columns}
      dataSource={data ?? []}
      pagination={false}
      size="small"
      locale={{ emptyText: tDocuments("listEmpty") }}
    />
  );
}
