"use client";

import { ArrowLeftOutlined } from "@ant-design/icons";
import { Button, Card, Flex, Typography } from "antd";
import Link from "next/link";
import { useRouter } from "next/navigation";

import { CompanyForm, type CompanyFormValues } from "@/components/companies";
import { useCreateCompany } from "@/lib/hooks";
import { tCompany } from "@/lib/i18n/companies";

export default function NewCompanyPage() {
  const router = useRouter();
  const createCompany = useCreateCompany();

  async function handleSubmit(values: CompanyFormValues) {
    const company = await createCompany.mutateAsync(values);
    router.push(`/companies/${company.id}`);
  }

  return (
    <Flex vertical gap={16}>
      <Link href="/companies" prefetch={false}>
        <Button icon={<ArrowLeftOutlined aria-hidden />} type="link" style={{ paddingLeft: 0 }}>
          {tCompany("formBackToList")}
        </Button>
      </Link>
      <Typography.Title level={3} style={{ margin: 0 }}>
        {tCompany("formCreateTitle")}
      </Typography.Title>
      <Card>
        <CompanyForm
          onSubmit={handleSubmit}
          submitLabel={tCompany("formCreateSubmit")}
          submitting={createCompany.isPending}
        />
      </Card>
    </Flex>
  );
}
