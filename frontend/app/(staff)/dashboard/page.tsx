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
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import Link from "next/link";
import type { CSSProperties } from "react";
import { useMemo } from "react";

import { formatCurrency, formatDateTime, statusTag } from "@/components/operations/format";
import { BarList, DonutChart, TrendBars, type ChartDatum } from "@/components/visual/InsightCharts";
import type { Booking } from "@/lib/api/bookings";
import {
  useBookings,
  useCompanies,
  useContracts,
  useFinanceDashboard,
  useTickets,
} from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";

const { Text, Title } = Typography;

const cardColumnStyle: CSSProperties = { display: "flex" };
const fullHeightCardStyle: CSSProperties = { width: "100%", height: "100%" };
const metricBodyStyle: CSSProperties = { minHeight: 92 };
const chartBodyStyle: CSSProperties = {
  minHeight: 214,
  display: "flex",
  alignItems: "center",
};
const summaryBodyStyle: CSSProperties = { minHeight: 122 };

function statusColor(status: string | undefined): string | undefined {
  if (status === "paid") return "#22c55e";
  if (status === "pending") return "#f59e0b";
  if (status === "overdue") return "#fb7185";
  return undefined;
}

function bookingDayLabel(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("pt-PT", { day: "2-digit", month: "short" });
}

export default function StaffDashboardPage() {
  const companies = useCompanies({ page_size: 200, is_active: true });
  const contracts = useContracts();
  const bookings = useBookings();
  const tickets = useTickets();
  const finance = useFinanceDashboard();

  const queries = [companies, contracts, bookings, tickets, finance];
  const companyNames = useMemo(
    () => new Map((companies.data?.results ?? []).map((company) => [company.id, company.name])),
    [companies.data],
  );
  const recentBookingColumns: ColumnsType<Booking> = [
    {
      title: tStaff("columnCompany"),
      dataIndex: "company_id",
      key: "company_id",
      width: 280,
      ellipsis: true,
      render: (companyId: string | null) =>
        companyId ? (companyNames.get(companyId) ?? companyId) : tStaff("bookingCompanyMissing"),
    },
    {
      title: tStaff("columnStatus"),
      dataIndex: "status",
      key: "status",
      width: 180,
      render: statusTag,
    },
    {
      title: tStaff("columnStart"),
      dataIndex: "start_time",
      key: "start_time",
      width: 220,
      render: formatDateTime,
    },
    {
      title: tStaff("columnPrice"),
      dataIndex: "quoted_price",
      key: "quoted_price",
      width: 160,
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

  const maturityData = useMemo<ChartDatum[]>(() => {
    const counts = new Map<string, number>();
    for (const company of companies.data?.results ?? []) {
      const label = company.maturity_stage_name || "Sem estágio";
      counts.set(label, (counts.get(label) ?? 0) + 1);
    }
    return Array.from(counts, ([label, value]) => ({ label, value }));
  }, [companies.data]);

  const sectorData = useMemo<ChartDatum[]>(
    () =>
      (finance.data?.by_sector ?? [])
        .map((row) => ({ label: row.sector || "Sem setor", value: Number(row.amount || 0) }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 6),
    [finance.data?.by_sector],
  );

  const paymentStatusData = useMemo<ChartDatum[]>(
    () =>
      (finance.data?.status_breakdown ?? []).map((row) => ({
        label: row.status ? String(row.status) : "Sem estado",
        value: Number(row.amount || 0),
        color: statusColor(row.status),
      })),
    [finance.data?.status_breakdown],
  );

  const bookingTrendData = useMemo<ChartDatum[]>(() => {
    const counts = new Map<string, number>();
    for (const booking of bookings.data ?? []) {
      const label = bookingDayLabel(booking.start_time);
      counts.set(label, (counts.get(label) ?? 0) + 1);
    }
    return Array.from(counts, ([label, value]) => ({ label, value })).slice(-8);
  }, [bookings.data]);

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
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Card>
        <Row gutter={[24, 16]} align="middle">
          <Col xs={24} lg={15}>
            <Text type="secondary">Centro operacional</Text>
            <Title level={2} style={{ marginTop: 6, marginBottom: 8 }}>
              Visão geral do ecossistema SDL
            </Title>
            <Text type="secondary">
              Empresas, contratos, reservas, pagamentos e suporte reunidos num painel executivo.
            </Text>
          </Col>
          <Col xs={24} lg={9}>
            <BarList data={paymentStatusData} currency />
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6} style={cardColumnStyle}>
          <Card
            style={fullHeightCardStyle}
            styles={{ body: metricBodyStyle }}
            extra={<Link href="/companies?is_active=true">{tStaff("dashboardViewDetails")}</Link>}
          >
            <Statistic title={tStaff("dashboardKpiCompanies")} value={companies.data?.count ?? 0} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} style={cardColumnStyle}>
          <Card
            style={fullHeightCardStyle}
            styles={{ body: metricBodyStyle }}
            extra={<Link href="/contracts?status=active">{tStaff("dashboardViewDetails")}</Link>}
          >
            <Statistic
              title={tStaff("dashboardKpiContracts")}
              value={contracts.data?.length ?? 0}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} style={cardColumnStyle}>
          <Card
            style={fullHeightCardStyle}
            styles={{ body: metricBodyStyle }}
            extra={<Link href="/bookings?status=Pending">{tStaff("dashboardViewDetails")}</Link>}
          >
            <Statistic title={tStaff("dashboardKpiPendingBookings")} value={pendingBookings} />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} style={cardColumnStyle}>
          <Card
            style={fullHeightCardStyle}
            styles={{ body: metricBodyStyle }}
            extra={<Link href="/tickets?status=Open">{tStaff("dashboardViewDetails")}</Link>}
          >
            <Statistic title={tStaff("dashboardKpiOpenTickets")} value={openTickets} />
          </Card>
        </Col>

        <Col xs={24} lg={8} style={cardColumnStyle}>
          <Card
            title="Maturidade das empresas"
            style={fullHeightCardStyle}
            styles={{ body: chartBodyStyle }}
          >
            <DonutChart data={maturityData} centerLabel="empresas" />
          </Card>
        </Col>
        <Col xs={24} lg={8} style={cardColumnStyle}>
          <Card
            title="Receita por setor"
            style={fullHeightCardStyle}
            styles={{ body: chartBodyStyle }}
          >
            <BarList data={sectorData} currency />
          </Card>
        </Col>
        <Col xs={24} lg={8} style={cardColumnStyle}>
          <Card
            title="Reservas por dia"
            style={fullHeightCardStyle}
            styles={{ body: chartBodyStyle }}
          >
            <TrendBars data={bookingTrendData} />
          </Card>
        </Col>

        <Col xs={24} lg={16} style={cardColumnStyle}>
          <Card
            style={fullHeightCardStyle}
            styles={{ body: summaryBodyStyle }}
            title={tStaff("dashboardFinanceSummary")}
            extra={<Link href="/finance?status=overdue">{tStaff("dashboardOpenReport")}</Link>}
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
        <Col xs={24} lg={8} style={cardColumnStyle}>
          <Card
            title={tStaff("dashboardOpsFocus")}
            style={fullHeightCardStyle}
            styles={{ body: summaryBodyStyle }}
          >
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
                <Button size="small" href="/bookings?status=Pending">
                  {tStaff("dashboardBookingDrillthrough")}
                </Button>
                <Button size="small" href="/inventory?focus=assignments">
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
                scroll={{ x: 800 }}
                size="middle"
              />
            )}
          </Card>
        </Col>
      </Row>
    </Space>
  );
}
