"use client";

import { Card, Typography } from "antd";

import { type StaffI18nKey, tStaff } from "@/lib/i18n/staffNav";

type Props = {
  titleKey: StaffI18nKey;
};

export function PlaceholderSection({ titleKey }: Props) {
  return (
    <Card title={tStaff(titleKey)}>
      <Typography.Paragraph type="secondary">{tStaff("pagePlaceholderBody")}</Typography.Paragraph>
    </Card>
  );
}
