"use client";

import { Card, Col, Result, Row, Spin, Statistic } from "antd";

import {
  useBookings,
  useCompanies,
  useContracts,
  useFinanceDashboard,
  useTickets,
} from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";

export default function StaffDashboardPage() {
  const companies = useCompanies({ page_size: 1 });
  const contracts = useContracts();
  const bookings = useBookings();
  const tickets = useTickets();
  const finance = useFinanceDashboard();

  if ([companies, contracts, bookings, tickets, finance].some((query) => query.isLoading)) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if ([companies, contracts, bookings, tickets, finance].some((query) => query.isError)) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  const pendingBookings =
    bookings.data?.filter((booking) => booking.status === "Pending").length ?? 0;
  const openTickets = tickets.data?.filter((ticket) => ticket.status !== "Closed").length ?? 0;

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic title={tStaff("dashboardKpiCompanies")} value={companies.data?.count ?? 0} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic title={tStaff("dashboardKpiContracts")} value={contracts.data?.length ?? 0} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic title={tStaff("dashboardKpiPendingBookings")} value={pendingBookings} />
        </Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic title={tStaff("dashboardKpiOpenTickets")} value={openTickets} />
        </Card>
      </Col>
      <Col span={24}>
        <Card title={tStaff("dashboardFinanceSummary")}>
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
            </Col>
          </Row>
        </Card>
      </Col>
    </Row>
  );
}
