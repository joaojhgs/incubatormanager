"use client";

import {
  Alert,
  Button,
  Card,
  Descriptions,
  InputNumber,
  Popconfirm,
  Result,
  Select,
  Space,
  Spin,
  Table,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useEffect, useMemo, useState } from "react";

import { formatDateTime, statusTag } from "@/components/operations/format";
import {
  useBookingActions,
  useBookingCalendar,
  useBookings,
  useCompanies,
  useEquipment,
  useSpaces,
} from "@/lib/hooks";
import type { Booking, BookingCalendarEvent } from "@/lib/api/bookings";
import { tStaff } from "@/lib/i18n/staffNav";
import { calculateRentalEstimate, formatMoney, rateLabel } from "@/lib/pricing";

function byId<T extends { id: string; name?: string }>(items: T[] | undefined) {
  return new Map((items ?? []).map((item) => [item.id, item.name ?? item.id]));
}

export default function BookingsPage() {
  const { data, isLoading, isError } = useBookings();
  const calendar = useBookingCalendar();
  const spaces = useSpaces();
  const equipment = useEquipment();
  const companies = useCompanies({ page_size: 100, is_active: true });
  const actions = useBookingActions();
  const [quotedPriceByBooking, setQuotedPriceByBooking] = useState<Record<string, number | null>>(
    {},
  );
  const [selectedEquipmentByBooking, setSelectedEquipmentByBooking] = useState<
    Record<string, string[]>
  >({});
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [highlightBookingId, setHighlightBookingId] = useState<string | undefined>();

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const status = params.get("status") ?? undefined;
    const booking = params.get("booking") ?? undefined;
    if (status) setStatusFilter(status);
    if (booking) setHighlightBookingId(booking);
  }, []);

  useEffect(() => {
    if (!highlightBookingId || isLoading) return;
    window.setTimeout(() => {
      document
        .querySelector(`[data-row-key="${CSS.escape(highlightBookingId)}"]`)
        ?.scrollIntoView({ behavior: "smooth", block: "center" });
    }, 100);
  }, [highlightBookingId, isLoading]);

  const spaceNames = useMemo(() => byId(spaces.data), [spaces.data]);
  const companyNames = useMemo(
    () => new Map((companies.data?.results ?? []).map((company) => [company.id, company.name])),
    [companies.data],
  );
  const equipmentOptions = useMemo(
    () =>
      (equipment.data ?? []).map((item) => ({
        label: `${item.name}${item.serial_number ? ` · ${item.serial_number}` : ""}`,
        value: item.id,
        disabled: item.status !== "Available" && item.status !== "In use",
      })),
    [equipment.data],
  );

  const calculateBookingEstimate = (row: Booking, equipmentIds: string[]) => {
    const start = new Date(row.start_time).getTime();
    const end = new Date(row.end_time).getTime();
    const durationHours =
      Number.isFinite(start) && Number.isFinite(end) && end > start
        ? Math.round(((end - start) / 3_600_000) * 100) / 100
        : 0;
    const space = (spaces.data ?? []).find((item) => item.id === row.space_id);
    const selectedItems = (equipment.data ?? []).filter((item) => equipmentIds.includes(item.id));
    return { durationHours, ...calculateRentalEstimate(space, selectedItems, durationHours) };
  };

  const columns: ColumnsType<Booking> = [
    {
      title: tStaff("columnSpace"),
      dataIndex: "space_id",
      key: "space_id",
      ellipsis: true,
      render: (spaceId: string, row) => (
        <Space direction="vertical" size={0}>
          <Typography.Text strong>{spaceNames.get(spaceId) ?? spaceId}</Typography.Text>
          <Typography.Text type="secondary">
            {row.company_id
              ? (companyNames.get(row.company_id) ?? row.company_id)
              : tStaff("bookingCompanyMissing")}
          </Typography.Text>
        </Space>
      ),
    },
    {
      title: tStaff("bookingRequester"),
      key: "requester",
      ellipsis: true,
      render: (_: unknown, row) => (
        <Space direction="vertical" size={0}>
          <Typography.Text>{row.requester_name || "—"}</Typography.Text>
          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
            {row.requester_email || row.requester_phone || "Sem contacto"}
          </Typography.Text>
        </Space>
      ),
    },
    {
      title: tStaff("columnStatus"),
      dataIndex: "status",
      key: "status",
      width: 120,
      render: statusTag,
    },
    {
      title: "Período",
      key: "period",
      width: 210,
      render: (_: unknown, row) => (
        <Space direction="vertical" size={0}>
          <Typography.Text>{formatDateTime(row.start_time)}</Typography.Text>
          <Typography.Text type="secondary">até {formatDateTime(row.end_time)}</Typography.Text>
        </Space>
      ),
    },
    {
      title: tStaff("columnPrice"),
      key: "quotedPricePicker",
      width: 150,
      render: (_: unknown, row) => (
        <InputNumber
          min={0}
          precision={2}
          size="small"
          addonBefore="€"
          placeholder={tStaff("bookingQuotedPricePlaceholder")}
          value={
            quotedPriceByBooking[row.id] ?? (row.quoted_price ? Number(row.quoted_price) : null)
          }
          disabled={row.status !== "Pending" || actions.approve.isPending}
          onChange={(value) =>
            setQuotedPriceByBooking((current) => ({ ...current, [row.id]: value }))
          }
          style={{ width: 132 }}
        />
      ),
    },
    {
      title: tStaff("bookingActions"),
      key: "actions",
      width: 250,
      render: (_: unknown, row) => (
        <Space size={4} wrap>
          <Popconfirm
            title={row.company_id ? "Aprovar reserva?" : "Reserva sem empresa associada"}
            okText="Aprovar"
            cancelText="Cancelar"
            disabled={!row.company_id}
            onConfirm={() =>
              actions.approve.mutate({
                id: row.id,
                payload: {
                  company_id: row.company_id ?? undefined,
                  quoted_price: quotedPriceByBooking[row.id] ?? row.quoted_price ?? undefined,
                  equipment_ids: selectedEquipmentByBooking[row.id] ?? row.equipment_ids,
                },
              })
            }
          >
            <Button
              size="small"
              type="primary"
              disabled={row.status !== "Pending" || !row.company_id}
              loading={actions.approve.isPending}
            >
              {tStaff("bookingApprove")}
            </Button>
          </Popconfirm>
          <Popconfirm
            title="Rejeitar reserva?"
            okText="Rejeitar"
            cancelText="Cancelar"
            onConfirm={() => actions.reject.mutate(row.id)}
          >
            <Button
              size="small"
              disabled={row.status !== "Pending"}
              loading={actions.reject.isPending}
            >
              {tStaff("bookingReject")}
            </Button>
          </Popconfirm>
          <Popconfirm
            title="Cancelar reserva?"
            okText="Cancelar reserva"
            cancelText="Voltar"
            onConfirm={() => actions.cancel.mutate(row.id)}
          >
            <Button
              size="small"
              danger
              disabled={!["Pending", "Approved"].includes(row.status)}
              loading={actions.cancel.isPending}
            >
              {tStaff("bookingCancel")}
            </Button>
          </Popconfirm>
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

  if (
    isLoading ||
    calendar.isLoading ||
    spaces.isLoading ||
    equipment.isLoading ||
    companies.isLoading
  ) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (isError || calendar.isError || spaces.isError || equipment.isError || companies.isError) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  const pendingCount = data?.filter((booking) => booking.status === "Pending").length ?? 0;
  const approvedCount = data?.filter((booking) => booking.status === "Approved").length ?? 0;
  const bookingsData = (data ?? []).filter(
    (booking) => !statusFilter || booking.status.toLowerCase() === statusFilter.toLowerCase(),
  );
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
      <Card title="Filtros">
        <Select
          allowClear
          placeholder="Filtrar por estado"
          value={statusFilter}
          onChange={setStatusFilter}
          options={["Pending", "Approved", "Rejected", "Cancelled", "Completed"].map((status) => ({
            label: status,
            value: status,
          }))}
          style={{ width: 240 }}
        />
      </Card>
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
          dataSource={bookingsData}
          locale={{ emptyText: tStaff("emptyData") }}
          tableLayout="fixed"
          rowClassName={(row) => (row.id === highlightBookingId ? "booking-row-highlight" : "")}
          expandable={{
            defaultExpandedRowKeys: highlightBookingId ? [highlightBookingId] : undefined,
            expandedRowRender: (row) => {
              const currentEquipmentIds = selectedEquipmentByBooking[row.id] ?? row.equipment_ids;
              const estimate = calculateBookingEstimate(row, currentEquipmentIds);
              return (
                <Descriptions size="small" column={{ xs: 1, md: 2 }} bordered>
                  <Descriptions.Item label={tStaff("bookingRequester")}>
                    <Space direction="vertical" size={0}>
                      <Typography.Text>
                        {row.requester_name || "Nome não informado"}
                      </Typography.Text>
                      <Typography.Text type="secondary">
                        {row.requester_email || "Email não informado"}
                      </Typography.Text>
                      <Typography.Text type="secondary">
                        {row.requester_phone || "Telefone não informado"}
                      </Typography.Text>
                    </Space>
                  </Descriptions.Item>
                  <Descriptions.Item label={tStaff("columnCompany")}>
                    {row.company_id
                      ? (companyNames.get(row.company_id) ?? row.company_id)
                      : tStaff("bookingCompanyMissing")}
                  </Descriptions.Item>
                  <Descriptions.Item label={tStaff("bookingEquipmentSelected")} span={2}>
                    <Select
                      mode="multiple"
                      allowClear
                      size="small"
                      maxTagCount="responsive"
                      placeholder={tStaff("bookingEquipmentPlaceholder")}
                      value={currentEquipmentIds}
                      options={equipmentOptions}
                      disabled={row.status !== "Pending" || actions.approve.isPending}
                      onChange={(equipmentIds) =>
                        setSelectedEquipmentByBooking((current) => ({
                          ...current,
                          [row.id]: equipmentIds,
                        }))
                      }
                      style={{ width: "100%" }}
                    />
                  </Descriptions.Item>
                  <Descriptions.Item label="Estimativa" span={2}>
                    <Space direction="vertical" size={0}>
                      <Typography.Text>
                        {estimate.durationHours}h · espaço {formatMoney(estimate.spaceCost)} ·
                        equipamento {formatMoney(estimate.equipmentCost)}
                      </Typography.Text>
                      <Typography.Text type="secondary">
                        Total estimado {formatMoney(estimate.total)}; valor aprovado{" "}
                        {formatMoney(quotedPriceByBooking[row.id] ?? row.quoted_price)}.
                      </Typography.Text>
                    </Space>
                  </Descriptions.Item>
                  <Descriptions.Item label="Tarifa do espaço">
                    {rateLabel((spaces.data ?? []).find((space) => space.id === row.space_id))}
                  </Descriptions.Item>
                  <Descriptions.Item label={tStaff("bookingNotes")}>
                    {row.notes || "—"}
                  </Descriptions.Item>
                </Descriptions>
              );
            },
          }}
        />
      </Card>
    </Space>
  );
}
