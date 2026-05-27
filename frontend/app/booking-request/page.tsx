"use client";

import {
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  Result,
  Select,
  Space,
  Spin,
  Statistic,
  Typography,
  message,
} from "antd";
import type { Dayjs } from "dayjs";

import {
  bookingRangeOverlaps,
  disabledBookingDate,
  disabledBookingTime,
  spaceHasOverlap,
} from "@/lib/bookingAvailability";
import {
  useCreatePublicBooking,
  usePublicBookingWindows,
  usePublicEquipment,
  usePublicSpaces,
} from "@/lib/hooks";
import {
  calculateRentalEstimate,
  durationHours as calculateDurationHours,
  formatMoney,
  rateLabel,
} from "@/lib/pricing";
import { tPublicBooking } from "@/lib/i18n/publicBooking";

interface PublicBookingFormValues {
  company_name: string;
  space_id: string;
  requester_name: string;
  requester_email: string;
  requester_phone: string;
  start_time: Dayjs;
  end_time: Dayjs;
  equipment_ids?: string[];
  notes?: string;
}

export default function PublicBookingRequestPage() {
  const createPublicBooking = useCreatePublicBooking();
  const spaces = usePublicSpaces();
  const equipment = usePublicEquipment();
  const bookingWindows = usePublicBookingWindows();
  const [form] = Form.useForm<PublicBookingFormValues>();
  const selectedSpaceId = Form.useWatch("space_id", form);
  const selectedEquipmentIds = Form.useWatch("equipment_ids", form) ?? [];
  const startTime = Form.useWatch("start_time", form);
  const endTime = Form.useWatch("end_time", form);
  const availableSpaces = (spaces.data ?? []).filter(
    (space) =>
      space.is_active &&
      !space.company_id &&
      !["Blocked", "Maintenance"].includes(space.status) &&
      !spaceHasOverlap(bookingWindows.data, space.id, startTime, endTime),
  );
  const availableEquipment = (equipment.data ?? []).filter(
    (item) => item.is_active && item.status === "Available",
  );
  const selectedSpace = availableSpaces.find((space) => space.id === selectedSpaceId);
  const selectedEquipment = availableEquipment.filter((item) =>
    selectedEquipmentIds.includes(item.id),
  );
  const hours = calculateDurationHours(startTime, endTime);
  const estimate = calculateRentalEstimate(selectedSpace, selectedEquipment, hours);

  const submit = (values: PublicBookingFormValues) => {
    createPublicBooking.mutate(
      {
        space_id: values.space_id,
        requester_name: values.requester_name,
        requester_email: values.requester_email,
        requester_phone: values.requester_phone,
        start_time: values.start_time.toISOString(),
        end_time: values.end_time.toISOString(),
        quoted_price: estimate.total.toFixed(2),
        equipment_ids: values.equipment_ids ?? [],
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
  if (spaces.isLoading || equipment.isLoading || bookingWindows.isLoading) {
    return <Spin size="large" style={{ margin: "48px auto", display: "block" }} />;
  }
  if (spaces.isError || equipment.isError || bookingWindows.isError) {
    return <Result status="error" title="Não foi possível carregar a disponibilidade." />;
  }

  return (
    <main style={{ maxWidth: 760, margin: "48px auto", padding: 16 }}>
      <Card title={tPublicBooking("pageTitle")}>
        <Typography.Paragraph type="secondary">{tPublicBooking("pageIntro")}</Typography.Paragraph>
        <Form form={form} layout="vertical" onFinish={submit}>
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
              options={availableSpaces.map((space) => ({
                label: `${space.name} · ${space.status} · ${space.capacity} pessoas · ${rateLabel(
                  space,
                )}`,
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
            <DatePicker
              disabledDate={(date) =>
                disabledBookingDate(date, bookingWindows.data, selectedSpaceId)
              }
              disabledTime={(date) =>
                disabledBookingTime(date, bookingWindows.data, selectedSpaceId)
              }
              showTime={{ format: "HH:mm", minuteStep: 30 }}
              style={{ width: "100%" }}
            />
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
                  if (!value || !start || !value.isAfter(start)) {
                    return Promise.reject(new Error(tPublicBooking("endTimeAfterStart")));
                  }
                  if (
                    !bookingRangeOverlaps(bookingWindows.data, selectedSpaceId, start, value)
                  ) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error("O espaço já tem uma reserva nesse período."));
                },
              }),
            ]}
          >
            <DatePicker
              disabledDate={(date) =>
                disabledBookingDate(date, bookingWindows.data, selectedSpaceId)
              }
              disabledTime={(date) =>
                disabledBookingTime(date, bookingWindows.data, selectedSpaceId)
              }
              showTime={{ format: "HH:mm", minuteStep: 30 }}
              style={{ width: "100%" }}
            />
          </Form.Item>
          <Form.Item name="equipment_ids" label="Equipamento opcional">
            <Select
              mode="multiple"
              optionFilterProp="label"
              options={availableEquipment.map((item) => ({
                label: `${item.name} · ${rateLabel(item)}`,
                value: item.id,
              }))}
              placeholder="Selecionar equipamento"
            />
          </Form.Item>
          <Card size="small" style={{ marginBottom: 16 }}>
            <Space direction="vertical" size={4}>
              <Typography.Text type="secondary">Estimativa automática</Typography.Text>
              <Statistic value={estimate.total} precision={2} prefix="€" />
              <Typography.Text type="secondary">
                {hours > 0
                  ? `${hours}h · espaço ${formatMoney(estimate.spaceCost)} · equipamento ${formatMoney(
                      estimate.equipmentCost,
                    )}`
                  : "Escolha espaço e horário para calcular."}
              </Typography.Text>
            </Space>
          </Card>
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
