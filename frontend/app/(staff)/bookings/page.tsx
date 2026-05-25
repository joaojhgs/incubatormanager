"use client";

import {
  Alert,
  Button,
  Card,
  Descriptions,
  Result,
  Select,
  Space,
  Spin,
  Table,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useMemo, useState } from "react";

import { formatCurrency, formatDateTime, statusTag } from "@/components/operations/format";
import {
  useBookingActions,
  useBookingCalendar,
  useBookings,
  useEquipment,
  useSpaces,
} from "@/lib/hooks";
import type { Booking, BookingCalendarEvent } from "@/lib/api/bookings";
import { tStaff } from "@/lib/i18n/staffNav";

function byId<T extends { id: string; name?: string }>(items: T[] | undefined) {
  return new Map((items ?? []).map((item) => [item.id, item.name ?? item.id]));
}

export default function BookingsPage() {
  const { data, isLoading, isError } = useBookings();
  const calendar = useBookingCalendar();
  const spaces = useSpaces();
  const equipment = useEquipment();
  const actions = useBookingActions();
  const [selectedEquipmentByBooking, setSelectedEquipmentByBooking] = useState<
    Record<string, string[]>
  >({});

  const spaceNames = useMemo(() => byId(spaces.data), [spaces.data]);
  const equipmentNames = useMemo(() => byId(equipment.data), [equipment.data]);
  const equipmentOptions = useMemo(
    () =>
      (equipment.data ?? []).map((item) => ({
        label: `${item.name}${item.serial_number ? ` · ${item.serial_number}` : ""}`,
        value: item.id,
        disabled: item.status !== "Available" && item.status !== "In use",
      })),
    [equipment.data],
  );

  const columns: ColumnsType<Booking> = [
    { title: tStaff("columnCompany"), dataIndex: "company_id", key: "company_id", width: 210 },
    {
      title: tStaff("columnSpace"),
      dataIndex: "space_id",
      key: "space_id",
      width: 210,
      render: (spaceId: string) => spaceNames.get(spaceId) ?? spaceId,
    },
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
      title: tStaff("bookingEquipmentPicker"),
      key: "equipment",
      width: 300,
      render: (_: unknown, row) => (
        <Select
          mode="multiple"
          allowClear
          size="small"
          maxTagCount="responsive"
          placeholder={tStaff("bookingEquipmentPlaceholder")}
          value={selectedEquipmentByBooking[row.id] ?? row.equipment_ids}
          options={equipmentOptions}
          disabled={row.status !== "Pending" || actions.approve.isPending}
          onChange={(equipmentIds) =>
            setSelectedEquipmentByBooking((current) => ({ ...current, [row.id]: equipmentIds }))
          }
          style={{ minWidth: 260 }}
        />
      ),
    },
    {
      title: tStaff("bookingActions"),
      key: "actions",
      fixed: "right",
      render: (_: unknown, row) => (
        <Space>
          <Button
            size="small"
            type="primary"
            onClick={() =>
              actions.approve.mutate({
                id: row.id,
                payload: { equipment_ids: selectedEquipmentByBooking[row.id] ?? row.equipment_ids },
              })
            }
            disabled={row.status !== "Pending"}
            loading={actions.approve.isPending}
          >
            {tStaff("bookingApprove")}
          </Button>
          <Button
            size="small"
            onClick={() => actions.reject.mutate(row.id)}
            disabled={row.status !== "Pending"}
            loading={actions.reject.isPending}
          >
            {tStaff("bookingReject")}
          </Button>
          <Button
            size="small"
            danger
            onClick={() => actions.cancel.mutate(row.id)}
            disabled={!["Pending", "Approved"].includes(row.status)}
            loading={actions.cancel.isPending}
          >
            {tStaff("bookingCancel")}
          </Button>
        </Space>
      ),
    },
  ];

  const calendarColumns: ColumnsType<BookingCalendarEvent> = [
    {
      title: tStaff("columnSpace"),
      dataIndex: "space_id",
      key: "space_id",
      render: (spaceId: string) => spaceNames.get(spaceId) ?? spaceId,
    },
    {
      title: tStaff("columnStart"),
      dataIndex: "start_time",
      key: "start_time",
      render: formatDateTime,
    },
    { title: tStaff("columnEnd"), dataIndex: "end_time", key: "end_time", render: formatDateTime },
  ];

  if (isLoading || calendar.isLoading || spaces.isLoading || equipment.isLoading) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (isError || calendar.isError || spaces.isError || equipment.isError) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  const pendingCount = data?.filter((booking) => booking.status === "Pending").length ?? 0;
  const approvedCount = data?.filter((booking) => booking.status === "Approved").length ?? 0;
  const calendarEvents = [...(calendar.data ?? [])]
    .sort((a, b) => new Date(a.start_time).getTime() - new Date(b.start_time).getTime())
    .slice(0, 6);

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Alert
        type="info"
        showIcon
        message={tStaff("bookingOpsSummary")}
        description={`${pendingCount} ${tStaff("bookingPendingCount")}; ${approvedCount} ${tStaff("bookingApprovedCount")}.`}
      />
      <Card title={tStaff("bookingCalendarTitle")}>
        <Table<BookingCalendarEvent>
          rowKey="id"
          columns={calendarColumns}
          dataSource={calendarEvents}
          locale={{ emptyText: tStaff("bookingCalendarEmpty") }}
          pagination={false}
          size="small"
        />
      </Card>
      <Card title={tStaff("navBookings")}>
        <Table<Booking>
          rowKey="id"
          columns={columns}
          dataSource={data ?? []}
          locale={{ emptyText: tStaff("emptyData") }}
          scroll={{ x: 1200 }}
          expandable={{
            expandedRowRender: (row) => (
              <Descriptions size="small" column={1} bordered>
                <Descriptions.Item label={tStaff("bookingRequester")}>
                  <Space direction="vertical" size={0}>
                    <Typography.Text>{row.requester_name || "—"}</Typography.Text>
                    <Typography.Text type="secondary">{row.requester_email || "—"}</Typography.Text>
                    <Typography.Text type="secondary">{row.requester_phone || "—"}</Typography.Text>
                  </Space>
                </Descriptions.Item>
                <Descriptions.Item label={tStaff("bookingEquipmentSelected")}>
                  {row.equipment_ids.length > 0
                    ? row.equipment_ids.map((id) => equipmentNames.get(id) ?? id).join(", ")
                    : tStaff("bookingNoEquipment")}
                </Descriptions.Item>
                <Descriptions.Item label={tStaff("bookingNotes")}>
                  {row.notes || "—"}
                </Descriptions.Item>
              </Descriptions>
            ),
          }}
        />
      </Card>
    </Space>
  );
}
