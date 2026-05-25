"use client";

import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Result,
  Select,
  Typography,
  message,
} from "antd";
import type { Dayjs } from "dayjs";

import { useCreatePublicBooking, useSpaces } from "@/lib/hooks";
import { tPublicBooking } from "@/lib/i18n/publicBooking";

interface PublicBookingFormValues {
  company_name: string;
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
  const spaces = useSpaces();

  const submit = (values: PublicBookingFormValues) => {
    createPublicBooking.mutate(
      {
        space_id: values.space_id,
        requester_name: values.requester_name,
        requester_email: values.requester_email,
        requester_phone: values.requester_phone,
        start_time: values.start_time.toISOString(),
        end_time: values.end_time.toISOString(),
        quoted_price: String(values.quoted_price ?? 0),
        notes: [
          values.company_name ? `Empresa externa: ${values.company_name}` : null,
          values.notes,
        ]
          .filter(Boolean)
          .join("\n\n"),
      },
      {
        onSuccess: () => message.success(tPublicBooking("success")),
        onError: () => message.error(tPublicBooking("error")),
      },
    );
  };

  if (createPublicBooking.isSuccess) {
    return <Result status="success" title={tPublicBooking("success")} />;
  }

  return (
    <main style={{ maxWidth: 760, margin: "48px auto", padding: 16 }}>
      <Card title={tPublicBooking("pageTitle")}>
        <Typography.Paragraph type="secondary">{tPublicBooking("pageIntro")}</Typography.Paragraph>
        <Form layout="vertical" onFinish={submit}>
          <Form.Item
            name="company_name"
            label={tPublicBooking("companyNameLabel")}
            help={tPublicBooking("companyNameHelp")}
            rules={[{ required: true, message: tPublicBooking("companyNameRequired") }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="space_id"
            label={tPublicBooking("spaceIdLabel")}
            help={tPublicBooking("spaceIdHelp")}
            rules={[{ required: true, message: tPublicBooking("spaceIdRequired") }]}
          >
            <Select
              aria-label={tPublicBooking("spaceIdLabel")}
              showSearch
              loading={spaces.isLoading}
              optionFilterProp="label"
              options={(spaces.data ?? [])
                .filter((space) => space.is_active)
                .map((space) => ({
                  label: `${space.name} · ${space.capacity} pessoas`,
                  value: space.id,
                }))}
              placeholder={tPublicBooking("spacePlaceholder")}
            />
          </Form.Item>
          <Form.Item
            name="requester_name"
            label={tPublicBooking("requesterNameLabel")}
            rules={[{ required: true, message: tPublicBooking("requesterNameRequired") }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="requester_email"
            label={tPublicBooking("requesterEmailLabel")}
            rules={[
              { required: true, message: tPublicBooking("requesterEmailRequired") },
              { type: "email", message: tPublicBooking("requesterEmailInvalid") },
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="requester_phone"
            label={tPublicBooking("requesterPhoneLabel")}
            rules={[{ required: true, message: tPublicBooking("requesterPhoneRequired") }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="start_time"
            label={tPublicBooking("startTimeLabel")}
            rules={[{ required: true, message: tPublicBooking("startTimeRequired") }]}
          >
            <DatePicker showTime style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="end_time"
            label={tPublicBooking("endTimeLabel")}
            dependencies={["start_time"]}
            rules={[
              { required: true, message: tPublicBooking("endTimeRequired") },
              ({ getFieldValue }) => ({
                validator(_, value: Dayjs | undefined) {
                  const start = getFieldValue("start_time") as Dayjs | undefined;
                  if (!value || !start || value.isAfter(start)) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error(tPublicBooking("endTimeAfterStart")));
                },
              }),
            ]}
          >
            <DatePicker showTime style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item
            name="quoted_price"
            label={tPublicBooking("quotedPriceLabel")}
            initialValue={0}
          >
            <InputNumber min={0} precision={2} style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="notes" label={tPublicBooking("notesLabel")}>
            <Input.TextArea rows={4} placeholder={tPublicBooking("notesPlaceholder")} />
          </Form.Item>
          <Button type="primary" htmlType="submit" loading={createPublicBooking.isPending}>
            {createPublicBooking.isPending
              ? tPublicBooking("submitting")
              : tPublicBooking("submit")}
          </Button>
        </Form>
      </Card>
    </main>
  );
}
