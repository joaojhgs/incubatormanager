"use client";

import { ArrowLeftOutlined } from "@ant-design/icons";
import { Button, Card, Flex, Result, Spin, Typography } from "antd";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";

import { CompanyForm, type CompanyFormValues } from "@/components/companies";
import { useCompany, useUpdateCompany } from "@/lib/hooks";
import { tCompany } from "@/lib/i18n/companies";

function getParamId(value: string | string[] | undefined): string {
  return Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
}

export default function EditCompanyPage() {
  const params = useParams<{ id: string }>();
  const id = getParamId(params.id);
  const router = useRouter();
  const company = useCompany(id);
  const updateCompany = useUpdateCompany();

  async function handleSubmit(values: CompanyFormValues) {
    await updateCompany.mutateAsync({ id, payload: values });
    router.push(`/companies/${id}`);
  }

  if (company.isLoading) return <Spin size="large" tip={tCompany("formLoading")} />;
  if (company.isError || !company.data) {
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
      <Link href={`/companies/${id}`} prefetch={false}>
        <Button icon={<ArrowLeftOutlined aria-hidden />} type="link" style={{ paddingLeft: 0 }}>
          {tCompany("detailBack")}
        </Button>
      </Link>
      <Typography.Title level={3} style={{ margin: 0 }}>
        {tCompany("formEditTitle")}
      </Typography.Title>
      <Card>
        <CompanyForm
          initialValues={{
            name: company.data.name,
            tax_id: company.data.tax_id,
            legal_representative: company.data.legal_representative,
            email: company.data.email ?? undefined,
            phone: company.data.phone ?? undefined,
            address: company.data.address ?? undefined,
            description: company.data.description ?? undefined,
            cae_id: company.data.cae_id,
            maturity_stage_id: company.data.maturity_stage_id,
          }}
          onSubmit={handleSubmit}
          submitLabel={tCompany("formUpdateSubmit")}
          submitting={updateCompany.isPending}
        />
      </Card>
    </Flex>
  );
}
