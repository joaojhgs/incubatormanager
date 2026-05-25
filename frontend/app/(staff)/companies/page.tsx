"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import {
  BankOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  SearchOutlined,
} from "@ant-design/icons";
import {
  Button,
  Card,
  Col,
  Flex,
  Input,
  Row,
  Select,
  Space,
  Statistic,
  Switch,
  Table,
  Typography,
  Popconfirm,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import Link from "next/link";

import { ArchivedBadge, MaturityStageTag } from "@/components/companies";
import {
  useArchiveCompany,
  useCAECodes,
  useCompanies,
  useCompanyStats,
  useMaturityStages,
} from "@/lib/hooks";
import { tCompany } from "@/lib/i18n/companies";
import type { Company } from "@/lib/api/companies";

const { Title } = Typography;

/** Page size options for the table. */
const PAGE_SIZE = 20;

export default function CompaniesListPage() {
  // ── Filters ──────────────────────────────────────────────────────────
  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [maturityStageId, setMaturityStageId] = useState<string | undefined>(undefined);
  const [caeId, setCaeId] = useState<string | undefined>(undefined);
  const [activeOnly, setActiveOnly] = useState(true);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const active = params.get("is_active");
    if (active === "false") setActiveOnly(false);
    if (active === "true") setActiveOnly(true);
    const search = params.get("search");
    if (search) setSearchInput(search);
  }, []);

  // Debounce search input: 300ms delay before triggering API query
  useEffect(() => {
    if (debounceTimer.current !== null) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => {
      setDebouncedSearch(searchInput);
      setPage(1);
    }, 300);
    return () => {
      if (debounceTimer.current !== null) clearTimeout(debounceTimer.current);
    };
  }, [searchInput]);

  // ── Data ─────────────────────────────────────────────────────────────
  const { data, isLoading } = useCompanies({
    page,
    page_size: PAGE_SIZE,
    search: debouncedSearch || undefined,
    is_active: activeOnly ? true : undefined,
    maturity_stage_id: maturityStageId,
    cae_id: caeId,
  });

  const archiveMutation = useArchiveCompany();
  const caeQuery = useCAECodes();
  const maturityQuery = useMaturityStages();
  const statsQuery = useCompanyStats();

  const caeOptions = useMemo(
    () =>
      (caeQuery.data ?? []).map((cae) => ({
        value: cae.id,
        label: `${cae.code} — ${cae.description}`,
      })),
    [caeQuery.data],
  );

  const maturityOptions = useMemo(
    () =>
      (maturityQuery.data ?? []).map((stage) => ({
        value: stage.id,
        label: stage.name,
      })),
    [maturityQuery.data],
  );

  // ── Handlers ─────────────────────────────────────────────────────────
  const handleArchive = useCallback(
    (id: string) => {
      archiveMutation.mutate(id);
    },
    [archiveMutation],
  );

  // ── Table columns ────────────────────────────────────────────────────
  const columns: ColumnsType<Company> = useMemo(
    () => [
      {
        title: tCompany("listColumnCompanyName"),
        dataIndex: "name",
        key: "name",
        render: (name: string, record: Company) => (
          <Space>
            <Link href={`/companies/${record.id}`} prefetch={false}>
              {name}
            </Link>
            <ArchivedBadge archived={!record.is_active} />
          </Space>
        ),
      },
      {
        title: tCompany("listColumnNif"),
        dataIndex: "tax_id",
        key: "tax_id",
        width: 140,
      },
      {
        title: tCompany("listColumnSector"),
        dataIndex: "cae_description",
        key: "cae_id",
        width: 180,
        render: (_: unknown, record: Company) => record.cae_description ?? "—",
      },
      {
        title: tCompany("listColumnMaturityStage"),
        dataIndex: "maturity_stage_name",
        key: "maturity_stage_id",
        width: 160,
        render: (_: unknown, record: Company) => (
          <MaturityStageTag stageName={record.maturity_stage_name ?? ""} />
        ),
      },
      {
        title: tCompany("listColumnActions"),
        key: "actions",
        width: 160,
        render: (_: unknown, record: Company) => (
          <Space>
            <Link href={`/companies/${record.id}`} prefetch={false}>
              <Button
                type="text"
                size="small"
                icon={<EyeOutlined aria-hidden />}
                aria-label={tCompany("listActionView")}
              />
            </Link>
            <Link href={`/companies/${record.id}/edit`} prefetch={false}>
              <Button
                type="text"
                size="small"
                icon={<EditOutlined aria-hidden />}
                aria-label={tCompany("listActionEdit")}
              />
            </Link>
            {record.is_active && (
              <Popconfirm
                title={tCompany("listArchiveConfirmTitle")}
                description={tCompany("listArchiveConfirmDescription")}
                onConfirm={() => handleArchive(record.id)}
                okText={tCompany("listActionArchive")}
                okButtonProps={{ danger: true }}
              >
                <Button
                  type="text"
                  size="small"
                  danger
                  icon={<DeleteOutlined aria-hidden />}
                  aria-label={tCompany("listActionArchive")}
                />
              </Popconfirm>
            )}
          </Space>
        ),
      },
    ],
    [handleArchive],
  );

  const visibleCompanies = data?.results ?? [];
  const visibleActiveCount = visibleCompanies.filter((company) => company.is_active).length;
  const visibleArchivedCount = visibleCompanies.length - visibleActiveCount;

  // ── Render ───────────────────────────────────────────────────────────
  return (
    <>
      <Flex justify="space-between" align="center" style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <BankOutlined aria-hidden style={{ marginRight: 8 }} />
          {tCompany("listTitle")}
        </Title>
        <Link href="/companies/new" prefetch={false}>
          <Button type="primary" icon={<PlusOutlined aria-hidden />}>
            {tCompany("listRegisterButton")}
          </Button>
        </Link>
      </Flex>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={tCompany("listKpiTotal")}
              value={statsQuery.data?.total ?? data?.count ?? 0}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={tCompany("listKpiActive")}
              value={statsQuery.data?.active ?? visibleActiveCount}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={tCompany("listKpiArchived")}
              value={statsQuery.data?.inactive ?? visibleArchivedCount}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic title={tCompany("listKpiVisible")} value={visibleCompanies.length} />
          </Card>
        </Col>
      </Row>

      <Card
        title={tCompany("listDirectoryTitle")}
        extra={
          <Typography.Text type="secondary">
            {tCompany("listResultCount").replace("{count}", String(data?.count ?? 0))}
          </Typography.Text>
        }
      >
        <Space wrap style={{ marginBottom: 16 }} size="middle">
          <Input
            placeholder={tCompany("listSearchPlaceholder")}
            prefix={<SearchOutlined aria-hidden />}
            allowClear
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            style={{ width: 280 }}
          />
          <Select
            allowClear
            placeholder={tCompany("listFilterMaturityStage")}
            value={maturityStageId}
            onChange={(val) => {
              setMaturityStageId(val);
              setPage(1);
            }}
            style={{ width: 200 }}
            loading={maturityQuery.isLoading}
            options={maturityOptions}
            showSearch
            optionFilterProp="label"
          />
          <Select
            allowClear
            placeholder={tCompany("listFilterSector")}
            value={caeId}
            onChange={(val) => {
              setCaeId(val);
              setPage(1);
            }}
            style={{ width: 200 }}
            loading={caeQuery.isLoading}
            options={caeOptions}
            showSearch
            optionFilterProp="label"
          />
          <Space>
            <Switch
              checked={activeOnly}
              onChange={(checked) => {
                setActiveOnly(checked);
                setPage(1);
              }}
            />
            <Typography.Text>
              {activeOnly ? tCompany("listFilterActive") : tCompany("listFilterAll")}
            </Typography.Text>
          </Space>
        </Space>

        <Table<Company>
          rowKey="id"
          columns={columns}
          dataSource={visibleCompanies}
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total: data?.count ?? 0,
            showSizeChanger: false,
            showTotal: (total, range) =>
              tCompany("listShowingPagination")
                .replace("{from}", String(range[0]))
                .replace("{to}", String(range[1]))
                .replace("{total}", String(total)),
          }}
          onChange={(pagination) => {
            setPage(pagination.current ?? 1);
          }}
          locale={{
            emptyText: (
              <div style={{ padding: "24px 0" }}>
                <Typography.Text strong>{tCompany("listEmptyTitle")}</Typography.Text>
                <br />
                <Typography.Text type="secondary">
                  {tCompany("listEmptyDescription")}
                </Typography.Text>
              </div>
            ),
          }}
        />
      </Card>
    </>
  );
}
