"use client";

import { ArrowLeftOutlined } from "@ant-design/icons";
import { useQuery } from "@tanstack/react-query";
import { isAxiosError } from "axios";
import {
  Button,
  Card,
  Flex,
  Form,
  Input,
  Result,
  Select,
  Spin,
  Switch,
  Typography,
  message,
} from "antd";
import Link from "next/link";
import { useCallback, useEffect } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { listCompanies } from "@/lib/api/companies";
import type { UserAdminRole, UserUpdatePayload } from "@/lib/api/users";
import { useUpdateUser, useUserDetail } from "@/lib/hooks/useUsers";
import { isDirectorRole } from "@/lib/auth/constants";
import { tUsers } from "@/lib/i18n/users";

type EditFormValues = {
  first_name: string;
  last_name: string;
  role: UserAdminRole;
  company_id?: string | null;
  is_active: boolean;
  new_password?: string;
};

function roleSelectOptions(): { value: UserAdminRole; label: string }[] {
  return [
    { value: "Director", label: tUsers("roleFilterDirector") },
    { value: "Staff", label: tUsers("roleFilterStaff") },
    { value: "Client", label: tUsers("roleFilterClient") },
  ];
}

function parseApiError(err: unknown): string | null {
  if (!isAxiosError(err) || !err.response?.data) return null;
  const data = err.response.data;
  if (typeof data === "object" && data !== null) {
    if ("detail" in data && typeof (data as { detail?: unknown }).detail === "string") {
      return (data as { detail: string }).detail;
    }
    const pairs = Object.entries(data as Record<string, unknown>).flatMap(([key, val]) => {
      if (Array.isArray(val) && val.length > 0 && typeof val[0] === "string") {
        return [`${key}: ${val[0]}`];
      }
      return [];
    });
    if (pairs.length > 0) return pairs.join(" ");
  }
  return null;
}

export function UserEditClient({ userId }: { userId: string }) {
  const { user, isReady } = useAuth();
  const director = Boolean(isReady && user && isDirectorRole(user.role));
  const [form] = Form.useForm<EditFormValues>();

  const watchedRole = Form.useWatch("role", form);

  const { data, isLoading, isError } = useUserDetail(userId, director);

  useEffect(() => {
    if (!data) return;
    form.setFieldsValue({
      first_name: data.first_name,
      last_name: data.last_name,
      role: data.role as UserAdminRole,
      company_id: data.company_id,
      is_active: data.is_active,
      new_password: "",
    });
  }, [data, form]);

  const companiesQuery = useQuery({
    queryKey: ["companies", "options", "user-edit", watchedRole],
    queryFn: () => listCompanies({ page_size: 200 }),
    enabled: watchedRole === "Client" && director && Boolean(userId),
    staleTime: 60_000,
  });

  const updateUserMutation = useUpdateUser();

  const onFinish = useCallback(
    async (values: EditFormValues) => {
      const payload: UserUpdatePayload = {
        first_name: values.first_name.trim(),
        last_name: values.last_name.trim(),
        role: values.role,
        is_active: values.is_active,
        company_id: values.role === "Client" ? (values.company_id ?? null) : null,
      };
      const pwd = values.new_password?.trim();
      if (pwd) {
        payload.password = pwd;
      }
      try {
        await updateUserMutation.mutateAsync({ userId, payload });
        message.success(tUsers("editSuccess"));
        form.setFieldsValue({ new_password: "" });
      } catch (err: unknown) {
        const parsed = parseApiError(err);
        message.error(parsed ?? tUsers("editError"));
      }
    },
    [form, updateUserMutation, userId],
  );

  if (!isReady || (director && isLoading && !data)) {
    return (
      <Flex align="center" justify="center" style={{ minHeight: 240 }}>
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

  if (isError || !data) {
    return (
      <Result
        status="404"
        title={tUsers("editNotFound")}
        extra={
          <Link href="/users" prefetch={false}>
            <Button type="primary">{tUsers("editBack")}</Button>
          </Link>
        }
      />
    );
  }

  const companyOptions =
    companiesQuery.data?.results.map((c) => ({
      value: c.id,
      label: c.name,
    })) ?? [];

  return (
    <Flex vertical gap={16}>
      <Link href="/users" prefetch={false}>
        <Button icon={<ArrowLeftOutlined aria-hidden />} type="link" style={{ paddingLeft: 0 }}>
          {tUsers("editBack")}
        </Button>
      </Link>

      <div>
        <Typography.Title level={3} style={{ marginBottom: 4 }}>
          {tUsers("editTitle")}
        </Typography.Title>
        <Typography.Paragraph type="secondary" style={{ marginBottom: 0 }}>
          {tUsers("editSubtitle")}
        </Typography.Paragraph>
      </div>

      <Card bordered>
        <Form<EditFormValues>
          form={form}
          layout="vertical"
          onFinish={(v) => void onFinish(v)}
          scrollToFirstError
        >
          <Flex vertical gap={4} style={{ marginBottom: 16 }}>
            <Typography.Text strong>{tUsers("editFieldEmail")}</Typography.Text>
            <Typography.Text>{data.email}</Typography.Text>
          </Flex>

          <Form.Item
            name="first_name"
            label={tUsers("editFieldFirstName")}
            rules={[{ required: true, message: tUsers("editValidationFirstName") }]}
          >
            <Input autoComplete="given-name" />
          </Form.Item>

          <Form.Item
            name="last_name"
            label={tUsers("editFieldLastName")}
            rules={[{ required: true, message: tUsers("editValidationLastName") }]}
          >
            <Input autoComplete="family-name" />
          </Form.Item>

          <Form.Item
            name="role"
            label={tUsers("editFieldRole")}
            rules={[{ required: true, message: tUsers("editValidationRole") }]}
          >
            <Select<UserAdminRole> options={roleSelectOptions()} />
          </Form.Item>

          {watchedRole === "Client" ? (
            <Form.Item
              name="company_id"
              label={tUsers("editFieldCompany")}
              rules={[
                {
                  validator: (_, v) => {
                    if (watchedRole !== "Client") return Promise.resolve();
                    if (v) return Promise.resolve();
                    return Promise.reject(new Error(tUsers("editValidationCompany")));
                  },
                },
              ]}
            >
              <Select
                allowClear={false}
                loading={companiesQuery.isLoading}
                options={companyOptions}
                placeholder={tUsers("editFieldCompany")}
                showSearch
                optionFilterProp="label"
              />
            </Form.Item>
          ) : null}

          <Form.Item
            name="is_active"
            label={tUsers("editFieldActive")}
            valuePropName="checked"
            rules={[{ required: true }]}
          >
            <Switch aria-label={tUsers("editFieldActive")} />
          </Form.Item>

          <Form.Item
            name="new_password"
            label={tUsers("editFieldPassword")}
            extra={tUsers("editFieldPasswordHint")}
            rules={[
              {
                validator: async (_, value) => {
                  const s = typeof value === "string" ? value.trim() : "";
                  if (!s) return;
                  if (s.length < 8) {
                    throw new Error(tUsers("editValidationPasswordMin"));
                  }
                },
              },
            ]}
          >
            <Input.Password autoComplete="new-password" />
          </Form.Item>

          <Form.Item>
            <Flex gap={8} wrap="wrap">
              <Button type="primary" htmlType="submit" loading={updateUserMutation.isPending}>
                {tUsers("editSave")}
              </Button>
              <Link href="/users" prefetch={false}>
                <Button>{tUsers("editCancel")}</Button>
              </Link>
            </Flex>
          </Form.Item>
        </Form>
      </Card>
    </Flex>
  );
}
