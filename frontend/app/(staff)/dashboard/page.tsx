"use client";

import {
  Alert,
  Button,
  Card,
  Col,
  List,
  Progress,
  Result,
  Row,
  Space,
  Spin,
  Statistic,
  Table,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import Link from "next/link";
import { useMemo } from "react";

import { formatCurrency, formatDateTime, statusTag } from "@/components/operations/format";
import {
  useBookings,
  useCompanies,
  useContracts,
  useFinanceDashboard,
  useTickets,
} from "@/lib/hooks";
import type { Booking } from "@/lib/api/bookings";
import { tStaff } from "@/lib/i18n/staffNav";

export default function StaffDashboardPage() {
  const companies = useCompanies({ page_size: 1 });
  const contracts = useContracts();
  const bookings = useBookings();
  const tickets = useTickets();
  const finance = useFinanceDashboard();

  const queries = [companies, contracts, bookings, tickets, finance];
  const recentBookingColumns: ColumnsType<Booking> = [
    {
      title: tStaff("columnCompany"),
      dataIndex: "company_id",
      key: "company_id",
      ellipsis: true,
    },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    {
      title: tStaff("columnStart"),
      dataIndex: "start_time",
      key: "start_time",
      render: formatDateTime,
    },
    {
      title: tStaff("columnPrice"),
      dataIndex: "quoted_price",
      key: "quoted_price",
      align: "right",
      render: formatCurrency,
    },
  ];

  const recentBookings = useMemo(
    () =>
      [...(bookings.data ?? [])]
        .sort((a, b) => new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
        .slice(0, 5),
    [bookings.data],
  );

  if (queries.some((query) => query.isLoading)) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (queries.some((query) => query.isError)) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  const pendingBookings =
    bookings.data?.filter((booking) => booking.status === "Pending").length ?? 0;
  const approvedBookings =
    bookings.data?.filter((booking) => booking.status === "Approved").length ?? 0;
  const openTickets = tickets.data?.filter((ticket) => ticket.status !== "Closed").length ?? 0;
  const overdueCount = finance.data?.overdue ?? 0;
  const totalPayments = finance.data?.total_payments ?? 0;
  const overduePercent = totalPayments > 0 ? Math.round((overdueCount / totalPayments) * 100) : 0;

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card extra={<Link href="/companies">{tStaff("dashboardViewDetails")}</Link>}>
          <Statistic title={tStaff("dashboardKpiCompanies")} value={companies.data?.count ?? 0} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card extra={<Link href="/contracts">{tStaff("dashboardViewDetails")}</Link>}>
          <Statistic title={tStaff("dashboardKpiContracts")} value={contracts.data?.length ?? 0} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card extra={<Link href="/bookings">{tStaff("dashboardViewDetails")}</Link>}>
          <Statistic title={tStaff("dashboardKpiPendingBookings")} value={pendingBookings} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card extra={<Link href="/tickets">{tStaff("dashboardViewDetails")}</Link>}>
          <Statistic title={tStaff("dashboardKpiOpenTickets")} value={openTickets} />
        </Card>
      </Col>

      <Col xs={24} lg={16}>
        <Card
          title={tStaff("dashboardFinanceSummary")}
          extra={<Link href="/finance">{tStaff("dashboardOpenReport")}</Link>}
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={8}>
              <Statistic
                title={tStaff("financePaidAmount")}
                value={Number(finance.data?.paid_amount ?? 0)}
                prefix="€"
                precision={2}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title={tStaff("financePendingAmount")}
                value={Number(finance.data?.pending_amount ?? 0)}
                prefix="€"
                precision={2}
              />
            </Col>
            <Col xs={24} sm={8}>
              <Statistic
                title={tStaff("financeOverdueAmount")}
                value={Number(finance.data?.overdue_amount ?? 0)}
                prefix="€"
                precision={2}
              />
              <Progress percent={overduePercent} size="small" status="exception" />
            </Col>
          </Row>
        </Card>
      </Col>
      <Col xs={24} lg={8}>
        <Card title={tStaff("dashboardOpsFocus")}>
          <List
            size="small"
            dataSource={[
              `${pendingBookings} ${tStaff("dashboardPendingBookingHint")}`,
              `${approvedBookings} ${tStaff("dashboardApprovedBookingHint")}`,
              `${overdueCount} ${tStaff("dashboardOverduePaymentHint")}`,
            ]}
            renderItem={(item) => <List.Item>{item}</List.Item>}
          />
        </Card>
      </Col>

      <Col span={24}>
        <Card
          title={tStaff("dashboardRecentBookings")}
          extra={
            <Space>
              <Button size="small" href="/bookings">
                {tStaff("dashboardBookingDrillthrough")}
              </Button>
              <Button size="small" href="/inventory">
                {tStaff("dashboardInventoryDrillthrough")}
              </Button>
            </Space>
          }
        >
          {recentBookings.length === 0 ? (
            <Alert type="info" showIcon message={tStaff("dashboardNoRecentBookings")} />
          ) : (
            <Table<Booking>
              rowKey="id"
              columns={recentBookingColumns}
              dataSource={recentBookings}
              pagination={false}
              size="small"
            />
          )}
        </Card>
      </Col>
    </Row>
  );
}
