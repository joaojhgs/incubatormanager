"use client";

import { Button, Card, DatePicker, Form, Input, InputNumber, Result, Typography, message } from "antd";
import type { Dayjs } from "dayjs";

import { useCreatePublicBooking } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";

interface PublicBookingFormValues {
  company_id: string;
  space_id: string;
  requester_name: string;
  requester_email: string;
  requester_phone: string;
  start_time: Dayjs;
  end_time: Dayjs;
  quoted_price?: number;
  notes?: string;
}

export default function PublicBookingRequestPage() {
  const createPublicBooking = useCreatePublicBooking();

  const submit = (values: PublicBookingFormValues) => {
    createPublicBooking.mutate(
      {
        company_id: values.company_id,
        space_id: values.space_id,
        requester_name: values.requester_name,
        requester_email: values.requester_email,
        requester_phone: values.requester_phone,
        start_time: values.start_time.toISOString(),
        end_time: values.end_time.toISOString(),
        quoted_price: String(values.quoted_price ?? 0),
        notes: values.notes,
      },
      {
        onSuccess: () => message.success(tClient("bookingPublicSuccess")),
        onError: () => message.error(tClient("bookingPublicError")),
      },
    );
  };

  if (createPublicBooking.isSuccess) {
    return <Result status="success" title={tClient("bookingPublicSuccess")} />;
  }

  return (
    <main style={{ maxWidth: 760, margin: "48px auto", padding: 16 }}>
      <Card title={tClient("bookingPublicTitle")}>
        <Typography.Paragraph type="secondary">
          {tClient("bookingPublicDescription")}
        </Typography.Paragraph>
        <Form layout="vertical" onFinish={submit}>
          <Form.Item
            name="company_id"
            label={tClient("fieldCompanyId")}
            rules={[{ required: true, message: tClient("fieldRequired") }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="space_id"
            label={tClient("fieldSpace")}
            rules={[{ required: true, message: tClient("fieldRequired") }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="requester_name"
            label={tClient("fieldRequesterName")}
            rules={[{ required: true, message: tClient("fieldRequired") }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="requester_email"
            label={tClient("fieldRequesterEmail")}
            rules={[{ required: true, message: tClient("fieldRequired") }, { type: "email" }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="requester_phone"
            label={tClient("fieldRequesterPhone")}
            rules={[{ required: true, message: tClient("fieldRequired") }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="start_time"
            label={tClient("fieldStart")}
            rules={[{ required: true, message: tClient("fieldRequired") }]}
          >
            <DatePicker showTime style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="end_time"
            label={tClient("fieldEnd")}
            rules={[{ required: true, message: tClient("fieldRequired") }]}
          >
            <DatePicker showTime style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="quoted_price" label={tClient("fieldQuotedPrice")} initialValue={0}>
            <InputNumber min={0} precision={2} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="notes" label={tClient("fieldNotes")}>
            <Input.TextArea rows={4} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createPublicBooking.isPending}>
            {tClient("bookingCreateSubmit")}
          </Button>
        </Form>
      </Card>
    </main>
  );
}
