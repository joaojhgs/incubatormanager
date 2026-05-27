"use client";

import { Button, Card, Descriptions, Result, Space, Spin, Table, Typography } from "antd";
import type { ColumnsType } from "antd/es/table";
import Link from "next/link";
import { useMemo } from "react";

import { formatCurrency, formatDateTime, statusTag } from "@/components/operations/format";
import type { Equipment } from "@/lib/api/inventory";
import type { Space as IncubatorSpace } from "@/lib/api/spaces";
import { useEquipment, useMyBookings, useSpaces } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";
import type { Booking } from "@/lib/api/bookings";
import { calculateRentalEstimate, formatMoney, rateLabel } from "@/lib/pricing";

function bookingDurationHours(booking: Booking): number {
  const start = new Date(booking.start_time);
  const end = new Date(booking.end_time);
  if (Number.isNaN(start.getTime()) || Number.isNaN(end.getTime()) || end <= start) return 0;
  return Math.round(((end.getTime() - start.getTime()) / 3_600_000) * 100) / 100;
}

function durationLabel(hours: number): string {
  if (hours <= 0) return "—";
  if (hours < 24) return `${hours}h`;
  const days = Math.floor(hours / 24);
  const remainingHours = Math.round((hours % 24) * 100) / 100;
  return remainingHours > 0 ? `${days}d ${remainingHours}h` : `${days}d`;
}

function equipmentSummary(booking: Booking, equipmentById: Map<string, Equipment>): string {
  if (!booking.equipment_ids.length) return "Sem equipamento";
  return booking.equipment_ids
    .map((id) => equipmentById.get(id)?.name ?? id)
    .slice(0, 3)
    .join(", ")
    .concat(booking.equipment_ids.length > 3 ? ` +${booking.equipment_ids.length - 3}` : "");
}

export default function ClientBookingsPage() {
  const { data, isLoading, isError } = useMyBookings();
  const spaces = useSpaces();
  const equipment = useEquipment();
  const spacesById = useMemo(
    () => new Map((spaces.data ?? []).map((space) => [space.id, space])),
    [spaces.data],
  );
  const equipmentById = useMemo(
    () => new Map((equipment.data ?? []).map((item) => [item.id, item])),
    [equipment.data],
  );
  const columns: ColumnsType<Booking> = [
    {
      title: tClient("columnSpace"),
      dataIndex: "space_id",
      key: "space_id",
      render: (spaceId: string) => {
        const space = spacesById.get(spaceId);
        return (
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{space?.name ?? spaceId}</Typography.Text>
            <Typography.Text type="secondary">
              {space ? `${space.capacity} pessoas · ${rateLabel(space)}` : "Tarifa indisponível"}
            </Typography.Text>
          </Space>
        );
      },
    },
    { title: tClient("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    {
      title: "Período",
      key: "period",
      render: (_: unknown, booking) => (
        <Space direction="vertical" size={0}>
          <Typography.Text>{formatDateTime(booking.start_time)}</Typography.Text>
          <Typography.Text type="secondary">até {formatDateTime(booking.end_time)}</Typography.Text>
          <Typography.Text type="secondary">
            Duração: {durationLabel(bookingDurationHours(booking))}
          </Typography.Text>
        </Space>
      ),
    },
    {
      title: tClient("fieldEquipment"),
      key: "equipment",
      render: (_: unknown, booking) => (
        <Typography.Text>{equipmentSummary(booking, equipmentById)}</Typography.Text>
      ),
    },
    {
      title: tClient("columnPrice"),
      dataIndex: "quoted_price",
      key: "quoted_price",
      align: "right",
      render: (value: string | null) => (value ? formatCurrency(value) : "A confirmar"),
    },
    {
      title: tClient("columnUpdatedAt"),
      dataIndex: "updated_at",
      key: "updated_at",
      render: formatDateTime,
    },
  ];

  if (isLoading || spaces.isLoading || equipment.isLoading)
    return <Spin size="large" tip={tClient("pageLoading")} />;
  if (isError || spaces.isError || equipment.isError)
    return <Result status="error" title={tClient("clientLoadError")} />;

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
        expandable={{
          expandedRowRender: (booking) => {
            const space = spacesById.get(booking.space_id);
            const selectedEquipment = booking.equipment_ids
              .map((id) => equipmentById.get(id))
              .filter((item): item is Equipment => Boolean(item));
            const hours = bookingDurationHours(booking);
            const estimate = calculateRentalEstimate(
              space as IncubatorSpace | undefined,
              selectedEquipment,
              hours,
            );
            return (
              <Descriptions size="small" column={{ xs: 1, md: 2 }} bordered>
                <Descriptions.Item label={tClient("fieldRequesterName")}>
                  {booking.requester_name || "—"}
                </Descriptions.Item>
                <Descriptions.Item label={tClient("fieldRequesterEmail")}>
                  {booking.requester_email || "—"}
                </Descriptions.Item>
                <Descriptions.Item label={tClient("fieldRequesterPhone")}>
                  {booking.requester_phone || "—"}
                </Descriptions.Item>
                <Descriptions.Item label="Submetido em">
                  {formatDateTime(booking.created_at)}
                </Descriptions.Item>
                <Descriptions.Item label="Tarifa do espaço">
                  {space ? rateLabel(space) : "—"}
                </Descriptions.Item>
                <Descriptions.Item label="Estimativa">
                  {hours > 0
                    ? `${durationLabel(hours)} · espaço ${formatMoney(
                        estimate.spaceCost,
                      )} · equipamento ${formatMoney(estimate.equipmentCost)}`
                    : "—"}
                </Descriptions.Item>
                <Descriptions.Item label={tClient("fieldEquipment")} span={2}>
                  {selectedEquipment.length ? (
                    <Space direction="vertical" size={0}>
                      {selectedEquipment.map((item) => (
                        <Typography.Text key={item.id}>
                          {item.name} · {rateLabel(item)}
                        </Typography.Text>
                      ))}
                    </Space>
                  ) : (
                    "Sem equipamento"
                  )}
                </Descriptions.Item>
                <Descriptions.Item label={tClient("fieldNotes")} span={2}>
                  {booking.notes || "—"}
                </Descriptions.Item>
              </Descriptions>
            );
          },
        }}
      />
    </Card>
  );
}
