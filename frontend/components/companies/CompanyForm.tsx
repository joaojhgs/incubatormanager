"use client";

import { useEffect, useMemo } from "react";

import { Button, Col, Form, Input, Row, Select, Space } from "antd";
import Link from "next/link";

import type { CompanyCreatePayload, CompanyUpdatePayload } from "@/lib/api/companies";
import { useCAECodes, useMaturityStages } from "@/lib/hooks";
import { tCompany } from "@/lib/i18n/companies";

export type CompanyFormValues = CompanyCreatePayload & CompanyUpdatePayload;

interface CompanyFormProps {
  initialValues?: Partial<CompanyFormValues>;
  onSubmit: (values: CompanyFormValues) => Promise<void> | void;
  submitLabel: string;
  submitting?: boolean;
}

export function CompanyForm({
  initialValues,
  onSubmit,
  submitLabel,
  submitting,
}: CompanyFormProps) {
  const [form] = Form.useForm<CompanyFormValues>();
  const caeQuery = useCAECodes();
  const maturityQuery = useMaturityStages();

  useEffect(() => {
    if (initialValues) form.setFieldsValue(initialValues);
  }, [form, initialValues]);

  const caeOptions = useMemo(
    () =>
      (caeQuery.data ?? []).map((cae) => ({
        value: cae.id,
        label: `${cae.code} — ${cae.description}`,
      })),
    [caeQuery.data],
  );

  const maturityOptions = useMemo(
    () =>
      (maturityQuery.data ?? []).map((stage) => ({
        value: stage.id,
        label: stage.name,
      })),
    [maturityQuery.data],
  );

  return (
    <Form<CompanyFormValues>
      form={form}
      layout="vertical"
      onFinish={(values) => void onSubmit(values)}
      requiredMark="optional"
      scrollToFirstError
    >
      <Row gutter={[16, 0]}>
        <Col xs={24} md={12}>
          <Form.Item
            name="name"
            label={tCompany("formFieldName")}
            rules={[{ required: true, message: tCompany("formFieldNameRequired") }]}
          >
            <Input autoComplete="organization" />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item
            name="tax_id"
            label={tCompany("formFieldTaxId")}
            rules={[{ required: true, message: tCompany("formFieldTaxIdRequired") }]}
          >
            <Input />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 0]}>
        <Col xs={24} md={12}>
          <Form.Item
            name="legal_representative"
            label={tCompany("formFieldLegalRepresentative")}
            rules={[{ required: true, message: tCompany("formFieldLegalRepresentativeRequired") }]}
          >
            <Input autoComplete="name" />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item
            name="email"
            label={tCompany("formFieldEmail")}
            rules={[{ type: "email", message: tCompany("formFieldEmailInvalid") }]}
          >
            <Input autoComplete="email" inputMode="email" />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 0]}>
        <Col xs={24} md={12}>
          <Form.Item
            name="cae_id"
            label={tCompany("formFieldCae")}
            rules={[{ required: true, message: tCompany("formFieldCaeRequired") }]}
          >
            <Select
              loading={caeQuery.isLoading}
              options={caeOptions}
              placeholder={tCompany("formFieldCaePlaceholder")}
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item
            name="maturity_stage_id"
            label={tCompany("formFieldMaturityStage")}
            rules={[{ required: true, message: tCompany("formFieldMaturityStageRequired") }]}
          >
            <Select
              loading={maturityQuery.isLoading}
              options={maturityOptions}
              placeholder={tCompany("formFieldMaturityStagePlaceholder")}
              showSearch
              optionFilterProp="label"
            />
          </Form.Item>
        </Col>
      </Row>

      <Row gutter={[16, 0]}>
        <Col xs={24} md={12}>
          <Form.Item name="phone" label={tCompany("formFieldPhone")}>
            <Input autoComplete="tel" />
          </Form.Item>
        </Col>
        <Col xs={24} md={12}>
          <Form.Item name="address" label={tCompany("formFieldAddress")}>
            <Input autoComplete="street-address" />
          </Form.Item>
        </Col>
      </Row>

      <Form.Item name="description" label={tCompany("formFieldDescription")}>
        <Input.TextArea rows={4} />
      </Form.Item>

      <Form.Item>
        <Space wrap>
          <Button type="primary" htmlType="submit" loading={submitting}>
            {submitLabel}
          </Button>
          <Link href="/companies" prefetch={false}>
            <Button>{tCompany("formCancel")}</Button>
          </Link>
        </Space>
      </Form.Item>
    </Form>
  );
}
