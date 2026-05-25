"use client";

import { Card, Result, Spin, Tag, Typography } from "antd";

import { useServiceHealth } from "@/lib/hooks";
import { type ServiceHealthDomain } from "@/lib/api/serviceHealth";

const { Text } = Typography;

export interface ServiceHealthPanelProps {
  title: string;
  service: ServiceHealthDomain;
  loadingMessage: string;
  statusUpText: string;
  statusDownText: string;
  unknownStatusText: string;
  statusLabelText?: string;
  unavailableText?: string;
}

export function ServiceHealthPanel({
  title,
  service,
  loadingMessage,
  statusUpText,
  statusDownText,
  unknownStatusText,
  statusLabelText = "Status",
  unavailableText,
}: ServiceHealthPanelProps) {
  const { data, isLoading, isError, dataUpdatedAt } = useServiceHealth(service);

  if (isLoading) {
    return (
      <Card title={title}>
        <Spin tip={loadingMessage} />
      </Card>
    );
  }

  if (isError) {
    return (
      <Card title={title}>
        <Result
          status="warning"
          title={statusDownText}
          subTitle={unavailableText}
          extra={
            <Text type="secondary">
              {new Date(dataUpdatedAt).toLocaleString("pt-PT", {
                dateStyle: "short",
                timeStyle: "short",
              })}
            </Text>
          }
        />
      </Card>
    );
  }

  const isUp = data?.status.toLowerCase() === "ok";

  return (
    <Card title={title}>
      <div style={{ display: "grid", gap: 8 }}>
        <span>
          <Text strong>{statusLabelText}</Text>
          <Tag color={isUp ? "success" : "warning"} style={{ marginLeft: 8 }}>
            {isUp ? statusUpText : statusDownText}
          </Tag>
          <Text type="secondary" style={{ marginLeft: 8 }}>
            {data?.status ?? unknownStatusText}
          </Text>
        </span>
        <Text type="secondary">
          {new Date(dataUpdatedAt).toLocaleString("pt-PT", {
            dateStyle: "short",
            timeStyle: "short",
          })}
        </Text>
      </div>
    </Card>
  );
}
