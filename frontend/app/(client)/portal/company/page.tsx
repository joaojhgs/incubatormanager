"use client";

import { BankOutlined, IdcardOutlined, TeamOutlined } from "@ant-design/icons";
import { Card, Col, Descriptions, Result, Row, Space, Spin, Statistic, Typography } from "antd";

import { useAuth } from "@/components/auth/AuthProvider";
import { ArchivedBadge, EmployeeManager, MaturityStageTag } from "@/components/companies";
import { DocumentList } from "@/components/documents";
import { useCompany } from "@/lib/hooks/useCompanies";
import { tClient } from "@/lib/i18n/clientPortal";

const { Text } = Typography;

export default function ClientCompanyPage() {
  const { user, isReady } = useAuth();
  const companyId = user?.companyId ?? null;
  const { data, isLoading, isError } = useCompany(companyId ?? "");

  if (!isReady || isLoading) {
    return <Spin size="large" tip={tClient("pageLoading")} />;
  }

  if (!companyId) {
    return (
      <Result
        status="warning"
        title={tClient("pageNoCompany")}
        subTitle={tClient("pageNoCompanyAction")}
      />
    );
  }

  if (isError) {
    return <Result status="error" title={tClient("pageLoadError")} />;
  }

  if (!data) {
    return (
      <Result
        status="warning"
        title={tClient("pageNoCompany")}
        subTitle={tClient("pageNoCompanyAction")}
      />
    );
  }

  const activeEmployees = data.employees?.filter((employee) => employee.is_active).length ?? 0;

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Card>
        <Space direction="vertical" size={4}>
          <Text type="secondary">{tClient("pageCompanyTitle")}</Text>
          <Typography.Title level={3} style={{ margin: 0 }}>
            {data.name} <ArchivedBadge archived={!data.is_active} />
          </Typography.Title>
          <Space wrap>
            <MaturityStageTag stageName={data.maturity_stage_name ?? ""} />
            <Text type="secondary">{data.cae_description ?? tClient("clientEmptyData")}</Text>
          </Space>
        </Space>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("companyFieldTaxId")}
              value={data.tax_id}
              prefix={<IdcardOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("companyActiveEmployees")}
              value={activeEmployees}
              prefix={<TeamOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("companyFieldCompany")}
              value={
                data.is_active ? tClient("companyStatusActive") : tClient("companyStatusArchived")
              }
              prefix={<BankOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card title={tClient("companyFieldSection")}>
        <Descriptions bordered layout="vertical" size="middle" column={{ xs: 1, md: 2 }}>
          <Descriptions.Item label={tClient("companyFieldCompany")}>
            <Text strong>{data.name}</Text>
          </Descriptions.Item>
          <Descriptions.Item label={tClient("companyFieldLegalRepresentative")}>
            {data.legal_representative}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("companyFieldPhone")}>
            {data.phone || "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("companyFieldEmail")}>
            {data.email || "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("companyFieldAddress")} span={2}>
            {data.address || "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("companyFieldDescription")} span={2}>
            {data.description || "—"}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title="Colaboradores da empresa">
        <EmployeeManager companyId={data.id} employees={data.employees ?? []} />
      </Card>

      <Card title={tClient("documentsTitle")}>
        <DocumentList entityType="Company" entityId={data.id} readOnly />
      </Card>
    </Space>
  );
}
