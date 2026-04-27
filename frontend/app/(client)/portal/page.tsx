"use client";

import { CalendarOutlined, QuestionCircleOutlined } from "@ant-design/icons";
import { Button, Card, Col, Row, Space, Statistic, Typography, Tag } from "antd";
import Link from "next/link";

import { useAuth } from "@/components/auth/AuthProvider";
import { tClient } from "@/lib/i18n/clientPortal";

const { Title, Text, Paragraph } = Typography;

export default function ClientPortalHomePage() {
  const { user } = useAuth();

  const firstName = user?.email?.split("@")[0] ?? "";

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      {/* Welcome banner */}
      <Card>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              {tClient("welcomeBack").replace("{name}", firstName)}
            </Title>
            <Text type="secondary">{tClient("companyLabel")}</Text>
          </Col>
          <Col>
            <Tag color="green">{tClient("contractStatusActive")}</Tag>
          </Col>
        </Row>
      </Card>

      {/* KPI cards */}
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title={tClient("monthlyFee")} value={80} prefix="€" precision={2} />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {tClient("monthlyFeeSubtitle")}
            </Text>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic title={tClient("nextPayment")} value="1 Mai 2026" formatter={(val) => val} />
            <Tag color="orange">{tClient("nextPaymentPending")}</Tag>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("openTickets")}
              value={2}
              prefix={<QuestionCircleOutlined />}
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              {tClient("openTicketsAwaiting")}
            </Text>
          </Card>
        </Col>
      </Row>

      {/* Contract summary + Recent payments */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title={tClient("contractSummary")}>
            <Space direction="vertical" style={{ width: "100%" }}>
              <Row>
                <Col span={8}>
                  <Text type="secondary">{tClient("contractSpace")}</Text>
                </Col>
                <Col span={16}>
                  <Text strong>—</Text>
                </Col>
              </Row>
              <Row>
                <Col span={8}>
                  <Text type="secondary">{tClient("contractArea")}</Text>
                </Col>
                <Col span={16}>
                  <Text strong>—</Text>
                </Col>
              </Row>
              <Row>
                <Col span={8}>
                  <Text type="secondary">{tClient("contractRate")}</Text>
                </Col>
                <Col span={16}>
                  <Text strong>—</Text>
                </Col>
              </Row>
              <Row>
                <Col span={8}>
                  <Text type="secondary">{tClient("contractPeriod")}</Text>
                </Col>
                <Col span={16}>
                  <Text strong>—</Text>
                </Col>
              </Row>
              <Row>
                <Col span={8}>
                  <Text type="secondary">{tClient("contractMonthlyFee")}</Text>
                </Col>
                <Col span={16}>
                  <Text strong>€80,00</Text>
                </Col>
              </Row>
            </Space>
            <div style={{ marginTop: 16 }}>
              <Link href="/portal/contract" prefetch={false}>
                {tClient("viewFullContract")}
              </Link>
            </div>
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card title={tClient("recentPayments")}>
            <Paragraph type="secondary">{tClient("pagePlaceholderBody")}</Paragraph>
            <div style={{ marginTop: 16 }}>
              <Link href="/portal/payments" prefetch={false}>
                {tClient("viewAllPayments")}
              </Link>
            </div>
          </Card>
        </Col>
      </Row>

      {/* Quick actions */}
      <Card title={tClient("quickActions")}>
        <Space size="middle">
          <Link href="/portal/bookings" prefetch={false}>
            <Button type="primary" icon={<CalendarOutlined aria-hidden />}>
              {tClient("requestBooking")}
            </Button>
          </Link>
          <Link href="/portal/tickets" prefetch={false}>
            <Button icon={<QuestionCircleOutlined aria-hidden />}>{tClient("openTicket")}</Button>
          </Link>
        </Space>
      </Card>
    </Space>
  );
}
