"use client";

import { Card, Col, Result, Row, Spin, Table } from "antd";
import type { ColumnsType } from "antd/es/table";

import { statusTag } from "@/components/operations/format";
import { useEquipment, useEquipmentTypes } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Equipment, EquipmentType } from "@/lib/api/inventory";

export default function InventoryPage() {
  const equipment = useEquipment();
  const types = useEquipmentTypes();

  const equipmentColumns: ColumnsType<Equipment> = [
    { title: tStaff("columnName"), dataIndex: "name", key: "name" },
    { title: tStaff("columnType"), dataIndex: "equipment_type", key: "equipment_type" },
    {
      title: tStaff("columnSerial"),
      dataIndex: "serial_number",
      key: "serial_number",
      render: (v: string) => v || "—",
    },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
  ];
  const typeColumns: ColumnsType<EquipmentType> = [
    { title: tStaff("columnName"), dataIndex: "name", key: "name" },
    {
      title: tStaff("columnStatus"),
      dataIndex: "is_active",
      key: "is_active",
      render: (v: boolean) => statusTag(v ? "Active" : "Inactive"),
    },
  ];

  if (equipment.isLoading || types.isLoading)
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  if (equipment.isError || types.isError)
    return <Result status="error" title={tStaff("loadError")} />;

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} lg={16}>
        <Card title={tStaff("navInventory")}>
          <Table<Equipment>
            rowKey="id"
            columns={equipmentColumns}
            dataSource={equipment.data ?? []}
            locale={{ emptyText: tStaff("emptyData") }}
          />
        </Card>
      </Col>
      <Col xs={24} lg={8}>
        <Card title={tStaff("inventoryTypesTitle")}>
          <Table<EquipmentType>
            rowKey="id"
            columns={typeColumns}
            dataSource={types.data ?? []}
            locale={{ emptyText: tStaff("emptyData") }}
            pagination={false}
            size="small"
          />
        </Card>
      </Col>
    </Row>
  );
}
