"use client";

import { Layout, Typography } from "antd";
import type { ReactNode } from "react";

import { tClient } from "@/lib/i18n/clientPortal";

const { Header, Content } = Layout;

export function ClientPortalShell({ children }: { children: ReactNode }) {
  return (
    <Layout style={{ minHeight: "100vh" }}>
      <Header
        style={{
          display: "flex",
          alignItems: "center",
          paddingInline: 24,
          background: "#001529",
        }}
      >
        <Typography.Title level={4} style={{ margin: 0, color: "#fff" }}>
          {tClient("headerTitle")}
        </Typography.Title>
      </Header>
      <Content style={{ padding: 24 }}>{children}</Content>
    </Layout>
  );
}
