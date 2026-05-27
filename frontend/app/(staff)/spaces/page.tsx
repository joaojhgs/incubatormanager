"use client";

import {
  Alert,
  Button,
  Card,
  Col,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Progress,
  Result,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Switch,
  Table,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import { useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { formatDateTime, statusTag } from "@/components/operations/format";
import { rateLabel } from "@/lib/pricing";
import {
  useCompanies,
  useSpaceActions,
  useSpaceBookingRecords,
  useSpaceOccupancy,
  useSpaces,
  useSpaceTypes,
} from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type {
  Space as IncubatorSpace,
  SpaceBookingRecord,
  SpaceOccupancy,
  SpaceType,
} from "@/lib/api/spaces";

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
  const { isAuthenticated, isReady } = useAuth();
  const canFetch = isReady && isAuthenticated;
  const queryControls = useMemo(
    () => ({
      enabled: canFetch,
      retry: false,
      refetchOnMount: false,
      refetchOnReconnect: false,
      staleTime: 5 * 60_000,
    }),
    [canFetch],
  );
  const companyParams = useMemo(() => ({ page_size: 200, is_active: true }), []);

  const spaces = useSpaces(queryControls);
  const spaceTypes = useSpaceTypes(queryControls);
  const actions = useSpaceActions();
  const occupancy = useSpaceOccupancy(queryControls);
  const bookingRecords = useSpaceBookingRecords(queryControls);
  const companies = useCompanies(companyParams, queryControls);
  const [spaceForm] = Form.useForm();
  const [typeForm] = Form.useForm();
  const [editingSpace, setEditingSpace] = useState<IncubatorSpace | null>(null);
  const [spaceModalOpen, setSpaceModalOpen] = useState(false);
  const [typeModalOpen, setTypeModalOpen] = useState(false);

  const spacesData = useMemo(() => spaces.data ?? [], [spaces.data]);
  const occupancyData = useMemo(() => occupancy.data ?? [], [occupancy.data]);
  const recordsData = useMemo(() => bookingRecords.data ?? [], [bookingRecords.data]);
  const companyNames = useMemo(
    () => new Map((companies.data?.results ?? []).map((company) => [company.id, company.name])),
    [companies.data?.results],
  );
  const spaceTypeNames = useMemo(
    () => new Map((spaceTypes.data ?? []).map((type) => [type.id, type.name])),
    [spaceTypes.data],
  );

  const openSpaceModal = (space?: IncubatorSpace) => {
    setEditingSpace(space ?? null);
    if (space) {
      spaceForm.setFieldsValue(space);
    } else {
      spaceForm.resetFields();
      spaceForm.setFieldsValue({
        status: "Available",
        capacity: 1,
        rental_cost_unit: "hour",
        is_active: true,
      });
    }
    setSpaceModalOpen(true);
  };

  const closeSpaceModal = () => {
    setSpaceModalOpen(false);
    setEditingSpace(null);
    spaceForm.resetFields();
  };

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
    { title: tStaff("columnName"), dataIndex: "name", key: "name", width: 180 },
    {
      title: tStaff("columnType"),
      dataIndex: "space_type",
      key: "space_type",
      width: 170,
      render: (value: string | null) => (value ? (spaceTypeNames.get(value) ?? value) : "—"),
    },
    { title: tStaff("columnCapacity"), dataIndex: "capacity", key: "capacity", width: 110 },
    {
      title: "Tarifa",
      key: "rental_cost",
      width: 140,
      render: (_: unknown, row) => rateLabel(row),
    },
    {
      title: tStaff("columnStatus"),
      dataIndex: "status",
      key: "status",
      width: 150,
      render: statusTag,
    },
    {
      title: tStaff("spacesActiveBookings"),
      dataIndex: "activeBookingCount",
      key: "activeBookingCount",
      align: "right",
      width: 150,
    },
    {
      title: tStaff("spacesNextBooking"),
      dataIndex: "nextBookingAt",
      key: "nextBookingAt",
      width: 190,
      render: formatDateTime,
    },
    {
      title: tStaff("columnCompany"),
      dataIndex: "company_id",
      key: "company_id",
      width: 220,
      ellipsis: true,
      render: (v: string | null) => (v ? (companyNames.get(v) ?? v) : "—"),
    },
    {
      title: tStaff("columnActions"),
      key: "actions",
      width: 180,
      render: (_: unknown, row) => (
        <Space>
          <Button size="small" onClick={() => openSpaceModal(row)}>
            Editar
          </Button>
          <Popconfirm
            title={row.is_active ? "Bloquear espaço?" : "Ativar espaço?"}
            okText={row.is_active ? "Bloquear" : "Ativar"}
            cancelText="Cancelar"
            onConfirm={() =>
              actions.update.mutate({
                id: row.id,
                payload: {
                  is_active: !row.is_active,
                  status: row.is_active ? "Blocked" : "Available",
                },
              })
            }
          >
            <Button size="small">{row.is_active ? "Bloquear" : "Ativar"}</Button>
          </Popconfirm>
        </Space>
      ),
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

  const typeColumns: ColumnsType<SpaceType> = [
    { title: tStaff("columnName"), dataIndex: "name", key: "name" },
    {
      title: tStaff("columnStatus"),
      dataIndex: "is_active",
      key: "is_active",
      render: (value: boolean) => statusTag(value ? "Active" : "Inactive"),
    },
  ];

  if (
    !isReady ||
    spaces.isLoading ||
    spaceTypes.isLoading ||
    occupancy.isLoading ||
    bookingRecords.isLoading ||
    companies.isLoading
  ) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (!isAuthenticated) {
    return <Result status="403" title="Sessão expirada" subTitle="Inicie sessão novamente." />;
  }

  if (
    spaces.isError ||
    spaceTypes.isError ||
    occupancy.isError ||
    bookingRecords.isError ||
    companies.isError
  ) {
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
        <Col span={24}>
          <Card
            title={tStaff("navSpaces")}
            extra={
              <Space>
                <Button onClick={() => setTypeModalOpen(true)}>Novo tipo</Button>
                <Button type="primary" onClick={() => openSpaceModal()}>
                  Novo espaço
                </Button>
              </Space>
            }
          >
            <Table<SpaceOverviewRow>
              rowKey="id"
              columns={spaceColumns}
              dataSource={spaceRows}
              locale={{ emptyText: tStaff("emptyData") }}
              pagination={false}
              scroll={{ x: 1340 }}
              size="middle"
            />
          </Card>
        </Col>
        <Col xs={24} lg={14}>
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
        <Col xs={24} lg={10}>
          <Card title="Tipos de espaço">
            <Table<SpaceType>
              rowKey="id"
              columns={typeColumns}
              dataSource={spaceTypes.data ?? []}
              locale={{ emptyText: tStaff("emptyData") }}
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
      <Modal
        title={editingSpace ? "Editar espaço" : "Novo espaço"}
        open={spaceModalOpen}
        onCancel={closeSpaceModal}
        onOk={() => spaceForm.submit()}
        confirmLoading={actions.create.isPending || actions.update.isPending}
        destroyOnClose
      >
        <Form
          form={spaceForm}
          layout="vertical"
          onFinish={(values) => {
            const payload = {
              ...values,
              company_id: values.company_id || null,
              space_type: values.space_type || null,
              rental_cost: values.rental_cost ?? null,
              rental_cost_unit: values.rental_cost_unit || "hour",
            };
            if (editingSpace) {
              actions.update.mutate(
                { id: editingSpace.id, payload },
                { onSuccess: closeSpaceModal },
              );
            } else {
              actions.create.mutate(payload, { onSuccess: closeSpaceModal });
            }
          }}
        >
          <Form.Item name="name" label={tStaff("columnName")} rules={[{ required: true }]}>
            <Input />
          </Form.Item>
          <Form.Item name="space_type" label={tStaff("columnType")}>
            <Select
              allowClear
              options={(spaceTypes.data ?? []).map((type) => ({
                label: type.name,
                value: type.id,
              }))}
            />
          </Form.Item>
          <Form.Item name="capacity" label={tStaff("columnCapacity")} rules={[{ required: true }]}>
            <InputNumber min={1} precision={0} style={{ width: "100%" }} />
          </Form.Item>
          <Space.Compact style={{ width: "100%" }}>
            <Form.Item name="rental_cost" label="Valor de reserva" style={{ width: "65%" }}>
              <InputNumber min={0} precision={2} addonBefore="€" style={{ width: "100%" }} />
            </Form.Item>
            <Form.Item name="rental_cost_unit" label="Unidade" style={{ width: "35%" }}>
              <Select
                options={[
                  { label: "Por hora", value: "hour" },
                  { label: "Por dia", value: "day" },
                  { label: "Por reserva", value: "fixed" },
                ]}
              />
            </Form.Item>
          </Space.Compact>
          <Form.Item name="status" label={tStaff("columnStatus")} rules={[{ required: true }]}>
            <Select
              options={["Available", "Reserved", "Occupied", "Maintenance", "Blocked"].map(
                (value) => ({
                  label: value,
                  value,
                }),
              )}
            />
          </Form.Item>
          <Form.Item name="company_id" label={tStaff("columnCompany")}>
            <Select
              allowClear
              showSearch
              optionFilterProp="label"
              options={(companies.data?.results ?? []).map((company) => ({
                label: company.name,
                value: company.id,
              }))}
            />
          </Form.Item>
          <Form.Item name="is_active" label="Ativo" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
      <Modal
        title="Novo tipo de espaço"
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
    </Space>
  );
}
