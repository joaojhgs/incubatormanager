"use client";

import { Button, Card, Result, Spin, Table } from "antd";
import type { ColumnsType } from "antd/es/table";
import Link from "next/link";

import { formatCurrency, formatDateTime, statusTag } from "@/components/operations/format";
import { useMyBookings } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";
import type { Booking } from "@/lib/api/bookings";

export default function ClientBookingsPage() {
  const { data, isLoading, isError } = useMyBookings();
  const columns: ColumnsType<Booking> = [
    { title: tClient("columnSpace"), dataIndex: "space_id", key: "space_id" },
    { title: tClient("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    {
      title: tClient("columnStart"),
      dataIndex: "start_time",
      key: "start_time",
      render: formatDateTime,
    },
    { title: tClient("columnEnd"), dataIndex: "end_time", key: "end_time", render: formatDateTime },
    {
      title: tClient("columnPrice"),
      dataIndex: "quoted_price",
      key: "quoted_price",
      render: formatCurrency,
    },
  ];

  if (isLoading) return <Spin size="large" tip={tClient("pageLoading")} />;
  if (isError) return <Result status="error" title={tClient("clientLoadError")} />;

  return (
    <Card
      title={tClient("pageBookingsTitle")}
      extra={
        <Link href="/portal/bookings/new">
          <Button type="primary">{tClient("bookingNewTitle")}</Button>
        </Link>
      }
    >
      <Table<Booking>
        rowKey="id"
        columns={columns}
        dataSource={data ?? []}
        locale={{ emptyText: tClient("bookingsEmpty") }}
      />
    </Card>
  );
}
