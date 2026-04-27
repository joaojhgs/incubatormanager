"use client";

import { Tag } from "antd";

import { tCompany } from "@/lib/i18n/companies";

interface ArchivedBadgeProps {
  /** Whether the company is archived (is_active = false). */
  archived: boolean;
}

/**
 * Small coloured tag indicating that a company is archived.
 * Renders nothing when the company is active.
 */
export function ArchivedBadge({ archived }: ArchivedBadgeProps) {
  if (!archived) return null;
  return (
    <Tag color="default" style={{ marginLeft: 8 }}>
      {tCompany("badgeArchived")}
    </Tag>
  );
}
