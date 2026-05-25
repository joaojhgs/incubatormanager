"use client";

import { CalendarOutlined, FileTextOutlined, HomeOutlined } from "@ant-design/icons";
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
  Typography,
} from "antd";

import { useAuth } from "@/components/auth/AuthProvider";
import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import { useCompanyContracts, useSpaces } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";

function daysUntil(value: string | null | undefined): number | null {
  if (!value) return null;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return null;
  return Math.ceil((date.getTime() - Date.now()) / 86_400_000);
}

export default function ClientContractPage() {
  const { user, isReady } = useAuth();
  const companyId = user?.companyId ?? null;
  const { data, isLoading, isError } = useCompanyContracts(companyId);
  const spaces = useSpaces();
  const contract = data?.[0];

  if (!isReady || isLoading || spaces.isLoading)
    return <Spin size="large" tip={tClient("pageLoading")} />;
  if (!companyId)
    return (
      <Result
        status="warning"
        title={tClient("pageNoCompany")}
        subTitle={tClient("pageNoCompanyAction")}
      />
    );
  if (isError || spaces.isError)
    return <Result status="error" title={tClient("clientLoadError")} />;
  if (!contract) return <Result status="info" title={tClient("clientEmptyData")} />;

  const remainingDays = daysUntil(contract.end_date);
  const spaceName =
    spaces.data?.find((space) => space.id === contract.space_id)?.name ?? contract.space_id;

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Card>
        <Space direction="vertical" size={4}>
          <Typography.Text type="secondary">{tClient("pageContractTitle")}</Typography.Text>
          <Typography.Title level={3} style={{ margin: 0 }}>
            {tClient("contractSummary")}
          </Typography.Title>
          {statusTag(contract.status)}
        </Space>
      </Card>

      {remainingDays !== null && remainingDays <= 30 && remainingDays >= 0 ? (
        <Alert
          type="warning"
          showIcon
          message={tClient("contractEndingSoon")}
          description={tClient("contractEndingSoonDescription").replace(
            "{days}",
            String(remainingDays),
          )}
        />
      ) : null}

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("contractMonthlyFee")}
              value={Number(contract.monthly_fee ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("contractArea")}
              value={Number(contract.area_sqm ?? 0)}
              suffix="m²"
              prefix={<HomeOutlined />}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("contractDaysRemaining")}
              value={remainingDays ?? "—"}
              prefix={<CalendarOutlined />}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title={
          <Space>
            <FileTextOutlined aria-hidden />
            <span>{tClient("contractTermsTitle")}</span>
          </Space>
        }
      >
        <Descriptions bordered layout="vertical" column={{ xs: 1, md: 2 }}>
          <Descriptions.Item label={tClient("columnStatus")}>
            {statusTag(contract.status)}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("contractSpace")}>{spaceName}</Descriptions.Item>
          <Descriptions.Item label={tClient("contractArea")}>
            {contract.area_sqm} m²
          </Descriptions.Item>
          <Descriptions.Item label={tClient("contractRate")}>
            {formatCurrency(contract.rate_per_sqm)}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("contractMonthlyFee")}>
            {formatCurrency(contract.monthly_fee)}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("contractPeriod")}>
            {formatDate(contract.start_date)} — {formatDate(contract.end_date)}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("contractTerminationReason")} span={2}>
            {contract.termination_reason || "—"}
          </Descriptions.Item>
        </Descriptions>
      </Card>
    </Space>
  );
}
