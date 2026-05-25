"use client";

import { Card, Result, Spin, Table } from "antd";
import type { ColumnsType } from "antd/es/table";

import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import { useAuth } from "@/components/auth/AuthProvider";
import { useCompanyPayments } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";
import type { Payment } from "@/lib/api/finance";

export default function ClientPaymentsPage() {
  const { user, isReady } = useAuth();
  const companyId = user?.companyId ?? null;
  const { data, isLoading, isError } = useCompanyPayments(companyId);
  const columns: ColumnsType<Payment> = [
    { title: tClient("columnAmount"), dataIndex: "amount", key: "amount", render: formatCurrency },
    { title: tClient("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    { title: tClient("columnDueDate"), dataIndex: "due_date", key: "due_date", render: formatDate },
    { title: tClient("columnUpdatedAt"), dataIndex: "updated_at", key: "updated_at", render: formatDate },
  ];

  if (!isReady || isLoading) return <Spin size="large" tip={tClient("pageLoading")} />;
  if (!companyId) return <Result status="warning" title={tClient("pageNoCompany")} subTitle={tClient("pageNoCompanyAction")} />;
  if (isError) return <Result status="error" title={tClient("clientLoadError")} />;

  return (
    <Card title={tClient("pagePaymentsTitle")}>
      <Table<Payment> rowKey="id" columns={columns} dataSource={data ?? []} locale={{ emptyText: tClient("paymentsEmpty") }} />
    </Card>
  );
}
