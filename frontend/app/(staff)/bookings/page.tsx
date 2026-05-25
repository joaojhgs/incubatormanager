"use client";

import { Button, Card, Result, Space, Spin, Table } from "antd";
import type { ColumnsType } from "antd/es/table";

import { formatCurrency, formatDateTime, statusTag } from "@/components/operations/format";
import { useBookingActions, useBookings } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Booking } from "@/lib/api/bookings";

export default function BookingsPage() {
  const { data, isLoading, isError } = useBookings();
  const actions = useBookingActions();

  const columns: ColumnsType<Booking> = [
    { title: tStaff("columnCompany"), dataIndex: "company_id", key: "company_id", width: 210 },
    { title: tStaff("columnSpace"), dataIndex: "space_id", key: "space_id", width: 210 },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    {
      title: tStaff("columnStart"),
      dataIndex: "start_time",
      key: "start_time",
      render: formatDateTime,
    },
    { title: tStaff("columnEnd"), dataIndex: "end_time", key: "end_time", render: formatDateTime },
    {
      title: tStaff("columnPrice"),
      dataIndex: "quoted_price",
      key: "quoted_price",
      render: formatCurrency,
    },
    {
      title: tStaff("bookingActions"),
      key: "actions",
      render: (_: unknown, row) => (
        <Space>
          <Button size="small" onClick={() => actions.approve.mutate(row.id)} disabled={row.status !== "Pending"}>
            {tStaff("bookingApprove")}
          </Button>
          <Button size="small" onClick={() => actions.reject.mutate(row.id)} disabled={row.status !== "Pending"}>
            {tStaff("bookingReject")}
          </Button>
          <Button size="small" onClick={() => actions.cancel.mutate(row.id)} disabled={!['Pending','Approved'].includes(row.status)}>
            {tStaff("bookingCancel")}
          </Button>
        </Space>
      ),
    },
  ];

  if (isLoading) return <Spin size="large" tip={tStaff("pageLoading")} />;
  if (isError) return <Result status="error" title={tStaff("loadError")} />;

  return (
    <Card title={tStaff("navBookings")}>
      <Table<Booking> rowKey="id" columns={columns} dataSource={data ?? []} locale={{ emptyText: tStaff("emptyData") }} />
    </Card>
  );
}
