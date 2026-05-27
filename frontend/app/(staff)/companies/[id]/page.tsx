"use client";

import { ArrowLeftOutlined, EditOutlined } from "@ant-design/icons";
import { Button, Card, Col, Descriptions, Flex, Result, Row, Space, Spin, Typography } from "antd";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useMemo } from "react";

import { ArchivedBadge, EmployeeManager, MaturityStageTag } from "@/components/companies";
import { DocumentManager } from "@/components/documents";
import { BarList, DonutChart, TrendBars, type ChartDatum } from "@/components/visual/InsightCharts";
import { useCompany, useCompanyContracts, useMaturityStages } from "@/lib/hooks";
import { tCompany } from "@/lib/i18n/companies";

function getParamId(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

function stageOrder(stageName: string, stages: { name: string; display_order: number }[]): number {
  return stages.find((stage) => stage.name === stageName)?.display_order ?? 0;
}

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const id = getParamId(params.id);
  const { data, isLoading, isError } = useCompany(id);
  const contracts = useCompanyContracts(id);
  const maturityStages = useMaturityStages();

  const employeeRoleData = useMemo<ChartDatum[]>(() => {
    const counts = new Map<string, number>();
    for (const employee of data?.employees ?? []) {
      counts.set(employee.type, (counts.get(employee.type) ?? 0) + 1);
    }
    return Array.from(counts, ([label, value]) => ({ label, value }));
  }, [data?.employees]);

  const maturityTrendData = useMemo<ChartDatum[]>(() => {
    const stages = maturityStages.data ?? [];
    const contractPoints = (contracts.data ?? [])
      .map((contract) => {
        const stage = stages.find(
          (item) => Number(item.rate_per_sqm) === Number(contract.rate_per_sqm),
        );
        return {
          label: new Date(contract.start_date).toLocaleDateString("pt-PT", {
            month: "short",
            year: "2-digit",
          }),
          value: stage?.display_order ?? stageOrder(data?.maturity_stage_name ?? "", stages),
        };
      })
      .filter((item) => item.value > 0)
      .sort((a, b) => a.label.localeCompare(b.label));

    if (contractPoints.length > 0) return contractPoints;
    const currentOrder = stageOrder(data?.maturity_stage_name ?? "", stages);
    return currentOrder > 0 ? [{ label: "Atual", value: currentOrder }] : [];
  }, [contracts.data, data?.maturity_stage_name, maturityStages.data]);

  const contractRevenueData = useMemo<ChartDatum[]>(
    () =>
      (contracts.data ?? []).map((contract) => ({
        label: new Date(contract.start_date).toLocaleDateString("pt-PT", {
          month: "short",
          year: "2-digit",
        }),
        value: Number(contract.monthly_fee),
      })),
    [contracts.data],
  );

  if (isLoading) return <Spin size="large" tip={tCompany("formLoading")} />;
  if (isError || !data) {
    return (
      <Result
        status="404"
        title={tCompany("detailNotFound")}
        extra={
          <Link href="/companies" prefetch={false}>
            <Button type="primary">{tCompany("formBackToList")}</Button>
          </Link>
        }
      />
    );
  }

  return (
    <Flex vertical gap={16}>
      <Flex justify="space-between" align="center" wrap gap="small">
        <Space direction="vertical" size={0}>
          <Link href="/companies" prefetch={false}>
            <Button icon={<ArrowLeftOutlined aria-hidden />} type="link" style={{ paddingLeft: 0 }}>
              {tCompany("formBackToList")}
            </Button>
          </Link>
          <Typography.Title level={3} style={{ margin: 0 }}>
            {data.name} <ArchivedBadge archived={!data.is_active} />
          </Typography.Title>
        </Space>
        <Link href={`/companies/${id}/edit`} prefetch={false}>
          <Button type="primary" icon={<EditOutlined aria-hidden />}>
            {tCompany("listActionEdit")}
          </Button>
        </Link>
      </Flex>

      <Card title={tCompany("detailProfileTitle")}>
        <Descriptions bordered column={{ xs: 1, md: 2 }}>
          <Descriptions.Item label={tCompany("formFieldTaxId")}>{data.tax_id}</Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldLegalRepresentative")}>
            {data.legal_representative}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldCae")}>
            {data.cae_description ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldMaturityStage")}>
            <MaturityStageTag stageName={data.maturity_stage_name ?? ""} />
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldEmail")}>
            {data.email ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldPhone")}>
            {data.phone ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldAddress")} span={2}>
            {data.address ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldDescription")} span={2}>
            {data.description ?? "—"}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8}>
          <Card title="Distribuição de colaboradores" style={{ height: "100%" }}>
            <DonutChart data={employeeRoleData} centerLabel="pessoas" />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Evolução de maturidade" style={{ height: "100%" }}>
            <TrendBars data={maturityTrendData} />
            <Typography.Text type="secondary">
              Escala por ordem dos estágios configurados; contratos históricos inferem o estágio
              pela taxa aplicada.
            </Typography.Text>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Receita contratual no tempo" style={{ height: "100%" }}>
            <BarList data={contractRevenueData} currency />
          </Card>
        </Col>
      </Row>

      <Card title={tCompany("detailEmployeesTitle")}>
        <EmployeeManager companyId={id} employees={data.employees ?? []} />
      </Card>

      <Card title={tCompany("detailDocumentsTitle")}>
        <DocumentManager entityType="Company" entityId={id} />
      </Card>
    </Flex>
  );
}
