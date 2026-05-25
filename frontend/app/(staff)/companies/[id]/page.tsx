"use client";

import { ArrowLeftOutlined, EditOutlined } from "@ant-design/icons";
import {
  Button,
  Card,
  Descriptions,
  Flex,
  Result,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import Link from "next/link";
import { useParams } from "next/navigation";

import { ArchivedBadge, MaturityStageTag } from "@/components/companies";
import { DocumentList } from "@/components/documents";
import type { Employee } from "@/lib/api/companies";
import { useCompany } from "@/lib/hooks";
import { tCompany } from "@/lib/i18n/companies";

function getParamId(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

function formatDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleDateString("pt-PT");
}

export default function CompanyDetailPage() {
  const params = useParams<{ id: string }>();
  const id = getParamId(params.id);
  const { data, isLoading, isError } = useCompany(id);

  const employeeColumns: ColumnsType<Employee> = [
    { title: tCompany("detailEmployeeName"), dataIndex: "name", key: "name" },
    { title: tCompany("detailEmployeeType"), dataIndex: "type", key: "type" },
    {
      title: tCompany("detailEmployeeStart"),
      dataIndex: "start_date",
      key: "start_date",
      render: formatDate,
    },
    {
      title: tCompany("detailEmployeeEnd"),
      dataIndex: "end_date",
      key: "end_date",
      render: formatDate,
    },
    {
      title: tCompany("detailEmployeeStatus"),
      dataIndex: "is_active",
      key: "is_active",
      render: (active: boolean) => (
        <Tag color={active ? "success" : "default"}>
          {active ? tCompany("detailStatusActive") : tCompany("detailStatusInactive")}
        </Tag>
      ),
    },
  ];

  if (isLoading) return <Spin size="large" tip={tCompany("formLoading")} />;
  if (isError || !data) {
    return (
      <Result
        status="404"
        title={tCompany("detailNotFound")}
        extra={
          <Link href="/companies" prefetch={false}>
            <Button type="primary">{tCompany("formBackToList")}</Button>
          </Link>
        }
      />
    );
  }

  return (
    <Flex vertical gap={16}>
      <Flex justify="space-between" align="center" wrap gap="small">
        <Space direction="vertical" size={0}>
          <Link href="/companies" prefetch={false}>
            <Button icon={<ArrowLeftOutlined aria-hidden />} type="link" style={{ paddingLeft: 0 }}>
              {tCompany("formBackToList")}
            </Button>
          </Link>
          <Typography.Title level={3} style={{ margin: 0 }}>
            {data.name} <ArchivedBadge archived={!data.is_active} />
          </Typography.Title>
        </Space>
        <Link href={`/companies/${id}/edit`} prefetch={false}>
          <Button type="primary" icon={<EditOutlined aria-hidden />}>
            {tCompany("listActionEdit")}
          </Button>
        </Link>
      </Flex>

      <Card title={tCompany("detailProfileTitle")}>
        <Descriptions bordered column={{ xs: 1, md: 2 }}>
          <Descriptions.Item label={tCompany("formFieldTaxId")}>{data.tax_id}</Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldLegalRepresentative")}>
            {data.legal_representative}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldCae")}>
            {data.cae_description ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldMaturityStage")}>
            <MaturityStageTag stageName={data.maturity_stage_name ?? ""} />
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldEmail")}>
            {data.email ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldPhone")}>
            {data.phone ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldAddress")} span={2}>
            {data.address ?? "—"}
          </Descriptions.Item>
          <Descriptions.Item label={tCompany("formFieldDescription")} span={2}>
            {data.description ?? "—"}
          </Descriptions.Item>
        </Descriptions>
      </Card>

      <Card title={tCompany("detailEmployeesTitle")}>
        <Table<Employee>
          rowKey="id"
          columns={employeeColumns}
          dataSource={data.employees ?? []}
          locale={{ emptyText: tCompany("detailEmployeesEmpty") }}
          pagination={false}
        />
      </Card>

      <Card title={tCompany("detailDocumentsTitle")}>
        <DocumentList entityType="Company" entityId={id} readOnly />
      </Card>
    </Flex>
  );
}
