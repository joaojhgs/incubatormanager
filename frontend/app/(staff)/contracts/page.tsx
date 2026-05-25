"use client";

import { FileTextOutlined } from "@ant-design/icons";
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Descriptions,
  Form,
  Input,
  InputNumber,
  Modal,
  Popconfirm,
  Result,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import dayjs, { type Dayjs } from "dayjs";
import { useEffect, useMemo, useState } from "react";

import { DocumentManager } from "@/components/documents";
import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import type { Contract } from "@/lib/api/contracts";
import { useCompanies, useContractActions, useContracts, useSpaces } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";

type ContractFormValues = {
  company_id: string;
  space_id: string;
  area_sqm: number;
  rate_per_sqm: number;
  start_date: Dayjs;
  end_date: Dayjs;
  status?: string;
};

function normalize(value: string | null | undefined): string {
  return (value ?? "").toLocaleLowerCase("pt-PT");
}

function sumMonthlyFee(contracts: Contract[]): number {
  return contracts.reduce((total, contract) => total + Number(contract.monthly_fee ?? 0), 0);
}

export default function ContractsPage() {
  const { data, isLoading, isError } = useContracts();
  const companies = useCompanies({ page_size: 200, is_active: true });
  const spaces = useSpaces();
  const actions = useContractActions();
  const [form] = Form.useForm<ContractFormValues>();
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [search, setSearch] = useState("");
  const [editingContract, setEditingContract] = useState<Contract | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  useEffect(() => {
    const status = new URLSearchParams(window.location.search).get("status") ?? undefined;
    if (status) setStatusFilter(status);
  }, []);

  const openCreate = () => {
    setEditingContract(null);
    form.resetFields();
    setModalOpen(true);
  };

  const openEdit = (contract: Contract) => {
    setEditingContract(contract);
    form.setFieldsValue({
      company_id: contract.company_id,
      space_id: contract.space_id,
      area_sqm: Number(contract.area_sqm),
      rate_per_sqm: Number(contract.rate_per_sqm),
      start_date: dayjs(contract.start_date),
      end_date: dayjs(contract.end_date),
      status: contract.status,
    });
    setModalOpen(true);
  };

  const closeModal = () => {
    setModalOpen(false);
    setEditingContract(null);
    form.resetFields();
  };

  const saveContract = (values: ContractFormValues) => {
    const payload = {
      company_id: values.company_id,
      space_id: values.space_id,
      area_sqm: values.area_sqm.toFixed(2),
      rate_per_sqm: values.rate_per_sqm.toFixed(2),
      start_date: values.start_date.format("YYYY-MM-DD"),
      end_date: values.end_date.format("YYYY-MM-DD"),
      ...(values.status ? { status: values.status } : {}),
    };
    if (editingContract) {
      actions.update.mutate({ id: editingContract.id, payload }, { onSuccess: closeModal });
    } else {
      actions.create.mutate(payload, { onSuccess: closeModal });
    }
  };

  const companyNames = useMemo(
    () => new Map((companies.data?.results ?? []).map((company) => [company.id, company.name])),
    [companies.data?.results],
  );
  const spaceNames = useMemo(
    () => new Map((spaces.data ?? []).map((space) => [space.id, space.name])),
    [spaces.data],
  );

  const contracts = useMemo(() => data ?? [], [data]);
  const statusOptions = useMemo(
    () =>
      Array.from(new Set(contracts.map((contract) => contract.status).filter(Boolean)))
        .sort((a, b) => a.localeCompare(b, "pt-PT"))
        .map((status) => ({ label: status, value: status })),
    [contracts],
  );

  const filteredContracts = useMemo(() => {
    const term = normalize(search);
    return contracts.filter((contract) => {
      const companyName = companyNames.get(contract.company_id) ?? contract.company_id;
      const spaceName = spaceNames.get(contract.space_id) ?? contract.space_id;
      const matchesStatus = !statusFilter || normalize(contract.status) === normalize(statusFilter);
      const matchesSearch =
        !term ||
        normalize(companyName).includes(term) ||
        normalize(spaceName).includes(term) ||
        normalize(contract.id).includes(term);
      return matchesStatus && matchesSearch;
    });
  }, [companyNames, contracts, search, spaceNames, statusFilter]);

  const activeContracts = contracts.filter((contract) => normalize(contract.status) === "active");
  const expiringContracts = contracts.filter((contract) => {
    if (!contract.end_date) return false;
    const endDate = new Date(contract.end_date);
    if (Number.isNaN(endDate.getTime())) return false;
    const daysUntilEnd = (endDate.getTime() - Date.now()) / 86_400_000;
    return daysUntilEnd >= 0 && daysUntilEnd <= 30;
  });

  const columns: ColumnsType<Contract> = [
    {
      title: tStaff("columnCompany"),
      dataIndex: "company_id",
      key: "company_id",
      render: (companyId: string) => companyNames.get(companyId) ?? companyId,
    },
    {
      title: tStaff("columnSpace"),
      dataIndex: "space_id",
      key: "space_id",
      render: (spaceId: string) => spaceNames.get(spaceId) ?? spaceId,
    },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    {
      title: tStaff("columnPrice"),
      dataIndex: "monthly_fee",
      key: "monthly_fee",
      align: "right",
      render: formatCurrency,
    },
    {
      title: tStaff("columnStart"),
      dataIndex: "start_date",
      key: "start_date",
      render: formatDate,
    },
    { title: tStaff("columnEnd"), dataIndex: "end_date", key: "end_date", render: formatDate },
    {
      title: tStaff("columnActions"),
      key: "actions",
      width: 260,
      render: (_: unknown, contract) => (
        <Space>
          <Button size="small" onClick={() => openEdit(contract)}>
            Editar
          </Button>
          <Popconfirm
            title="Ativar contrato?"
            okText="Ativar"
            cancelText="Cancelar"
            onConfirm={() => actions.activate.mutate(contract.id)}
          >
            <Button
              size="small"
              disabled={contract.status === "active"}
              loading={actions.activate.isPending}
            >
              Ativar
            </Button>
          </Popconfirm>
          <Popconfirm
            title="Terminar contrato?"
            okText="Terminar"
            cancelText="Cancelar"
            onConfirm={() =>
              actions.terminate.mutate({ id: contract.id, payload: { reason: "Staff request" } })
            }
          >
            <Button size="small" danger disabled={contract.status === "terminated"}>
              Terminar
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  if (isLoading || companies.isLoading || spaces.isLoading) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (isError || companies.isError || spaces.isError) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title={tStaff("contractsKpiTotal")} value={contracts.length} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title={tStaff("contractsKpiActive")} value={activeContracts.length} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title={tStaff("contractsKpiExpiring")} value={expiringContracts.length} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={tStaff("contractsKpiMonthlyRevenue")}
              value={sumMonthlyFee(activeContracts)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
      </Row>

      {expiringContracts.length > 0 ? (
        <Alert
          type="warning"
          showIcon
          message={tStaff("contractsExpiringAlert")}
          description={`${expiringContracts.length} ${tStaff("contractsExpiringAlertDescription")}`}
        />
      ) : null}

      <Card
        title={
          <Space>
            <FileTextOutlined aria-hidden />
            <span>{tStaff("navContracts")}</span>
          </Space>
        }
        extra={
          <Typography.Text type="secondary">
            {tStaff("contractsResultCount").replace("{count}", String(filteredContracts.length))}
          </Typography.Text>
        }
      >
        <Space wrap style={{ marginBottom: 16 }} size="middle">
          <Button type="primary" onClick={openCreate}>
            Novo contrato
          </Button>
          <Input.Search
            allowClear
            placeholder={tStaff("contractsSearchPlaceholder")}
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            style={{ width: 320 }}
          />
          <Select
            allowClear
            placeholder={tStaff("contractsStatusPlaceholder")}
            value={statusFilter}
            onChange={setStatusFilter}
            options={statusOptions}
            style={{ width: 220 }}
          />
        </Space>
        <Table<Contract>
          rowKey="id"
          columns={columns}
          dataSource={filteredContracts}
          locale={{ emptyText: tStaff("emptyData") }}
          scroll={{ x: 900 }}
          expandable={{
            expandedRowRender: (contract) => (
              <Space direction="vertical" size="middle" style={{ width: "100%" }}>
                <Descriptions size="small" column={{ xs: 1, md: 3 }} bordered>
                  <Descriptions.Item label={tStaff("contractsArea")}>
                    {contract.area_sqm} m²
                  </Descriptions.Item>
                  <Descriptions.Item label={tStaff("contractsRatePerSqm")}>
                    {formatCurrency(contract.rate_per_sqm)}
                  </Descriptions.Item>
                  <Descriptions.Item label={tStaff("contractsTerminationReason")}>
                    {contract.termination_reason || "—"}
                  </Descriptions.Item>
                </Descriptions>
                <Card type="inner" title={tStaff("documentsTitle")}>
                  <DocumentManager entityType="Contract" entityId={contract.id} />
                </Card>
              </Space>
            ),
          }}
        />
      </Card>
      <Modal
        title={editingContract ? "Editar contrato" : "Novo contrato"}
        open={modalOpen}
        onCancel={closeModal}
        onOk={() => form.submit()}
        confirmLoading={actions.create.isPending || actions.update.isPending}
        destroyOnClose
      >
        <Form form={form} layout="vertical" onFinish={saveContract}>
          <Form.Item name="company_id" label={tStaff("columnCompany")} rules={[{ required: true }]}>
            <Select
              showSearch
              options={(companies.data?.results ?? []).map((company) => ({
                label: company.name,
                value: company.id,
              }))}
              optionFilterProp="label"
            />
          </Form.Item>
          <Form.Item name="space_id" label={tStaff("columnSpace")} rules={[{ required: true }]}>
            <Select
              showSearch
              options={(spaces.data ?? []).map((space) => ({ label: space.name, value: space.id }))}
              optionFilterProp="label"
            />
          </Form.Item>
          <Form.Item name="area_sqm" label={tStaff("contractsArea")} rules={[{ required: true }]}>
            <InputNumber min={0.01} precision={2} addonAfter="m²" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="rate_per_sqm"
            label={tStaff("contractsRatePerSqm")}
            rules={[{ required: true }]}
          >
            <InputNumber min={0} precision={2} addonBefore="€" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="start_date" label={tStaff("columnStart")} rules={[{ required: true }]}>
            <DatePicker format="YYYY-MM-DD" style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="end_date"
            label={tStaff("columnEnd")}
            dependencies={["start_date"]}
            rules={[
              { required: true },
              ({ getFieldValue }) => ({
                validator(_, value: Dayjs | undefined) {
                  const start = getFieldValue("start_date") as Dayjs | undefined;
                  if (!value || !start || value.isAfter(start, "day")) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("A data de fim deve ser posterior ao início."));
                },
              }),
            ]}
          >
            <DatePicker format="YYYY-MM-DD" style={{ width: "100%" }} />
          </Form.Item>
          {editingContract ? (
            <Form.Item name="status" label={tStaff("columnStatus")}>
              <Select options={statusOptions} />
            </Form.Item>
          ) : null}
        </Form>
      </Modal>
    </Space>
  );
}
