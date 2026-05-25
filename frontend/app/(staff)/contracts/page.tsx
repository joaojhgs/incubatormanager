"use client";

import { Card, Result, Spin, Table } from "antd";
import type { ColumnsType } from "antd/es/table";

import { formatCurrency, formatDate, statusTag } from "@/components/operations/format";
import { DocumentList } from "@/components/documents";
import { useContracts } from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Contract } from "@/lib/api/contracts";

export default function ContractsPage() {
  const { data, isLoading, isError } = useContracts();
  const firstContract = data?.[0];
  const columns: ColumnsType<Contract> = [
    { title: tStaff("columnCompany"), dataIndex: "company_id", key: "company_id" },
    { title: tStaff("columnSpace"), dataIndex: "space_id", key: "space_id" },
    { title: tStaff("columnStatus"), dataIndex: "status", key: "status", render: statusTag },
    { title: tStaff("columnPrice"), dataIndex: "monthly_fee", key: "monthly_fee", render: formatCurrency },
    { title: tStaff("columnStart"), dataIndex: "start_date", key: "start_date", render: formatDate },
    { title: tStaff("columnEnd"), dataIndex: "end_date", key: "end_date", render: formatDate },
  ];

  if (isLoading) return <Spin size="large" tip={tStaff("pageLoading")} />;
  if (isError) return <Result status="error" title={tStaff("loadError")} />;

  return (
    <Card title={tStaff("navContracts")}>
      <Table<Contract> rowKey="id" columns={columns} dataSource={data ?? []} locale={{ emptyText: tStaff("emptyData") }} />
      {firstContract ? (
        <Card type="inner" title={tStaff("documentsTitle")} style={{ marginTop: 16 }}>
          <DocumentList entityType="Contract" entityId={firstContract.id} readOnly />
        </Card>
      ) : null}
    </Card>
  );
}
