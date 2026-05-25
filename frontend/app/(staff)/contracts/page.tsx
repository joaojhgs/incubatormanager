"use client";

import { FileTextOutlined } from "@ant-design/icons";
import {
  Alert,
  Card,
  Col,
  Descriptions,
  Input,
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
import { useMemo, useState } from "react";

import { DocumentList } from "@/components/documents";
import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import type { Contract } from "@/lib/api/contracts";
import { useCompanies, useContracts, useSpaces } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";

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
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [search, setSearch] = useState("");

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
      const matchesStatus = !statusFilter || contract.status === statusFilter;
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
                  <DocumentList entityType="Contract" entityId={contract.id} readOnly />
                </Card>
              </Space>
            ),
          }}
        />
      </Card>
    </Space>
  );
}
