"use client";

import {
  Alert,
  Card,
  Col,
  Descriptions,
  Result,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";

import { formatCurrency, formatDateTime, statusTag } from "@/components/operations/format";
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
      render: (value: string) => value || "—",
    },
    {
      title: tStaff("inventoryAssignedSpace"),
      dataIndex: "assigned_space_id",
      key: "assigned_space_id",
      render: (value: string | null) => value ?? "—",
    },
    {
      title: tStaff("inventoryRentalCost"),
      dataIndex: "rental_cost",
      key: "rental_cost",
      align: "right",
      render: formatCurrency,
    },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    {
      title: tStaff("columnUpdatedAt"),
      dataIndex: "updated_at",
      key: "updated_at",
      render: formatDateTime,
    },
  ];
  const typeColumns: ColumnsType<EquipmentType> = [
    { title: tStaff("columnName"), dataIndex: "name", key: "name" },
    {
      title: tStaff("columnStatus"),
      dataIndex: "is_active",
      key: "is_active",
      render: (value: boolean) => statusTag(value ? "Active" : "Inactive"),
    },
  ];

  if (equipment.isLoading || types.isLoading) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (equipment.isError || types.isError) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  const equipmentData = equipment.data ?? [];
  const availableCount = equipmentData.filter((item) => item.status === "Available").length;
  const assignedCount = equipmentData.filter((item) => item.status === "In use").length;
  const maintenanceCount = equipmentData.filter((item) => item.status === "Maintenance").length;

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title={tStaff("inventoryAvailableCount")} value={availableCount} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title={tStaff("inventoryAssignedCount")} value={assignedCount} />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title={tStaff("inventoryMaintenanceCount")} value={maintenanceCount} />
          </Card>
        </Col>
      </Row>

      <Alert
        type="info"
        showIcon
        message={tStaff("inventoryAssignmentHint")}
        description={tStaff("inventoryHistoryHint")}
      />

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title={tStaff("navInventory")}>
            <Table<Equipment>
              rowKey="id"
              columns={equipmentColumns}
              dataSource={equipmentData}
              locale={{ emptyText: tStaff("emptyData") }}
              scroll={{ x: 1000 }}
              expandable={{
                expandedRowRender: (row) => (
                  <Descriptions size="small" column={1} bordered>
                    <Descriptions.Item label={tStaff("inventoryAssignmentHistory")}>
                      <Space direction="vertical" size={0}>
                        <Typography.Text>
                          {row.assigned_space_id
                            ? `${tStaff("inventoryAssignedToSpace")} ${row.assigned_space_id}`
                            : tStaff("inventoryNoAssignment")}
                        </Typography.Text>
                        <Typography.Text type="secondary">
                          {tStaff("columnUpdatedAt")}: {formatDateTime(row.updated_at)}
                        </Typography.Text>
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label={tStaff("bookingNotes")}>
                      {row.notes || "—"}
                    </Descriptions.Item>
                  </Descriptions>
                ),
              }}
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
    </Space>
  );
}
