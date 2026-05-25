"use client";

import { useMemo } from "react";
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
import {
  useEquipment,
  useEquipmentAssignments,
  useEquipmentTypes,
  useSpaceBookingRecords,
  useSpaces,
} from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Equipment, EquipmentAssignment, EquipmentType } from "@/lib/api/inventory";

type SpaceInventoryRow = {
  spaceId: string;
  spaceName: string;
  spaceStatus: string;
  activeBookingCount: number;
  nextBookingAt: string | null;
  assignedEquipment: string[];
};

function isActiveBookingStatus(status: string): boolean {
  return !["cancelled", "canceled", "completed", "rejected"].includes(status.toLowerCase());
}

export default function InventoryPage() {
  const equipment = useEquipment();
  const types = useEquipmentTypes();
  const spaces = useSpaces();
  const spaceBookings = useSpaceBookingRecords();
  const assignments = useEquipmentAssignments();

  const equipmentData = useMemo(() => equipment.data ?? [], [equipment.data]);
  const spacesData = useMemo(() => spaces.data ?? [], [spaces.data]);
  const bookingRecords = useMemo(() => spaceBookings.data ?? [], [spaceBookings.data]);
  const assignmentData = useMemo(() => assignments.data ?? [], [assignments.data]);

  const spaceNames = useMemo(
    () => new Map(spacesData.map((space) => [space.id, space.name])),
    [spacesData],
  );

  const equipmentNames = useMemo(
    () => new Map(equipmentData.map((item) => [item.id, item.name])),
    [equipmentData],
  );
  const equipmentTypeNames = useMemo(
    () => new Map((types.data ?? []).map((type) => [type.id, type.name])),
    [types.data],
  );

  const spaceInventoryRows = useMemo<SpaceInventoryRow[]>(() => {
    return spacesData.map((space) => {
      const assignedEquipment = equipmentData
        .filter((item) => item.assigned_space_id === space.id)
        .map((item) => item.name);
      const activeRecords = bookingRecords
        .filter((record) => record.space_id === space.id && isActiveBookingStatus(record.status))
        .sort(
          (a, b) => new Date(a.start_time ?? 0).getTime() - new Date(b.start_time ?? 0).getTime(),
        );
      return {
        spaceId: space.id,
        spaceName: space.name,
        spaceStatus: space.status,
        activeBookingCount: activeRecords.length,
        nextBookingAt: activeRecords[0]?.start_time ?? null,
        assignedEquipment,
      };
    });
  }, [bookingRecords, equipmentData, spacesData]);

  const recentAssignments = useMemo(
    () => [...assignmentData].sort((a, b) => Date.parse(b.updated_at) - Date.parse(a.updated_at)),
    [assignmentData],
  );

  const equipmentColumns: ColumnsType<Equipment> = [
    { title: tStaff("columnName"), dataIndex: "name", key: "name" },
    {
      title: tStaff("columnType"),
      dataIndex: "equipment_type",
      key: "equipment_type",
      render: (value: string) => equipmentTypeNames.get(value) ?? value,
    },
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
      render: (value: string | null) => (value ? (spaceNames.get(value) ?? value) : "—"),
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
  const spaceInventoryColumns: ColumnsType<SpaceInventoryRow> = [
    { title: tStaff("columnSpace"), dataIndex: "spaceName", key: "spaceName" },
    {
      title: tStaff("columnStatus"),
      dataIndex: "spaceStatus",
      key: "spaceStatus",
      render: statusTag,
    },
    {
      title: tStaff("inventoryActiveBookings"),
      dataIndex: "activeBookingCount",
      key: "activeBookingCount",
      align: "right",
    },
    {
      title: tStaff("inventoryNextBooking"),
      dataIndex: "nextBookingAt",
      key: "nextBookingAt",
      render: formatDateTime,
    },
    {
      title: tStaff("inventoryAssignedEquipment"),
      dataIndex: "assignedEquipment",
      key: "assignedEquipment",
      render: (value: string[]) => (value.length > 0 ? value.join(", ") : "—"),
    },
  ];
  const assignmentColumns: ColumnsType<EquipmentAssignment> = [
    {
      title: tStaff("columnName"),
      dataIndex: "equipment_name",
      key: "equipment_name",
      render: (value: string, row) =>
        value || equipmentNames.get(row.equipment_id) || row.equipment_id,
    },
    {
      title: tStaff("columnSpace"),
      dataIndex: "assigned_space_id",
      key: "assigned_space_id",
      render: (value: string | null) => (value ? (spaceNames.get(value) ?? value) : "—"),
    },
    {
      title: tStaff("columnStatus"),
      dataIndex: "status",
      key: "status",
      render: statusTag,
    },
    {
      title: tStaff("inventoryBookingReference"),
      dataIndex: "booking_id",
      key: "booking_id",
      render: (value: string) => <Typography.Text code>{value}</Typography.Text>,
    },
    {
      title: tStaff("columnUpdatedAt"),
      dataIndex: "updated_at",
      key: "updated_at",
      render: formatDateTime,
    },
  ];

  if (
    equipment.isLoading ||
    types.isLoading ||
    spaces.isLoading ||
    spaceBookings.isLoading ||
    assignments.isLoading
  ) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (
    equipment.isError ||
    types.isError ||
    spaces.isError ||
    spaceBookings.isError ||
    assignments.isError
  ) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

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

      <Card title={tStaff("inventorySpaceBookingTitle")}>
        <Table<SpaceInventoryRow>
          rowKey="spaceId"
          columns={spaceInventoryColumns}
          dataSource={spaceInventoryRows}
          locale={{ emptyText: tStaff("emptyData") }}
          pagination={false}
          scroll={{ x: 900 }}
        />
      </Card>

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
                            ? `${tStaff("inventoryAssignedToSpace")} ${
                                spaceNames.get(row.assigned_space_id) ?? row.assigned_space_id
                              }`
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

      <Card title={tStaff("inventoryRecentAssignmentsTitle")}>
        <Table<EquipmentAssignment>
          rowKey="id"
          columns={assignmentColumns}
          dataSource={recentAssignments}
          locale={{ emptyText: tStaff("emptyData") }}
          pagination={{ pageSize: 6, hideOnSinglePage: true }}
          scroll={{ x: 1000 }}
          size="small"
        />
      </Card>
    </Space>
  );
}
