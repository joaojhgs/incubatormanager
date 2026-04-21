"use client";

import { Card, Typography } from "antd";

import { tStaff } from "@/lib/i18n/staffNav";

export function StaffWorkspaceHome() {
  return (
    <Card title={tStaff("pageHomeTitle")}>
      <Typography.Paragraph>{tStaff("pageHomeIntro")}</Typography.Paragraph>
    </Card>
  );
}
