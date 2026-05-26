import type { CSSProperties } from "react";

import styles from "./InsightCharts.module.css";

export interface ChartDatum {
  label: string;
  value: number;
  color?: string;
}

const palette = ["#6ee7f9", "#a78bfa", "#22c55e", "#f59e0b", "#f472b6", "#60a5fa"];

function safeData(data: ChartDatum[]): Required<ChartDatum>[] {
  return data
    .filter((item) => Number.isFinite(item.value) && item.value > 0)
    .map((item, index) => ({ ...item, color: item.color ?? palette[index % palette.length] }));
}

function formatCompact(value: number): string {
  return new Intl.NumberFormat("pt-PT", { notation: "compact", maximumFractionDigits: 1 }).format(
    value,
  );
}

export function DonutChart({ data, centerLabel = "Total" }: { data: ChartDatum[]; centerLabel?: string }) {
  const rows = safeData(data);
  const total = rows.reduce((sum, item) => sum + item.value, 0);
  const circumference = 2 * Math.PI * 42;
  let offset = 0;

  if (rows.length === 0 || total === 0) {
    return <div className={styles.emptyState}>Sem dados suficientes</div>;
  }

  return (
    <div className={styles.donutWrap}>
      <svg className={styles.donutSvg} viewBox="0 0 120 120" role="img" aria-label={centerLabel}>
        <circle className={styles.donutTrack} cx="60" cy="60" r="42" />
        {rows.map((item) => {
          const dash = (item.value / total) * circumference;
          const slice = (
            <circle
              key={item.label}
              className={styles.donutSlice}
              cx="60"
              cy="60"
              r="42"
              stroke={item.color}
              strokeDasharray={`${dash} ${circumference - dash}`}
              strokeDashoffset={-offset}
            />
          );
          offset += dash;
          return slice;
        })}
        <text x="60" y="57" className={styles.donutCenterLabel}>
          {formatCompact(total)}
        </text>
        <text x="60" y="74" className={styles.donutCenterLabel} opacity="0.55">
          {centerLabel}
        </text>
      </svg>
      <div className={styles.legend}>
        {rows.map((item) => (
          <div key={item.label} className={styles.legendItem}>
            <span className={styles.legendSwatch} style={{ color: item.color, background: item.color }} />
            <span className={styles.legendLabel}>{item.label}</span>
            <span className={styles.legendValue}>{formatCompact(item.value)}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

export function BarList({ data, currency = false }: { data: ChartDatum[]; currency?: boolean }) {
  const rows = safeData(data);
  const max = Math.max(...rows.map((item) => item.value), 0);
  const formatter = currency
    ? new Intl.NumberFormat("pt-PT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })
    : new Intl.NumberFormat("pt-PT", { maximumFractionDigits: 0 });

  if (rows.length === 0 || max === 0) {
    return <div className={styles.emptyState}>Sem dados suficientes</div>;
  }

  return (
    <div className={styles.barList}>
      {rows.map((item) => (
        <div key={item.label} className={styles.barRow}>
          <div className={styles.barLabel}>{item.label}</div>
          <div className={styles.barTrack}>
            <div
              className={styles.barFill}
              style={{ width: `${Math.max(6, (item.value / max) * 100)}%`, "--bar-color": item.color } as CSSProperties}
            />
          </div>
          <div className={styles.barValue}>{formatter.format(item.value)}</div>
        </div>
      ))}
    </div>
  );
}

export function TrendBars({ data, currency = false }: { data: ChartDatum[]; currency?: boolean }) {
  const rows = safeData(data).slice(-8);
  const max = Math.max(...rows.map((item) => item.value), 0);
  const formatter = currency
    ? new Intl.NumberFormat("pt-PT", { style: "currency", currency: "EUR", maximumFractionDigits: 0 })
    : new Intl.NumberFormat("pt-PT", { maximumFractionDigits: 0 });

  if (rows.length === 0 || max === 0) {
    return <div className={styles.emptyState}>Sem dados suficientes</div>;
  }

  return (
    <div className={styles.trend}>
      {rows.map((item) => (
        <div key={item.label} className={styles.trendColumn} title={`${item.label}: ${formatter.format(item.value)}`}>
          <div className={styles.trendBar} style={{ height: `${Math.max(10, (item.value / max) * 150)}px` }} />
          <div className={styles.trendLabel}>{item.label}</div>
        </div>
      ))}
    </div>
  );
}
