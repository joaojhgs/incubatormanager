"use client";

import { ArrowLeftOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import {
  Button,
  Card,
  Col,
  Flex,
  Form,
  Input,
  Progress,
  Result,
  Row,
  Select,
  Space,
  Spin,
  Typography,
  message,
} from "antd";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { listCompanies } from "@/lib/api/companies";
import type { UserCreatePayload, UserCreateRole } from "@/lib/api/users";
import { isDirectorRole } from "@/lib/auth/constants";
import { useCreateUser } from "@/lib/hooks/useCreateUser";
import { tUsers } from "@/lib/i18n/users";

const { Title } = Typography;

type CreateUserFormValues = {
  first_name: string;
  last_name: string;
  email: string;
  role: UserCreateRole;
  company_id?: string;
  password: string;
  confirm_password: string;
};

function passwordStrengthPercent(pw: string): number {
  if (!pw) return 0;
  let n = 0;
  if (pw.length >= 8) n += 25;
  if (pw.length >= 12) n += 10;
  if (/[a-z]/.test(pw)) n += 15;
  if (/[A-Z]/.test(pw)) n += 15;
  if (/[0-9]/.test(pw)) n += 15;
  if (/[^A-Za-z0-9]/.test(pw)) n += 20;
  return Math.min(100, n);
}

function passwordStrengthStroke(pw: string): string {
  const p = passwordStrengthPercent(pw);
  if (p >= 70) return "#52c41a";
  if (p >= 40) return "#faad14";
  return "#ff4d4f";
}

function extractErrorMessage(err: unknown): string {
  if (err && typeof err === "object" && "response" in err) {
    const res = (err as { response?: { data?: unknown } }).response;
    const data = res?.data;
    if (data && typeof data === "object") {
      if ("detail" in data) {
        const d = (data as { detail: unknown }).detail;
        if (typeof d === "string" && d.trim()) return d;
        if (Array.isArray(d) && d.length > 0 && typeof d[0] === "string") return d[0];
      }
      const firstKey = Object.keys(data as object).find((k) => k !== "detail");
      if (firstKey) {
        const v = (data as Record<string, unknown>)[firstKey];
        if (typeof v === "string" && v.trim()) return v;
        if (Array.isArray(v) && typeof v[0] === "string") return v[0];
      }
    }
  }
  return "";
}

export default function CreateUserPage() {
  const router = useRouter();
  const [form] = Form.useForm<CreateUserFormValues>();
  const role = Form.useWatch("role", form);
  const passwordWatch = Form.useWatch("password", form) ?? "";
  const { user, isReady } = useAuth();
  const director = Boolean(isReady && user && isDirectorRole(user.role));
  const createUserMutation = useCreateUser();

  const companiesQuery = useQuery({
    queryKey: ["companies", "user-create-picker"],
    queryFn: () => listCompanies({ page_size: 100, is_active: true }),
    enabled: director && role === "Client",
    staleTime: 60_000,
    retry: 1,
  });

  useEffect(() => {
    if (companiesQuery.isError) {
      message.error(tUsers("createCompaniesLoadError"));
    }
  }, [companiesQuery.isError]);

  const companyOptions = useMemo(
    () =>
      (companiesQuery.data?.results ?? []).map((c) => ({
        value: c.id,
        label: c.name,
      })),
    [companiesQuery.data?.results],
  );

  const roleOptions = useMemo(
    () => [
      { value: "Director" as const, label: tUsers("createFieldRoleDirector") },
      { value: "Staff" as const, label: tUsers("createFieldRoleStaff") },
      { value: "Client" as const, label: tUsers("createFieldRoleClient") },
    ],
    [],
  );

  const onFinish = async (values: CreateUserFormValues) => {
    const payload: UserCreatePayload = {
      email: values.email.trim(),
      first_name: values.first_name.trim(),
      last_name: values.last_name.trim(),
      password: values.password,
      role: values.role,
    };
    if (values.role === "Client") {
      payload.company_id = values.company_id;
    }
    try {
      await createUserMutation.mutateAsync(payload);
      message.success(tUsers("createSuccess"));
      router.push("/users");
    } catch (err) {
      const detail = extractErrorMessage(err);
      message.error(detail || tUsers("createErrorGeneric"));
    }
  };

  if (!isReady) {
    return (
      <Flex align="center" justify="center">
        <Spin size="large" />
      </Flex>
    );
  }

  if (!director) {
    return (
      <Result
        status="403"
        title={tUsers("listForbiddenTitle")}
        subTitle={tUsers("listForbiddenDescription")}
        extra={
          <Link href="/dashboard" prefetch={false}>
            <Button type="primary">{tUsers("listForbiddenBack")}</Button>
          </Link>
        }
      />
    );
  }

  return (
    <Flex vertical gap="large">
      <Flex justify="space-between" align="center" wrap gap="small">
        <Title level={3} style={{ margin: 0 }}>
          {tUsers("createTitle")}
        </Title>
        <Link href="/users" prefetch={false}>
          <Button type="default" icon={<ArrowLeftOutlined aria-hidden />}>
            {tUsers("createBackToList")}
          </Button>
        </Link>
      </Flex>

      <Card>
        <Form<CreateUserFormValues>
          form={form}
          layout="vertical"
          onFinish={onFinish}
          requiredMark="optional"
          validateTrigger="onBlur"
          initialValues={{ role: "Staff" }}
        >
          <Row gutter={[16, 0]}>
            <Col xs={24} md={12}>
              <Form.Item
                name="first_name"
                label={tUsers("createFieldFirstName")}
                rules={[{ required: true, message: tUsers("createFieldFirstNameRequired") }]}
              >
                <Input autoComplete="given-name" />
              </Form.Item>
            </Col>
            <Col xs={24} md={12}>
              <Form.Item
                name="last_name"
                label={tUsers("createFieldLastName")}
                rules={[{ required: true, message: tUsers("createFieldLastNameRequired") }]}
              >
                <Input autoComplete="family-name" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="email"
            label={tUsers("createFieldEmail")}
            rules={[
              { required: true, message: tUsers("createFieldEmailRequired") },
              { type: "email", message: tUsers("createFieldEmailInvalid") },
            ]}
          >
            <Input autoComplete="email" inputMode="email" />
          </Form.Item>

          <Form.Item
            name="role"
            label={tUsers("createFieldRole")}
            rules={[{ required: true, message: tUsers("createFieldRoleRequired") }]}
          >
            <Select
              options={roleOptions}
              onChange={(next) => {
                if (next !== "Client") {
                  form.setFieldValue("company_id", undefined);
                }
              }}
            />
          </Form.Item>

          {role === "Client" ? (
            <Form.Item
              name="company_id"
              label={tUsers("createFieldCompany")}
              rules={[{ required: true, message: tUsers("createFieldCompanyRequired") }]}
            >
              <Select
                showSearch
                optionFilterProp="label"
                placeholder={tUsers("createFieldCompanyPlaceholder")}
                loading={companiesQuery.isLoading}
                options={companyOptions}
              />
            </Form.Item>
          ) : null}

          <Form.Item
            name="password"
            label={tUsers("createFieldPassword")}
            rules={[
              { required: true, message: tUsers("createFieldPasswordRequired") },
              { min: 8, message: tUsers("createFieldPasswordMin") },
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>
          <div style={{ marginTop: -12, marginBottom: 16 }}>
            <Progress
              percent={passwordStrengthPercent(passwordWatch)}
              showInfo={false}
              strokeColor={passwordStrengthStroke(passwordWatch)}
              size="small"
              aria-hidden
            />
          </div>

          <Form.Item
            name="confirm_password"
            label={tUsers("createFieldPasswordConfirm")}
            dependencies={["password"]}
            rules={[
              { required: true, message: tUsers("createFieldPasswordConfirmRequired") },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue("password") === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error(tUsers("createFieldPasswordMismatch")));
                },
              }),
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>

          <Form.Item style={{ marginBottom: 0 }}>
            <Space wrap>
              <Link href="/users" prefetch={false}>
                <Button>{tUsers("createCancel")}</Button>
              </Link>
              <Button type="primary" htmlType="submit" loading={createUserMutation.isPending}>
                {tUsers("createSubmit")}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </Flex>
  );
}
