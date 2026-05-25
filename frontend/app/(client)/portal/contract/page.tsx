"use client";

import { Card, Descriptions, Result, Spin } from "antd";

import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import { useAuth } from "@/components/auth/AuthProvider";
import { useCompanyContracts } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";

export default function ClientContractPage() {
  const { user, isReady } = useAuth();
  const companyId = user?.companyId ?? null;
  const { data, isLoading, isError } = useCompanyContracts(companyId);
  const contract = data?.[0];

  if (!isReady || isLoading) return <Spin size="large" tip={tClient("pageLoading")} />;
  if (!companyId) return <Result status="warning" title={tClient("pageNoCompany")} subTitle={tClient("pageNoCompanyAction")} />;
  if (isError) return <Result status="error" title={tClient("clientLoadError")} />;
  if (!contract) return <Result status="info" title={tClient("clientEmptyData")} />;

  return (
    <Card title={tClient("pageContractTitle")}>
      <Descriptions bordered layout="vertical" column={2}>
        <Descriptions.Item label={tClient("columnStatus")}>{statusTag(contract.status)}</Descriptions.Item>
        <Descriptions.Item label={tClient("contractSpace")}>{contract.space_id}</Descriptions.Item>
        <Descriptions.Item label={tClient("contractArea")}>{contract.area_sqm}</Descriptions.Item>
        <Descriptions.Item label={tClient("contractRate")}>{formatCurrency(contract.rate_per_sqm)}</Descriptions.Item>
        <Descriptions.Item label={tClient("contractMonthlyFee")}>{formatCurrency(contract.monthly_fee)}</Descriptions.Item>
        <Descriptions.Item label={tClient("contractPeriod")}>{formatDate(contract.start_date)} — {formatDate(contract.end_date)}</Descriptions.Item>
      </Descriptions>
    </Card>
  );
}
