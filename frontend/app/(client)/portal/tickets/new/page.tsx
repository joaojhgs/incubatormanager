"use client";

import { Button, Card, Form, Input, Typography } from "antd";
import { useRouter } from "next/navigation";

import { useCreateTicket } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";

interface TicketFormValues {
  subject: string;
  description?: string;
}

export default function ClientNewTicketPage() {
  const router = useRouter();
  const createTicket = useCreateTicket();

  const submit = (values: TicketFormValues) => {
    createTicket.mutate(values, {
      onSuccess: (ticket) => router.push(`/portal/tickets/${ticket.id}`),
    });
  };

  return (
    <Card title={tClient("portalTicketNewTitle")}>
      <Typography.Paragraph type="secondary">
        {tClient("portalTicketDescription")}
      </Typography.Paragraph>
      <Form layout="vertical" onFinish={submit}>
        <Form.Item
          name="subject"
          label={tClient("portalTicketSubject")}
          rules={[{ required: true, message: tClient("fieldRequired") }]}
        >
          <Input />
        </Form.Item>
        <Form.Item name="description" label={tClient("portalTicketDescription")}>
          <Input.TextArea rows={6} />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={createTicket.isPending}>
          {tClient("portalTicketSubmit")}
        </Button>
      </Form>
    </Card>
  );
}
