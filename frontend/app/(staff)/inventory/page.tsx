"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Modal,
  Result,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Switch,
  Table,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";

import { formatCurrency, formatDateTime, statusTag } from "@/components/operations/format";
import {
  useEquipment,
  useEquipmentActions,
  useEquipmentAssignments,
  useEquipmentTypes,
  useCompanies,
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
  const actions = useEquipmentActions();
  const types = useEquipmentTypes();
  const spaces = useSpaces();
  const companies = useCompanies({ page_size: 200, is_active: true });
  const spaceBookings = useSpaceBookingRecords();
  const assignments = useEquipmentAssignments();
  const [equipmentForm] = Form.useForm();
  const [typeForm] = Form.useForm();
  const [assignForm] = Form.useForm();
  const [releaseForm] = Form.useForm<{ booking_id: string }>();
  const assignmentsRef = useRef<HTMLDivElement | null>(null);
  const [editingEquipment, setEditingEquipment] = useState<Equipment | null>(null);
  const [equipmentModalOpen, setEquipmentModalOpen] = useState(false);
  const [typeModalOpen, setTypeModalOpen] = useState(false);
  const [assigningEquipment, setAssigningEquipment] = useState<Equipment | null>(null);
  const [releasingEquipment, setReleasingEquipment] = useState<Equipment | null>(null);

  useEffect(() => {
    if (new URLSearchParams(window.location.search).get("focus") === "assignments") {
      assignmentsRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, []);

  const openEquipmentModal = (item?: Equipment) => {
    setEditingEquipment(item ?? null);
    if (item) {
      equipmentForm.setFieldsValue(item);
    } else {
      equipmentForm.resetFields();
      equipmentForm.setFieldsValue({ status: "Available", is_active: true });
    }
    setEquipmentModalOpen(true);
  };

  const closeEquipmentModal = () => {
    setEquipmentModalOpen(false);
    setEditingEquipment(null);
    equipmentForm.resetFields();
  };

  const equipmentData = useMemo(() => equipment.data ?? [], [equipment.data]);
  const spacesData = useMemo(() => spaces.data ?? [], [spaces.data]);
  const bookingRecords = useMemo(() => spaceBookings.data ?? [], [spaceBookings.data]);
  const assignmentData = useMemo(() => assignments.data ?? [], [assignments.data]);
  const companiesData = useMemo(() => companies.data?.results ?? [], [companies.data?.results]);

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
  const companyNames = useMemo(
    () => new Map(companiesData.map((company) => [company.id, company.name])),
    [companiesData],
  );
  const companyOptions = useMemo(
    () => companiesData.map((company) => ({ label: company.name, value: company.id })),
    [companiesData],
  );
  const bookingOptions = useMemo(
    () =>
      bookingRecords
        .filter((record) => isActiveBookingStatus(record.status))
        .map((record) => ({
          label: [
            spaceNames.get(record.space_id) ?? record.space_id,
            record.start_time ? formatDateTime(record.start_time) : null,
            record.company_id ? (companyNames.get(record.company_id) ?? record.company_id) : null,
          ]
            .filter(Boolean)
            .join(" · "),
          value: record.id,
        })),
    [bookingRecords, companyNames, spaceNames],
  );
  const releaseBookingOptions = useMemo(
    () =>
      assignmentData
        .filter(
          (assignment) =>
            assignment.equipment_id === releasingEquipment?.id &&
            isActiveBookingStatus(assignment.status),
        )
        .map((assignment) => ({
          label: [
            assignment.equipment_name || equipmentNames.get(assignment.equipment_id),
            spaceNames.get(assignment.assigned_space_id ?? ""),
            companyNames.get(assignment.company_id) ?? assignment.company_id,
            assignment.booking_id,
          ]
            .filter(Boolean)
            .join(" · "),
          value: assignment.booking_id,
        })),
    [assignmentData, companyNames, equipmentNames, releasingEquipment?.id, spaceNames],
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
    {
      title: tStaff("columnActions"),
      key: "actions",
      width: 240,
      render: (_: unknown, row) => (
        <Space>
          <Button size="small" onClick={() => openEquipmentModal(row)}>
            Editar
          </Button>
          <Button
            size="small"
            onClick={() => {
              setAssigningEquipment(row);
              assignForm.resetFields();
            }}
          >
            Atribuir
          </Button>
          <Button
            size="small"
            disabled={assignmentData.every((assignment) => assignment.equipment_id !== row.id)}
            onClick={() => {
              setReleasingEquipment(row);
              releaseForm.resetFields();
            }}
          >
            Libertar
          </Button>
        </Space>
      ),
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
    {
      title: tStaff("columnActions"),
      key: "actions",
      render: (_: unknown, row) => (
        <Button
          size="small"
          onClick={() =>
            actions.updateType.mutate({ id: row.id, payload: { is_active: !row.is_active } })
          }
        >
          {row.is_active ? "Desativar" : "Ativar"}
        </Button>
      ),
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
    companies.isLoading ||
    spaces.isLoading ||
    spaceBookings.isLoading ||
    assignments.isLoading
  ) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (
    equipment.isError ||
    types.isError ||
    companies.isError ||
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
          <Card
            title={tStaff("navInventory")}
            extra={
              <Button type="primary" onClick={() => openEquipmentModal()}>
                Novo equipamento
              </Button>
            }
          >
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
          <Card
            title={tStaff("inventoryTypesTitle")}
            extra={<Button onClick={() => setTypeModalOpen(true)}>Novo tipo</Button>}
          >
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

      <div ref={assignmentsRef}>
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
      </div>
      <Modal
        title={editingEquipment ? "Editar equipamento" : "Novo equipamento"}
        open={equipmentModalOpen}
        onCancel={closeEquipmentModal}
        onOk={() => equipmentForm.submit()}
        confirmLoading={actions.create.isPending || actions.update.isPending}
        destroyOnClose
      >
        <Form
          form={equipmentForm}
          layout="vertical"
          onFinish={(values) => {
            const payload = {
              ...values,
              assigned_space_id: values.assigned_space_id || null,
              rental_cost: values.rental_cost || null,
            };
            if (editingEquipment) {
              actions.update.mutate(
                { id: editingEquipment.id, payload },
                { onSuccess: closeEquipmentModal },
              );
            } else {
              actions.create.mutate(payload, { onSuccess: closeEquipmentModal });
            }
          }}
        >
          <Form.Item name="name" label={tStaff("columnName")} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item
            name="equipment_type"
            label={tStaff("columnType")}
            rules={[{ required: true }]}
          >
            <Select
              options={(types.data ?? []).map((type) => ({ label: type.name, value: type.id }))}
            />
          </Form.Item>
          <Form.Item name="serial_number" label={tStaff("columnSerial")}>
            <Input />
          </Form.Item>
          <Form.Item name="assigned_space_id" label={tStaff("inventoryAssignedSpace")}>
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              options={(spaces.data ?? []).map((space) => ({ label: space.name, value: space.id }))}
            />
          </Form.Item>
          <Form.Item name="rental_cost" label={tStaff("inventoryRentalCost")}>
            <InputNumber min={0} precision={2} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="status" label={tStaff("columnStatus")} rules={[{ required: true }]}>
            <Select
              options={["Available", "In use", "Maintenance"].map((value) => ({
                label: value,
                value,
              }))}
            />
          </Form.Item>
          <Form.Item name="notes" label={tStaff("bookingNotes")}>
            <Input.TextArea rows={3} />
          </Form.Item>
          <Form.Item name="is_active" label="Ativo" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="Novo tipo de equipamento"
        open={typeModalOpen}
        onCancel={() => setTypeModalOpen(false)}
        onOk={() => typeForm.submit()}
        confirmLoading={actions.createType.isPending}
        destroyOnClose
      >
        <Form
          form={typeForm}
          layout="vertical"
          onFinish={(values) =>
            actions.createType.mutate(values, {
              onSuccess: () => {
                setTypeModalOpen(false);
                typeForm.resetFields();
              },
            })
          }
        >
          <Form.Item name="name" label={tStaff("columnName")} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="is_active" label="Ativo" valuePropName="checked" initialValue>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="Atribuir equipamento"
        open={Boolean(assigningEquipment)}
        onCancel={() => setAssigningEquipment(null)}
        onOk={() => assignForm.submit()}
        confirmLoading={actions.assign.isPending}
        destroyOnClose
      >
        <Form
          form={assignForm}
          layout="vertical"
          onFinish={(values) => {
            if (!assigningEquipment) return;
            actions.assign.mutate(
              {
                id: assigningEquipment.id,
                payload: {
                  assigned_space_id: values.assigned_space_id,
                  booking_id: values.booking_id || undefined,
                  company_id: values.company_id || undefined,
                },
              },
              { onSuccess: () => setAssigningEquipment(null) },
            );
          }}
        >
          <Form.Item
            name="assigned_space_id"
            label={tStaff("columnSpace")}
            rules={[{ required: true }]}
          >
            <Select
              showSearch
              optionFilterProp="label"
              options={(spaces.data ?? []).map((space) => ({ label: space.name, value: space.id }))}
            />
          </Form.Item>
          <Form.Item name="booking_id" label={tStaff("inventoryBookingReference")}>
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              options={bookingOptions}
              placeholder="Selecionar reserva"
              onChange={(bookingId) => {
                const booking = bookingRecords.find((record) => record.id === bookingId);
                if (booking?.company_id) {
                  assignForm.setFieldValue("company_id", booking.company_id);
                }
              }}
            />
          </Form.Item>
          <Form.Item name="company_id" label={tStaff("columnCompany")}>
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              options={companyOptions}
              placeholder="Selecionar empresa"
            />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="Libertar equipamento"
        open={Boolean(releasingEquipment)}
        onCancel={() => setReleasingEquipment(null)}
        onOk={() => releaseForm.submit()}
        confirmLoading={actions.release.isPending}
        destroyOnClose
      >
        <Form
          form={releaseForm}
          layout="vertical"
          onFinish={(values) => {
            if (!releasingEquipment) return;
            actions.release.mutate(
              { id: releasingEquipment.id, payload: { booking_id: values.booking_id } },
              { onSuccess: () => setReleasingEquipment(null) },
            );
          }}
        >
          <Form.Item
            name="booking_id"
            label={tStaff("inventoryBookingReference")}
            rules={[{ required: true, message: "Selecione a reserva a libertar." }]}
          >
            <Select
              showSearch
              optionFilterProp="label"
              options={releaseBookingOptions}
              placeholder="Selecionar reserva atribuída"
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
