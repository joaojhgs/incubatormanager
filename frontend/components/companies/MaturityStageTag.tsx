"use client";

import { Tag } from "antd";

import { tCompany, type CompanyI18nKey } from "@/lib/i18n/companies";

/** Maps maturity stage names to their display colours per mockup spec. */
const STAGE_COLOR_MAP: Record<string, string> = {
  Incubated: "blue",
  Startup: "green",
  Intermediate: "orange",
  Consolidated: "purple",
};

/** Maps maturity stage names to their i18n keys. */
const STAGE_I18N_KEY: Record<string, CompanyI18nKey> = {
  Incubated: "stageIncubated",
  Startup: "stageStartup",
  Intermediate: "stageIntermediate",
  Consolidated: "stageConsolidated",
};

interface MaturityStageTagProps {
  /** Stage name as returned by the API (e.g. "Incubated"). Empty string if unavailable. */
  stageName: string;
}

/** Coloured tag for a company's maturity stage. Renders a dash when stage is unknown. */
export function MaturityStageTag({ stageName }: MaturityStageTagProps) {
  if (!stageName) return <Tag>—</Tag>;
  const color = STAGE_COLOR_MAP[stageName] ?? "default";
  const label = STAGE_I18N_KEY[stageName] ? tCompany(STAGE_I18N_KEY[stageName]) : stageName;
  return <Tag color={color}>{label}</Tag>;
}
