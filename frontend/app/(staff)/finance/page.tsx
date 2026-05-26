"use client";

import {
  Button,
  Card,
  Col,
  Descriptions,
  Popconfirm,
  Result,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import type { CSSProperties } from "react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import { BarList, DonutChart, TrendBars, type ChartDatum } from "@/components/visual/InsightCharts";
import type {
  FinanceReportFilters,
  FinanceReportGroupBy,
  FinanceReportRow,
  FinanceReportType,
  Payment,
  PaymentListFilters,
  PaymentSource,
  PaymentStatus,
  PaymentType,
} from "@/lib/api/finance";
import {
  useCompanies,
  useFinanceDashboard,
  useFinanceReport,
  useNextDuePayment,
  usePaymentActions,
  usePayments,
} from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";

const { Text, Title } = Typography;

const cardColumnStyle: CSSProperties = { display: "flex" };
const fullHeightCardStyle: CSSProperties = { width: "100%", height: "100%" };
const metricBodyStyle: CSSProperties = { minHeight: 92 };
const chartBodyStyle: CSSProperties = {
  minHeight: 232,
  display: "flex",
  alignItems: "center",
};

const statusOptions: Array<{ value: PaymentStatus; label: string }> = [
  { value: "pending", label: "Pendente" },
  { value: "paid", label: "Pago" },
  { value: "overdue", label: "Em atraso" },
];

const sourceOptions: Array<{ value: PaymentSource; label: string }> = [
  { value: "contract", label: tStaff("financeSourceContract") },
  { value: "booking", label: tStaff("financeSourceBooking") },
];

const paymentTypeOptions: Array<{ value: PaymentType; label: string }> = [
  { value: "monthly", label: tStaff("financeTypeMonthly") },
  { value: "rental", label: tStaff("financeTypeRental") },
];

const reportTypeOptions: Array<{ value: FinanceReportType; label: string }> = [
  { value: "revenue_by_company", label: tStaff("financeReportRevenueByCompany") },
  { value: "revenue_by_maturity", label: tStaff("financeReportRevenueByMaturity") },
  { value: "payment_status_summary", label: tStaff("financeReportPaymentStatusSummary") },
  { value: "cash_flow_trend", label: tStaff("financeReportCashFlowTrend") },
];

function renderSource(source: string) {
  if (source === "contract") return tStaff("financeSourceContract");
  if (source === "booking") return tStaff("financeSourceBooking");
  return source;
}

function renderPaymentType(paymentType: string) {
  if (paymentType === "monthly") return tStaff("financeTypeMonthly");
  if (paymentType === "rental") return tStaff("financeTypeRental");
  return paymentType;
}

function paymentStatusLabel(status: string | undefined): string {
  return statusOptions.find((option) => option.value === status)?.label ?? status ?? "Sem estado";
}

function paymentStatusColor(status: string | undefined): string | undefined {
  if (status === "paid") return "#22c55e";
  if (status === "pending") return "#f59e0b";
  if (status === "overdue") return "#fb7185";
  return undefined;
}

function reportRowKey(row: FinanceReportRow, index?: number): string {
  return [row.company_id, row.status, row.period, row.maturity_stage, index ?? 0]
    .filter((value) => value !== null && value !== undefined && value !== "")
    .join(":");
}

function formatReportValue(value: FinanceReportRow[string]) {
  if (value === null || value === undefined || value === "") return "—";
  if (typeof value === "number") return value;
  return String(value);
}

function isAmountColumn(key: string) {
  return key.includes("amount") || key === "collected_amount" || key === "total_revenue";
}

function reportColumnTitle(key: string): string {
  const labels: Record<string, string> = {
    period: tStaff("columnPeriodReport"),
    company_id: tStaff("columnCompany"),
    company_name: tStaff("columnCompany"),
    maturity_stage: "Maturidade",
    status: tStaff("columnStatus"),
    count: "Pagamentos",
    amount: tStaff("columnAmount"),
    total_amount: tStaff("financeTotalAmount"),
    collected_amount: "Receita cobrada",
    total_revenue: "Receita total",
  };
  return labels[key] ?? key.replaceAll("_", " ");
}

function firstNumber(row: FinanceReportRow, keys: string[]): number {
  for (const key of keys) {
    const value = Number(row[key] ?? 0);
    if (Number.isFinite(value) && value > 0) return value;
  }
  return 0;
}

export default function FinancePage() {
  const [paymentFilters, setPaymentFilters] = useState<PaymentListFilters>({});
  const [reportFilters, setReportFilters] = useState<FinanceReportFilters>({
    type: "revenue_by_company",
    group_by: "month",
  });

  useEffect(() => {
    const status = new URLSearchParams(window.location.search).get(
      "status",
    ) as PaymentStatus | null;
    if (status && statusOptions.some((option) => option.value === status)) {
      setPaymentFilters((current) => ({ ...current, status }));
    }
  }, []);

  const companies = useCompanies({ page_size: 200, is_active: true });
  const dashboard = useFinanceDashboard();
  const payments = usePayments(paymentFilters);
  const report = useFinanceReport(reportFilters);
  const cashFlow = useFinanceReport({ type: "cash_flow_trend", group_by: "month" });
  const nextDue = useNextDuePayment();
  const paymentActions = usePaymentActions();

  const companyNames = useMemo(
    () => new Map((companies.data?.results ?? []).map((company) => [company.id, company.name])),
    [companies.data],
  );

  const renderCompanyName = useCallback(
    (companyId: string | null | undefined) => {
      if (!companyId) return "—";
      return companyNames.get(companyId) ?? companyId;
    },
    [companyNames],
  );

  const statusChartData = useMemo<ChartDatum[]>(
    () =>
      (dashboard.data?.status_breakdown ?? []).map((row) => ({
        label: paymentStatusLabel(row.status),
        value: Number(row.amount || 0),
        color: paymentStatusColor(row.status),
      })),
    [dashboard.data?.status_breakdown],
  );

  const sectorChartData = useMemo<ChartDatum[]>(
    () =>
      (dashboard.data?.by_sector ?? [])
        .map((row) => ({ label: row.sector || "Sem setor", value: Number(row.amount || 0) }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 6),
    [dashboard.data?.by_sector],
  );

  const sourceChartData = useMemo<ChartDatum[]>(
    () =>
      (dashboard.data?.source_breakdown ?? []).map((row) => ({
        label: row.source ? renderSource(row.source) : "Sem origem",
        value: Number(row.amount || 0),
      })),
    [dashboard.data?.source_breakdown],
  );

  const cashFlowData = useMemo<ChartDatum[]>(
    () =>
      (cashFlow.data?.results ?? []).map((row) => ({
        label: String(row.period ?? "—"),
        value: firstNumber(row, ["collected_amount", "amount", "total_amount", "total_revenue"]),
      })),
    [cashFlow.data?.results],
  );

  const columns: ColumnsType<Payment> = [
    {
      title: tStaff("columnCompany"),
      dataIndex: "company_id",
      key: "company_id",
      width: 220,
      ellipsis: true,
      render: renderCompanyName,
    },
    {
      title: tStaff("columnAmount"),
      dataIndex: "amount",
      key: "amount",
      width: 120,
      align: "right",
      render: formatCurrency,
    },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", width: 120, render: statusTag },
    { title: tStaff("columnSource"), dataIndex: "source", key: "source", width: 110, render: renderSource },
    {
      title: tStaff("columnPaymentType"),
      dataIndex: "payment_type",
      key: "payment_type",
      width: 110,
      render: renderPaymentType,
    },
    {
      title: tStaff("columnDueDate"),
      dataIndex: "due_date",
      key: "due_date",
      width: 125,
      render: formatDate,
    },
    {
      title: tStaff("columnActions"),
      key: "actions",
      width: 128,
      align: "right",
      render: (_: unknown, row) => (
        <Popconfirm
          title="Marcar pagamento como pago?"
          okText="Marcar pago"
          cancelText="Cancelar"
          onConfirm={() =>
            paymentActions.update.mutate({
              id: row.id,
              payload: { status: "paid", paid_at: new Date().toISOString() },
            })
          }
        >
          <Button
            size="small"
            type="primary"
            disabled={row.status === "paid"}
            loading={
              paymentActions.update.isPending && paymentActions.update.variables?.id === row.id
            }
          >
            {tStaff("financeMarkPaid")}
          </Button>
        </Popconfirm>
      ),
    },
  ];

  const reportColumns = useMemo<ColumnsType<FinanceReportRow>>(() => {
    const rows = report.data?.results ?? [];
    const keys = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
    return keys.map((key) => ({
      title: reportColumnTitle(key),
      dataIndex: key,
      key,
      ellipsis: true,
      render: (value: FinanceReportRow[string]) => {
        if (key === "company_id") return renderCompanyName(String(value ?? ""));
        if (isAmountColumn(key)) return formatCurrency(value as string | number | null | undefined);
        if (key === "status") return statusTag(String(value ?? ""));
        return formatReportValue(value);
      },
    }));
  }, [report.data?.results, renderCompanyName]);

  if (
    companies.isLoading ||
    dashboard.isLoading ||
    payments.isLoading ||
    report.isLoading ||
    cashFlow.isLoading ||
    nextDue.isLoading
  ) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (
    companies.isError ||
    dashboard.isError ||
    payments.isError ||
    report.isError ||
    cashFlow.isError ||
    nextDue.isError
  ) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Card>
        <Row gutter={[24, 16]} align="middle">
          <Col xs={24} lg={15}>
            <Text type="secondary">Financeiro</Text>
            <Title level={2} style={{ marginTop: 6, marginBottom: 8 }}>
              Receita, cobranças e risco de atraso
            </Title>
            <Text type="secondary">
              Acompanhe pagamentos por estado, origem, setor e evolução mensal sem expor IDs técnicos.
            </Text>
          </Col>
          <Col xs={24} lg={9}>
            <DonutChart data={statusChartData} centerLabel="receita" />
          </Col>
        </Row>
      </Card>

      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6} style={cardColumnStyle}>
          <Card style={fullHeightCardStyle} styles={{ body: metricBodyStyle }}>
            <Statistic
              title={tStaff("financeTotalAmount")}
              value={Number(dashboard.data?.total_amount ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} style={cardColumnStyle}>
          <Card style={fullHeightCardStyle} styles={{ body: metricBodyStyle }}>
            <Statistic
              title={tStaff("financePaidAmount")}
              value={Number(dashboard.data?.paid_amount ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} style={cardColumnStyle}>
          <Card style={fullHeightCardStyle} styles={{ body: metricBodyStyle }}>
            <Statistic
              title={tStaff("financePendingAmount")}
              value={Number(dashboard.data?.pending_amount ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6} style={cardColumnStyle}>
          <Card style={fullHeightCardStyle} styles={{ body: metricBodyStyle }}>
            <Statistic
              title={tStaff("financeOverdueAmount")}
              value={Number(dashboard.data?.overdue_amount ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={[16, 16]}>
        <Col xs={24} lg={8} style={cardColumnStyle}>
          <Card title="Receita por setor" style={fullHeightCardStyle} styles={{ body: chartBodyStyle }}>
            <BarList data={sectorChartData} currency />
          </Card>
        </Col>
        <Col xs={24} lg={8} style={cardColumnStyle}>
          <Card title="Receita por origem" style={fullHeightCardStyle} styles={{ body: chartBodyStyle }}>
            <DonutChart data={sourceChartData} centerLabel="origens" />
          </Card>
        </Col>
        <Col xs={24} lg={8} style={cardColumnStyle}>
          <Card title="Fluxo mensal" style={fullHeightCardStyle} styles={{ body: chartBodyStyle }}>
            <TrendBars data={cashFlowData} currency />
          </Card>
        </Col>
      </Row>

      <Card title={tStaff("financeNextDueTitle")}>
        {nextDue.data?.payment_id ? (
          <Descriptions size="small" column={{ xs: 1, md: 3 }} bordered>
            <Descriptions.Item label={tStaff("columnCompany")}>
              {renderCompanyName(nextDue.data.company_id)}
            </Descriptions.Item>
            <Descriptions.Item label={tStaff("columnAmount")}>
              {formatCurrency(nextDue.data.amount)}
            </Descriptions.Item>
            <Descriptions.Item label={tStaff("columnDueDate")}>
              {formatDate(nextDue.data.due_date)}
            </Descriptions.Item>
            <Descriptions.Item label={tStaff("columnStatus")}>
              {statusTag(nextDue.data.status)}
            </Descriptions.Item>
            <Descriptions.Item label={tStaff("columnSource")}>
              {renderSource(nextDue.data.source)}
            </Descriptions.Item>
            <Descriptions.Item label={tStaff("columnPaymentType")}>
              {renderPaymentType(nextDue.data.payment_type)}
            </Descriptions.Item>
          </Descriptions>
        ) : (
          <Text type="secondary">{tStaff("financeNoNextDue")}</Text>
        )}
      </Card>

      <Card title={tStaff("financeFiltersTitle")}>
        <Space wrap>
          <Select<PaymentStatus>
            allowClear
            placeholder={tStaff("financeFilterStatus")}
            style={{ minWidth: 180 }}
            value={paymentFilters.status}
            options={statusOptions}
            onChange={(status) => setPaymentFilters((current) => ({ ...current, status }))}
          />
          <Select<PaymentSource>
            allowClear
            placeholder={tStaff("financeFilterSource")}
            style={{ minWidth: 180 }}
            value={paymentFilters.source}
            options={sourceOptions}
            onChange={(source) => setPaymentFilters((current) => ({ ...current, source }))}
          />
          <Select<PaymentType>
            allowClear
            placeholder={tStaff("financeFilterPaymentType")}
            style={{ minWidth: 180 }}
            value={paymentFilters.payment_type}
            options={paymentTypeOptions}
            onChange={(payment_type) =>
              setPaymentFilters((current) => ({ ...current, payment_type }))
            }
          />
        </Space>
      </Card>

      <Card title={tStaff("navFinance")}>
        <Table<Payment>
          rowKey="id"
          columns={columns}
          dataSource={payments.data ?? []}
          locale={{ emptyText: tStaff("emptyData") }}
          pagination={{ pageSize: 8, hideOnSinglePage: true }}
          scroll={{ x: 980 }}
          size="middle"
          expandable={{
            columnTitle: "Detalhes",
            columnWidth: 76,
            expandedRowRender: (row) => (
              <Descriptions size="small" column={1} bordered>
                <Descriptions.Item label={tStaff("columnPeriod")}>
                  {formatDate(row.period_start)} — {formatDate(row.period_end)}
                </Descriptions.Item>
                <Descriptions.Item label={tStaff("columnReference")}>
                  {row.reference_id || "—"}
                </Descriptions.Item>
                <Descriptions.Item label="Contrato">{row.contract_id ?? "—"}</Descriptions.Item>
                <Descriptions.Item label="Reserva">{row.booking_id ?? "—"}</Descriptions.Item>
              </Descriptions>
            ),
          }}
        />
      </Card>

      <Card title={tStaff("financeReportsTitle")}>
        <Space direction="vertical" size="middle" style={{ width: "100%" }}>
          <Space wrap>
            <Select<FinanceReportType>
              value={reportFilters.type}
              style={{ minWidth: 260 }}
              options={reportTypeOptions}
              onChange={(type) => setReportFilters((current) => ({ ...current, type }))}
            />
            <Select<FinanceReportGroupBy>
              value={reportFilters.group_by}
              style={{ minWidth: 160 }}
              disabled={reportFilters.type !== "cash_flow_trend"}
              options={[
                { value: "month", label: tStaff("financeGroupByMonth") },
                { value: "day", label: tStaff("financeGroupByDay") },
              ]}
              onChange={(group_by) => setReportFilters((current) => ({ ...current, group_by }))}
            />
          </Space>
          <Table<FinanceReportRow>
            rowKey={reportRowKey}
            columns={reportColumns}
            dataSource={report.data?.results ?? []}
            locale={{ emptyText: tStaff("emptyData") }}
            pagination={false}
            scroll={{ x: 1000 }}
            size="middle"
          />
        </Space>
      </Card>
    </Space>
  );
}
