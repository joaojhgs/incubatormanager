"use client";

import type { ColumnsType } from "antd/es/table";
import { Card, Result, Spin, Table, Tag, Typography } from "antd";

import { useMyTickets } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";
import type { Ticket } from "@/lib/hooks/useTickets";

const { Text } = Typography;

function statusTag(status: string) {
  if (status === "Open") return <Tag color="red">{tClient("portalTicketStatusOpen")}</Tag>;
  if (status === "In progress")
    return <Tag color="blue">{tClient("portalTicketStatusInProgress")}</Tag>;
  if (status === "Waiting response")
    return <Tag color="gold">{tClient("portalTicketStatusWaitingResponse")}</Tag>;
  if (status === "Resolved")
    return <Tag color="green">{tClient("portalTicketStatusResolved")}</Tag>;
  if (status === "Closed") return <Tag color="default">{tClient("portalTicketStatusClosed")}</Tag>;
  return <Tag>{status}</Tag>;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-PT", { dateStyle: "short", timeStyle: "short" });
}

function rowKey(row: Ticket): string {
  return row.id;
}

const columns: ColumnsType<Ticket> = [
  {
    title: tClient("portalTicketsColumnSubject"),
    dataIndex: "subject",
    key: "subject",
    width: 260,
  },
  {
    title: tClient("portalTicketsColumnStatus"),
    dataIndex: "status",
    key: "status",
    width: 160,
    render: (status: string) => statusTag(status),
  },
  {
    title: tClient("portalTicketsColumnUpdatedAt"),
    dataIndex: "updated_at",
    key: "updated_at",
    render: (value: string) => formatDate(value),
  },
];

export default function ClientTicketsPage() {
  const { data, isLoading, isError } = useMyTickets();

  if (isLoading) {
    return <Spin size="large" tip={tClient("pageLoading")} />;
  }

  if (isError) {
    return <Result status="error" title={tClient("portalTicketsLoadError")} />;
  }

  return (
    <Card title={tClient("portalTicketsTitle")}>
      <Table<Ticket>
        rowKey={rowKey}
        columns={columns}
        dataSource={data ?? []}
        pagination={false}
        locale={{ emptyText: tClient("portalTicketsEmpty") }}
      />
    </Card>
  );
}
