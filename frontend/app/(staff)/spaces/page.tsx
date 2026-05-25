"use client";

import { Alert, Card, Col, Progress, Result, Row, Space, Spin, Statistic, Table } from "antd";
import type { ColumnsType } from "antd/es/table";
import { useMemo } from "react";

import { formatDateTime, statusTag } from "@/components/operations/format";
import { useCompanies, useSpaceBookingRecords, useSpaceOccupancy, useSpaces } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Space as IncubatorSpace, SpaceBookingRecord, SpaceOccupancy } from "@/lib/api/spaces";

type SpaceOverviewRow = IncubatorSpace & {
  activeBookingCount: number;
  nextBookingAt: string | null;
};

function isActiveBookingStatus(status: string): boolean {
  return !["cancelled", "canceled", "completed", "rejected"].includes(status.toLowerCase());
}

function getNextBooking(records: SpaceBookingRecord[]): string | null {
  return (
    records
      .filter((record) => record.start_time && isActiveBookingStatus(record.status))
      .sort((a, b) => Date.parse(a.start_time ?? "") - Date.parse(b.start_time ?? ""))[0]
      ?.start_time ?? null
  );
}

export default function SpacesPage() {
  const spaces = useSpaces();
  const occupancy = useSpaceOccupancy();
  const bookingRecords = useSpaceBookingRecords();
  const companies = useCompanies({ page_size: 200, is_active: true });

  const spacesData = useMemo(() => spaces.data ?? [], [spaces.data]);
  const occupancyData = useMemo(() => occupancy.data ?? [], [occupancy.data]);
  const recordsData = useMemo(() => bookingRecords.data ?? [], [bookingRecords.data]);
  const companyNames = useMemo(
    () => new Map((companies.data?.results ?? []).map((company) => [company.id, company.name])),
    [companies.data?.results],
  );

  const bookingsBySpace = useMemo(() => {
    return recordsData.reduce<Map<string, SpaceBookingRecord[]>>((bySpace, record) => {
      const records = bySpace.get(record.space_id) ?? [];
      records.push(record);
      bySpace.set(record.space_id, records);
      return bySpace;
    }, new Map());
  }, [recordsData]);

  const spaceRows = useMemo<SpaceOverviewRow[]>(
    () =>
      spacesData.map((space) => {
        const records = bookingsBySpace.get(space.id) ?? [];
        return {
          ...space,
          activeBookingCount: records.filter((record) => isActiveBookingStatus(record.status))
            .length,
          nextBookingAt: getNextBooking(records),
        };
      }),
    [bookingsBySpace, spacesData],
  );

  const totalCapacity = occupancyData.reduce((total, row) => total + row.capacity, 0);
  const occupiedCapacity = occupancyData.reduce((total, row) => total + row.occupied, 0);
  const occupancyPercent =
    totalCapacity > 0 ? Math.round((occupiedCapacity / totalCapacity) * 100) : 0;
  const availableSpaces = spacesData.filter((space) => space.status === "Available").length;
  const activeBookings = recordsData.filter((record) =>
    isActiveBookingStatus(record.status),
  ).length;

  const spaceColumns: ColumnsType<SpaceOverviewRow> = [
    { title: tStaff("columnName"), dataIndex: "name", key: "name" },
    {
      title: tStaff("columnType"),
      dataIndex: "space_type",
      key: "space_type",
      render: (value) => value ?? "—",
    },
    { title: tStaff("columnCapacity"), dataIndex: "capacity", key: "capacity", width: 120 },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    {
      title: tStaff("spacesActiveBookings"),
      dataIndex: "activeBookingCount",
      key: "activeBookingCount",
      align: "right",
    },
    {
      title: tStaff("spacesNextBooking"),
      dataIndex: "nextBookingAt",
      key: "nextBookingAt",
      render: formatDateTime,
    },
    {
      title: tStaff("columnCompany"),
      dataIndex: "company_id",
      key: "company_id",
      render: (v: string | null) => (v ? (companyNames.get(v) ?? v) : "—"),
    },
  ];
  const occupancyColumns: ColumnsType<SpaceOccupancy> = [
    { title: tStaff("columnSpace"), dataIndex: "space_name", key: "space_name" },
    {
      title: tStaff("columnOccupied"),
      key: "occupied",
      render: (_: unknown, row) => `${row.occupied}/${row.capacity} (${row.occupancy_percent}%)`,
    },
    {
      title: tStaff("spacesOccupancyProgress"),
      dataIndex: "occupancy_percent",
      key: "occupancy_percent",
      render: (value: string) => <Progress percent={Number(value)} size="small" />,
    },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
  ];

  if (spaces.isLoading || occupancy.isLoading || bookingRecords.isLoading || companies.isLoading) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (spaces.isError || occupancy.isError || bookingRecords.isError || companies.isError) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title={tStaff("spacesKpiTotal")} value={spacesData.length} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title={tStaff("spacesKpiAvailable")} value={availableSpaces} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title={tStaff("spacesKpiActiveBookings")} value={activeBookings} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title={tStaff("spacesKpiOccupancy")} value={occupancyPercent} suffix="%" />
            <Progress percent={occupancyPercent} size="small" />
          </Card>
        </Col>
      </Row>

      <Alert
        type="info"
        showIcon
        message={tStaff("spacesOverviewTitle")}
        description={tStaff("spacesOverviewDescription")}
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={15}>
          <Card title={tStaff("navSpaces")}>
            <Table<SpaceOverviewRow>
              rowKey="id"
              columns={spaceColumns}
              dataSource={spaceRows}
              locale={{ emptyText: tStaff("emptyData") }}
              pagination={false}
              scroll={{ x: 1000 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={9}>
          <Card title={tStaff("spacesOccupancyTitle")}>
            <Table<SpaceOccupancy>
              rowKey="space_id"
              columns={occupancyColumns}
              dataSource={occupancyData}
              locale={{ emptyText: tStaff("emptyData") }}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </Space>
  );
}
