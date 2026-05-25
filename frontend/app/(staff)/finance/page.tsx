"use client";

import { Card, Col, Result, Row, Spin, Statistic, Table } from "antd";
import type { ColumnsType } from "antd/es/table";

import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import { useFinanceDashboard, usePayments } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Payment } from "@/lib/api/finance";

export default function FinancePage() {
  const dashboard = useFinanceDashboard();
  const payments = usePayments();

  const columns: ColumnsType<Payment> = [
    { title: tStaff("columnCompany"), dataIndex: "company_id", key: "company_id" },
    { title: tStaff("columnAmount"), dataIndex: "amount", key: "amount", render: formatCurrency },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    { title: tStaff("columnDueDate"), dataIndex: "due_date", key: "due_date", render: formatDate },
  ];

  if (dashboard.isLoading || payments.isLoading) return <Spin size="large" tip={tStaff("pageLoading")} />;
  if (dashboard.isError || payments.isError) return <Result status="error" title={tStaff("loadError")} />;

  return (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card><Statistic title={tStaff("financeTotalAmount")} value={Number(dashboard.data?.total_amount ?? 0)} prefix="€" precision={2} /></Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card><Statistic title={tStaff("financePaidAmount")} value={Number(dashboard.data?.paid_amount ?? 0)} prefix="€" precision={2} /></Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card><Statistic title={tStaff("financePendingAmount")} value={Number(dashboard.data?.pending_amount ?? 0)} prefix="€" precision={2} /></Card>
      </Col>
      <Col xs={24} sm={12} lg={6}>
        <Card><Statistic title={tStaff("financeOverdueAmount")} value={Number(dashboard.data?.overdue_amount ?? 0)} prefix="€" precision={2} /></Card>
      </Col>
      <Col span={24}>
        <Card title={tStaff("navFinance")}>
          <Table<Payment> rowKey="id" columns={columns} dataSource={payments.data ?? []} locale={{ emptyText: tStaff("emptyData") }} />
        </Card>
      </Col>
    </Row>
  );
}
