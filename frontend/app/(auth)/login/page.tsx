"use client";

import { Card, Space, Typography } from "antd";

import { useAuth } from "@/components/auth/AuthProvider";
import { tAuth } from "@/lib/i18n/auth";

const { Title, Paragraph, Text } = Typography;

export default function LoginPage() {
  const { user, isReady, isAuthenticated } = useAuth();

  return (
    <Space direction="vertical" size="large" style={{ padding: 48, width: "100%", maxWidth: 520 }}>
      <Title level={2}>{tAuth("loginTitle")}</Title>
      <Card>
        <Paragraph>{tAuth("loginIntro")}</Paragraph>
        {isReady ? (
          isAuthenticated && user ? (
            <Text>
              {tAuth("loginRoleHint")} <strong>{user.role}</strong>
            </Text>
          ) : (
            <Text type="secondary">{tAuth("loginNotSignedIn")}</Text>
          )
        ) : null}
      </Card>
    </Space>
  );
}
