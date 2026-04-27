"use client";

import { Card, Typography } from "antd";

import { type ClientPortalI18nKey, tClient } from "@/lib/i18n/clientPortal";

type Props = {
  titleKey: ClientPortalI18nKey;
};

export function ClientPlaceholderSection({ titleKey }: Props) {
  return (
    <Card title={tClient(titleKey)}>
      <Typography.Paragraph type="secondary">{tClient("pagePlaceholderBody")}</Typography.Paragraph>
    </Card>
  );
}
