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
  Spin,
  Typography,
} from "antd";
import type { Dayjs } from "dayjs";
import { useRouter } from "next/navigation";

import { useCreateBooking, useEquipment, useSpaces } from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";

interface BookingFormValues {
  space_id: string;
  start_time: Dayjs;
  end_time: Dayjs;
  quoted_price?: number;
  equipment_ids?: string[];
  notes?: string;
}

export default function ClientNewBookingPage() {
  const router = useRouter();
  const spaces = useSpaces();
  const equipment = useEquipment();
  const createBooking = useCreateBooking();

  if (spaces.isLoading || equipment.isLoading)
    return <Spin size="large" tip={tClient("pageLoading")} />;
  if (spaces.isError || equipment.isError)
    return <Result status="error" title={tClient("clientLoadError")} />;

  const submit = (values: BookingFormValues) => {
    createBooking.mutate(
      {
        space_id: values.space_id,
        start_time: values.start_time.toISOString(),
        end_time: values.end_time.toISOString(),
        quoted_price: String(values.quoted_price ?? 0),
        equipment_ids: values.equipment_ids ?? [],
        notes: values.notes,
      },
      { onSuccess: () => router.push("/portal/bookings") },
    );
  };

  return (
    <Card title={tClient("bookingNewTitle")}>
      <Typography.Paragraph type="secondary">
        {tClient("bookingNewDescription")}
      </Typography.Paragraph>
      <Form layout="vertical" onFinish={submit}>
        <Form.Item
          name="space_id"
          label={tClient("fieldSpace")}
          rules={[{ required: true, message: tClient("fieldRequired") }]}
        >
          <Select
            options={(spaces.data ?? []).map((space) => ({ value: space.id, label: space.name }))}
          />
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
        <Form.Item name="equipment_ids" label={tClient("fieldEquipment")}>
          <Select
            mode="multiple"
            options={(equipment.data ?? [])
              .filter((item) => item.status === "Available")
              .map((item) => ({ value: item.id, label: item.name }))}
          />
        </Form.Item>
        <Form.Item name="notes" label={tClient("fieldNotes")}>
          <Input.TextArea rows={3} />
        </Form.Item>
        <Button type="primary" htmlType="submit" loading={createBooking.isPending}>
          {tClient("bookingCreateSubmit")}
        </Button>
      </Form>
    </Card>
  );
}
