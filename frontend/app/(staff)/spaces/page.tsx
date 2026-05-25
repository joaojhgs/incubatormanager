"use client";

import { Card, Col, Result, Row, Spin, Table } from "antd";
import type { ColumnsType } from "antd/es/table";

import { statusTag } from "@/components/operations/format";
import { useSpaceOccupancy, useSpaces } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Space, SpaceOccupancy } from "@/lib/api/spaces";

export default function SpacesPage() {
  const spaces = useSpaces();
  const occupancy = useSpaceOccupancy();

  const spaceColumns: ColumnsType<Space> = [
    { title: tStaff("columnName"), dataIndex: "name", key: "name" },
    { title: tStaff("columnCapacity"), dataIndex: "capacity", key: "capacity", width: 120 },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    { title: tStaff("columnCompany"), dataIndex: "company_id", key: "company_id", render: (v: string | null) => v ?? "—" },
  ];
  const occupancyColumns: ColumnsType<SpaceOccupancy> = [
    { title: tStaff("columnSpace"), dataIndex: "space_name", key: "space_name" },
    { title: tStaff("columnOccupied"), key: "occupied", render: (_: unknown, row) => `${row.occupied}/${row.capacity} (${row.occupancy_percent}%)` },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
  ];

  if (spaces.isLoading || occupancy.isLoading) return <Spin size="large" tip={tStaff("pageLoading")} />;
  if (spaces.isError || occupancy.isError) return <Result status="error" title={tStaff("loadError")} />;

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={14}>
        <Card title={tStaff("navSpaces")}>
          <Table<Space> rowKey="id" columns={spaceColumns} dataSource={spaces.data ?? []} locale={{ emptyText: tStaff("emptyData") }} pagination={false} />
        </Card>
      </Col>
      <Col xs={24} lg={10}>
        <Card title={tStaff("spacesOccupancyTitle")}>
          <Table<SpaceOccupancy> rowKey="space_id" columns={occupancyColumns} dataSource={occupancy.data ?? []} locale={{ emptyText: tStaff("emptyData") }} pagination={false} size="small" />
        </Card>
      </Col>
    </Row>
  );
}
