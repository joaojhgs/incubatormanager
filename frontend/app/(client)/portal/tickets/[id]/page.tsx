"use client";

import {
  Button,
  Card,
  Descriptions,
  Empty,
  Form,
  Input,
  List,
  Result,
  Space,
  Spin,
  Tag,
  Typography,
} from "antd";
import Link from "next/link";
import { useParams } from "next/navigation";

import { useAddTicketMessage, useTicketDetail } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";
import { statusLabel } from "@/lib/i18n/status";

const { Text, Paragraph } = Typography;

interface MessageFormValues {
  content: string;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-PT", { dateStyle: "short", timeStyle: "short" });
}

export default function ClientTicketDetailPage() {
  const params = useParams<{ id: string }>();
  const ticketId = params.id;
  const ticket = useTicketDetail(ticketId);
  const addMessage = useAddTicketMessage(ticketId);
  const [form] = Form.useForm<MessageFormValues>();

  const submit = (values: MessageFormValues) => {
    addMessage.mutate(values, {
      onSuccess: () => form.resetFields(),
    });
  };

  if (ticket.isLoading) {
    return <Spin size="large" tip={tClient("pageLoading")} />;
  }

  if (ticket.isError || !ticket.data) {
    return <Result status="error" title={tClient("portalTicketsLoadError")} />;
  }

  return (
    <Space direction="vertical" size="large" style={{ width: "100%" }}>
      <Link href="/portal/tickets" prefetch={false}>
        {tClient("backToList")}
      </Link>
      <Card title={tClient("portalTicketDetailTitle")}>
        <Descriptions bordered layout="vertical" column={1}>
          <Descriptions.Item label={tClient("portalTicketSubject")}>
            <Text strong>{ticket.data.subject}</Text>
          </Descriptions.Item>
          <Descriptions.Item label={tClient("portalTicketsColumnStatus")}>
            <Tag>{statusLabel(ticket.data.status)}</Tag>
          </Descriptions.Item>
          <Descriptions.Item label={tClient("portalTicketOpenedBy")}>
            {ticket.data.created_by_role}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("portalTicketsColumnUpdatedAt")}>
            {formatDate(ticket.data.updated_at)}
          </Descriptions.Item>
          <Descriptions.Item label={tClient("portalTicketDescription")}>
            <Paragraph style={{ marginBottom: 0 }}>{ticket.data.description || "—"}</Paragraph>
          </Descriptions.Item>
        </Descriptions>
      </Card>
      <Card title={tClient("portalTicketThread")}>
        {ticket.data.messages.length ? (
          <List
            itemLayout="vertical"
            dataSource={ticket.data.messages}
            renderItem={(item) => (
              <List.Item key={item.id}>
                <List.Item.Meta
                  title={`${item.author_role} · ${formatDate(item.created_at)}`}
                  description={item.content}
                />
              </List.Item>
            )}
          />
        ) : (
          <Empty description={tClient("portalTicketNoMessages")} />
        )}
        <Form form={form} layout="vertical" onFinish={submit} style={{ marginTop: 24 }}>
          <Form.Item
            name="content"
            label={tClient("portalTicketMessage")}
            rules={[{ required: true, message: tClient("fieldRequired") }]}
          >
            <Input.TextArea rows={4} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={addMessage.isPending}>
            {tClient("portalTicketSendMessage")}
          </Button>
        </Form>
      </Card>
    </Space>
  );
}
