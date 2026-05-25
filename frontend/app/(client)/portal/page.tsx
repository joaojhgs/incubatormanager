"use client";

import { CalendarOutlined, QuestionCircleOutlined } from "@ant-design/icons";
import { Button, Card, Col, Result, Row, Space, Spin, Statistic, Typography, Tag } from "antd";
import Link from "next/link";

import { useAuth } from "@/components/auth/AuthProvider";
import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import {
  useCompanyContracts,
  useCompanyPayments,
  useMyBookings,
  useMyTickets,
  useSpaces,
} from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";
import { normalizeStatus, statusLabel } from "@/lib/i18n/status";

const { Title, Text } = Typography;

export default function ClientPortalHomePage() {
  const { user, isReady } = useAuth();
  const companyId = user?.companyId ?? null;
  const contracts = useCompanyContracts(companyId);
  const payments = useCompanyPayments(companyId);
  const bookings = useMyBookings();
  const tickets = useMyTickets();
  const spaces = useSpaces();
  const firstName = user?.email?.split("@")[0] ?? "";

  if (
    !isReady ||
    [contracts, payments, bookings, tickets, spaces].some((query) => query.isLoading)
  ) {
    return <Spin size="large" tip={tClient("pageLoading")} />;
  }
  if (!companyId)
    return (
      <Result
        status="warning"
        title={tClient("pageNoCompany")}
        subTitle={tClient("pageNoCompanyAction")}
      />
    );
  if ([contracts, payments, bookings, tickets, spaces].some((query) => query.isError)) {
    return <Result status="error" title={tClient("clientLoadError")} />;
  }

  const activeContract =
    contracts.data?.find((contract) => normalizeStatus(contract.status) === "active") ??
    contracts.data?.[0];
  const spaceName =
    spaces.data?.find((space) => space.id === activeContract?.space_id)?.name ??
    activeContract?.space_id;
  const nextPayment =
    payments.data?.find((payment) => normalizeStatus(payment.status) !== "paid") ??
    payments.data?.[0];
  const openTicketCount =
    tickets.data?.filter(
      (ticket) => !["closed", "resolved"].includes(normalizeStatus(ticket.status)),
    ).length ?? 0;
  const activeBookingCount =
    bookings.data?.filter((booking) =>
      ["pending", "approved"].includes(normalizeStatus(booking.status)),
    ).length ?? 0;

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Card>
        <Row justify="space-between" align="middle">
          <Col>
            <Title level={3} style={{ margin: 0 }}>
              {tClient("welcomeBack").replace("{name}", firstName)}
            </Title>
            <Text type="secondary">{companyId}</Text>
          </Col>
          <Col>
            {activeContract ? (
              statusTag(activeContract.status)
            ) : (
              <Tag>{tClient("clientEmptyData")}</Tag>
            )}
          </Col>
        </Row>
      </Card>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("monthlyFee")}
              value={Number(activeContract?.monthly_fee ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("nextPayment")}
              value={nextPayment ? formatDate(nextPayment.due_date) : "—"}
              formatter={(val) => val}
            />
            {nextPayment ? statusTag(nextPayment.status) : <Tag>{tClient("clientEmptyData")}</Tag>}
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title={tClient("openTickets")}
              value={openTicketCount}
              prefix={<QuestionCircleOutlined />}
            />
            <Text type="secondary">
              {activeBookingCount} {tClient("navBookings")}
            </Text>
          </Card>
        </Col>
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={14}>
          <Card title={tClient("contractSummary")}>
            <Space direction="vertical" style={{ width: "100%" }}>
              <Text>
                {tClient("contractSpace")}: <Text strong>{spaceName ?? "—"}</Text>
              </Text>
              <Text>
                {tClient("contractArea")}: <Text strong>{activeContract?.area_sqm ?? "—"}</Text>
              </Text>
              <Text>
                {tClient("contractMonthlyFee")}:{" "}
                <Text strong>{formatCurrency(activeContract?.monthly_fee)}</Text>
              </Text>
              <Text>
                {tClient("contractPeriod")}:{" "}
                <Text strong>
                  {formatDate(activeContract?.start_date)} — {formatDate(activeContract?.end_date)}
                </Text>
              </Text>
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
            <Space direction="vertical" style={{ width: "100%" }}>
              {(payments.data ?? []).slice(0, 3).map((payment) => (
                <Text key={payment.id}>
                  {formatCurrency(payment.amount)} · {statusLabel(payment.status)} ·{" "}
                  {formatDate(payment.due_date)}
                </Text>
              ))}
              {payments.data?.length ? null : (
                <Text type="secondary">{tClient("paymentsEmpty")}</Text>
              )}
            </Space>
            <div style={{ marginTop: 16 }}>
              <Link href="/portal/payments" prefetch={false}>
                {tClient("viewAllPayments")}
              </Link>
            </div>
          </Card>
        </Col>
      </Row>
      <Card title={tClient("quickActions")}>
        <Space size="middle">
          <Link href="/portal/bookings/new" prefetch={false}>
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
