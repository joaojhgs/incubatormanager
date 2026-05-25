"use client";

import type { ColumnsType } from "antd/es/table";
import { Card, Result, Spin, Table, Tag, Typography } from "antd";

import { useTickets } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Ticket } from "@/lib/hooks/useTickets";

const { Title, Text } = Typography;

function statusTag(status: string) {
  if (status === "Open") return <Tag color="red">{tStaff("ticketStatusOpen")}</Tag>;
  if (status === "In progress") return <Tag color="blue">{tStaff("ticketStatusInProgress")}</Tag>;
  if (status === "Waiting response")
    return <Tag color="gold">{tStaff("ticketStatusWaitingResponse")}</Tag>;
  if (status === "Resolved") return <Tag color="green">{tStaff("ticketStatusResolved")}</Tag>;
  if (status === "Closed") return <Tag color="default">{tStaff("ticketStatusClosed")}</Tag>;
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
    title: tStaff("ticketsColumnCompany"),
    dataIndex: "company_id",
    key: "company_id",
    width: 220,
  },
  {
    title: tStaff("ticketsColumnSubject"),
    dataIndex: "subject",
    key: "subject",
    width: 260,
  },
  {
    title: tStaff("ticketsColumnStatus"),
    dataIndex: "status",
    key: "status",
    width: 160,
    render: (status: string) => statusTag(status),
  },
  {
    title: tStaff("ticketsColumnOwner"),
    key: "owner",
    width: 180,
    render: (_: unknown, row: Ticket) => (
      <Text>
        {row.created_by_user_id}
        <br />
        <Text type="secondary">{row.created_by_role}</Text>
      </Text>
    ),
  },
  {
    title: tStaff("ticketsColumnUpdatedAt"),
    dataIndex: "updated_at",
    key: "updated_at",
    render: (value: string) => formatDate(value),
  },
];

export default function TicketsPage() {
  const { data, isLoading, isError } = useTickets();

  if (isLoading) {
    return <Spin size="large" tip={tStaff("pageLoading") ?? tStaff("serviceHealthLoading")} />;
  }

  if (isError) {
    return <Result status="error" title={tStaff("ticketsLoadError")} />;
  }

  return (
    <>
      <Title level={3}>{tStaff("ticketsListTitle")}</Title>
      <Card>
        <Table<Ticket>
          rowKey={rowKey}
          columns={columns}
          dataSource={data ?? []}
          locale={{ emptyText: tStaff("ticketsEmpty") }}
          pagination={false}
        />
      </Card>
    </>
  );
}
