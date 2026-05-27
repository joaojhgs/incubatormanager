"use client";

import { Alert, Button, Card, Form, Input, Space, Spin, Typography } from "antd";
import { useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { decodeAccessTokenPayload } from "@/lib/auth/accessTokenClaims";
import { getPostLoginPath } from "@/lib/auth/postLoginRedirect";
import { tAuth } from "@/lib/i18n/auth";
import { setAccessToken } from "@/lib/api/tokenStorage";

const { Title, Text } = Typography;

function extractDetail(data: unknown): string {
  if (data && typeof data === "object" && "detail" in data) {
    const d = (data as { detail: unknown }).detail;
    if (typeof d === "string" && d.trim()) return d;
  }
  return "";
}

export default function LoginForm() {
  const searchParams = useSearchParams();
  const { isReady, isAuthenticated, user, syncAuthFromStorage } = useAuth();
  const [bannerError, setBannerError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (!isReady || !isAuthenticated || !user) return;
    const next = searchParams.get("next");
    window.location.assign(getPostLoginPath(user.role, next));
  }, [isReady, isAuthenticated, user, searchParams]);

  const onFinish = async (values: { email: string; password: string }) => {
    setBannerError(null);
    setSubmitting(true);
    try {
      const res = await fetch("/api/auth/login/", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: values.email.trim(), password: values.password }),
      });
      const data: unknown = await res.json().catch(() => ({}));
      if (!res.ok) {
        if (res.status === 502) {
          setBannerError(extractDetail(data) || tAuth("loginErrorUnreachable"));
        } else {
          setBannerError(extractDetail(data) || tAuth("loginErrorInvalid"));
        }
        return;
      }
      const access = (data as { access?: unknown }).access;
      if (typeof access !== "string") {
        setBannerError(tAuth("loginErrorGeneric"));
        return;
      }
      setAccessToken(access);
      syncAuthFromStorage();
      const claims = decodeAccessTokenPayload(access);
      const role = typeof claims?.role === "string" ? claims.role.toLowerCase() : undefined;
      if (!role) {
        setBannerError(tAuth("loginErrorGeneric"));
        return;
      }
      const next = searchParams.get("next");
      window.location.assign(getPostLoginPath(role, next));
    } finally {
      setSubmitting(false);
    }
  };

  if (!isReady) {
    return <Spin size="large" style={{ margin: "48px auto", display: "block" }} />;
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
      }}
    >
      <Card
        style={{
          width: "100%",
          maxWidth: 460,
          borderRadius: 24,
          boxShadow: "0 28px 90px rgba(0, 0, 0, 0.38)",
        }}
        styles={{ body: { padding: 32 } }}
      >
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <div style={{ textAlign: "center" }}>
            <Title level={2} style={{ marginBottom: 8 }}>
              {tAuth("loginTitle")}
            </Title>
            <Text type="secondary">{tAuth("loginSubtitle")}</Text>
          </div>
          {bannerError ? (
            <Alert
              type="error"
              showIcon
              message={bannerError}
              style={{ marginBottom: 4 }}
              role="alert"
            />
          ) : null}
          <Form layout="vertical" onFinish={onFinish} requiredMark="optional">
            <Form.Item
              name="email"
              label={tAuth("loginEmailLabel")}
              hasFeedback
              validateTrigger="onBlur"
              rules={[
                { required: true, message: tAuth("fieldEmailRequired") },
                { type: "email", message: tAuth("fieldEmailInvalid") },
              ]}
            >
              <Input size="large" autoComplete="email" inputMode="email" />
            </Form.Item>
            <Form.Item
              name="password"
              label={tAuth("loginPasswordLabel")}
              hasFeedback
              validateTrigger="onBlur"
              rules={[{ required: true, message: tAuth("fieldPasswordRequired") }]}
            >
              <Input.Password size="large" autoComplete="current-password" />
            </Form.Item>
            <Form.Item style={{ marginBottom: 0 }}>
              <Button type="primary" htmlType="submit" loading={submitting} block size="large">
                {tAuth("loginSubmit")}
              </Button>
            </Form.Item>
          </Form>
        </Space>
      </Card>
    </div>
  );
}
