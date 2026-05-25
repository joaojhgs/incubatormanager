"use client";

import {
  Button,
  Card,
  Col,
  Descriptions,
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
import { useMemo, useState } from "react";

import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import {
  useFinanceDashboard,
  useFinanceReport,
  useNextDuePayment,
  usePaymentActions,
  usePayments,
} from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
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

const { Text } = Typography;

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
  return key.includes("amount") || key === "collected_amount";
}

export default function FinancePage() {
  const [paymentFilters, setPaymentFilters] = useState<PaymentListFilters>({});
  const [reportFilters, setReportFilters] = useState<FinanceReportFilters>({
    type: "revenue_by_company",
    group_by: "month",
  });

  const dashboard = useFinanceDashboard();
  const payments = usePayments(paymentFilters);
  const report = useFinanceReport(reportFilters);
  const nextDue = useNextDuePayment();
  const paymentActions = usePaymentActions();

  const columns: ColumnsType<Payment> = [
    { title: tStaff("columnCompany"), dataIndex: "company_id", key: "company_id", width: 220 },
    { title: tStaff("columnAmount"), dataIndex: "amount", key: "amount", render: formatCurrency },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    { title: tStaff("columnSource"), dataIndex: "source", key: "source", render: renderSource },
    {
      title: tStaff("columnPaymentType"),
      dataIndex: "payment_type",
      key: "payment_type",
      render: renderPaymentType,
    },
    { title: tStaff("columnDueDate"), dataIndex: "due_date", key: "due_date", render: formatDate },
    {
      title: tStaff("columnReference"),
      dataIndex: "reference_id",
      key: "reference_id",
      render: (value: string) => value || "—",
    },
    {
      title: tStaff("columnActions"),
      key: "actions",
      fixed: "right",
      render: (_: unknown, row) => (
        <Button
          size="small"
          type="primary"
          disabled={row.status === "paid"}
          loading={
            paymentActions.update.isPending && paymentActions.update.variables?.id === row.id
          }
          onClick={() =>
            paymentActions.update.mutate({
              id: row.id,
              payload: { status: "paid", paid_at: new Date().toISOString() },
            })
          }
        >
          {tStaff("financeMarkPaid")}
        </Button>
      ),
    },
  ];

  const reportColumns = useMemo<ColumnsType<FinanceReportRow>>(() => {
    const rows = report.data?.results ?? [];
    const keys = Array.from(new Set(rows.flatMap((row) => Object.keys(row))));
    return keys.map((key) => ({
      title: key === "period" ? tStaff("columnPeriodReport") : key,
      dataIndex: key,
      key,
      render: (value: FinanceReportRow[string]) =>
        isAmountColumn(key)
          ? formatCurrency(value as string | number | null | undefined)
          : formatReportValue(value),
    }));
  }, [report.data?.results]);

  if (dashboard.isLoading || payments.isLoading || report.isLoading || nextDue.isLoading) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }
  if (dashboard.isError || payments.isError || report.isError || nextDue.isError) {
    return <Result status="error" title={tStaff("loadError")} />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Row gutter={[16, 16]}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={tStaff("financeTotalAmount")}
              value={Number(dashboard.data?.total_amount ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={tStaff("financePaidAmount")}
              value={Number(dashboard.data?.paid_amount ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={tStaff("financePendingAmount")}
              value={Number(dashboard.data?.pending_amount ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title={tStaff("financeOverdueAmount")}
              value={Number(dashboard.data?.overdue_amount ?? 0)}
              prefix="€"
              precision={2}
            />
          </Card>
        </Col>
      </Row>

      <Card title={tStaff("financeNextDueTitle")}>
        {nextDue.data?.payment_id ? (
          <Descriptions size="small" column={{ xs: 1, md: 3 }} bordered>
            <Descriptions.Item label={tStaff("columnCompany")}>
              {nextDue.data.company_id}
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
          scroll={{ x: 1200 }}
          expandable={{
            expandedRowRender: (row) => (
              <Descriptions size="small" column={1} bordered>
                <Descriptions.Item label={tStaff("columnPeriod")}>
                  {formatDate(row.period_start)} — {formatDate(row.period_end)}
                </Descriptions.Item>
                <Descriptions.Item label="Contract ID">{row.contract_id ?? "—"}</Descriptions.Item>
                <Descriptions.Item label="Booking ID">{row.booking_id ?? "—"}</Descriptions.Item>
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
            size="small"
          />
        </Space>
      </Card>
    </Space>
  );
}
