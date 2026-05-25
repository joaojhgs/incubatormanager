"use client";

import { Card, Descriptions, Result, Spin, Typography } from "antd";

import { useCompany } from "@/lib/hooks/useCompanies";
import { useAuth } from "@/components/auth/AuthProvider";
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

  return (
    <Card title={tClient("pageCompanyTitle")}>
      <Descriptions bordered layout="vertical" size="middle" column={1}>
        <Descriptions.Item label={tClient("companyFieldCompany")}>
          <Text strong>{data.name}</Text>
        </Descriptions.Item>
        <Descriptions.Item label={tClient("companyFieldTaxId")}>{data.tax_id}</Descriptions.Item>
        <Descriptions.Item label={tClient("companyFieldLegalRepresentative")}>
          {data.legal_representative}
        </Descriptions.Item>
        <Descriptions.Item label={tClient("companyFieldPhone")}>
          {data.phone || "—"}
        </Descriptions.Item>
        <Descriptions.Item label={tClient("companyFieldEmail")}>
          {data.email || "—"}
        </Descriptions.Item>
        <Descriptions.Item label={tClient("companyFieldAddress")}>
          {data.address || "—"}
        </Descriptions.Item>
      </Descriptions>
    </Card>
  );
}
