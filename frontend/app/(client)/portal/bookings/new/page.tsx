"use client";

import {
  Alert,
  Button,
  Card,
  DatePicker,
  Form,
  Input,
  Result,
  Select,
  Space as AntSpace,
  Spin,
  Statistic,
  Typography,
} from "antd";
import type { Dayjs } from "dayjs";
import { useMemo } from "react";
import { useRouter } from "next/navigation";

import type { Equipment } from "@/lib/api/inventory";
import type { Space } from "@/lib/api/spaces";
import {
  bookingRangeOverlaps,
  disabledBookingDate,
  disabledBookingTime,
  spaceHasOverlap,
} from "@/lib/bookingAvailability";
import {
  calculateRentalEstimate,
  durationHours as calculateDurationHours,
  formatMoney,
  rateLabel,
} from "@/lib/pricing";
import {
  useCreateBooking,
  usePublicBookingWindows,
  usePublicEquipment,
  usePublicSpaces,
} from "@/lib/hooks";
import { tClient } from "@/lib/i18n/clientPortal";

interface BookingFormValues {
  space_id: string;
  start_time: Dayjs;
  end_time: Dayjs;
  equipment_ids?: string[];
  notes?: string;
}

function equipmentLabel(item: Equipment): string {
  return `${item.name} · ${rateLabel(item)}`;
}

export default function ClientNewBookingPage() {
  const router = useRouter();
  const [form] = Form.useForm<BookingFormValues>();
  const spaces = usePublicSpaces();
  const equipment = usePublicEquipment();
  const bookingWindows = usePublicBookingWindows();
  const createBooking = useCreateBooking();

  const selectedSpaceId = Form.useWatch("space_id", form);
  const selectedEquipmentIds = Form.useWatch("equipment_ids", form) ?? [];
  const startTime = Form.useWatch("start_time", form);
  const endTime = Form.useWatch("end_time", form);

  const availableSpaces = useMemo(
    () =>
      (spaces.data ?? []).filter(
        (space) =>
          space.is_active &&
          !space.company_id &&
          !["Blocked", "Maintenance"].includes(space.status) &&
          !spaceHasOverlap(bookingWindows.data, space.id, startTime, endTime),
      ),
    [bookingWindows.data, endTime, spaces.data, startTime],
  );
  const availableEquipment = useMemo(
    () => (equipment.data ?? []).filter((item) => item.is_active && item.status === "Available"),
    [equipment.data],
  );
  const selectedSpace = availableSpaces.find((space) => space.id === selectedSpaceId);
  const selectedEquipment = availableEquipment.filter((item) =>
    selectedEquipmentIds.includes(item.id),
  );
  const durationHours = useMemo(
    () => calculateDurationHours(startTime, endTime),
    [endTime, startTime],
  );
  const estimate = useMemo(
    () => calculateRentalEstimate(selectedSpace, selectedEquipment, durationHours),
    [durationHours, selectedEquipment, selectedSpace],
  );
  const estimatedPrice = estimate.total;

  if (spaces.isLoading || equipment.isLoading || bookingWindows.isLoading)
    return <Spin size="large" tip={tClient("pageLoading")} />;
  if (spaces.isError || equipment.isError || bookingWindows.isError)
    return <Result status="error" title={tClient("clientLoadError")} />;

  const submit = (values: BookingFormValues) => {
    createBooking.mutate(
      {
        space_id: values.space_id,
        start_time: values.start_time.toISOString(),
        end_time: values.end_time.toISOString(),
        quoted_price: estimatedPrice.toFixed(2),
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
      <Form form={form} layout="vertical" onFinish={submit}>
        <Form.Item
          name="space_id"
          label={tClient("fieldSpace")}
          rules={[{ required: true, message: tClient("fieldRequired") }]}
        >
          <Select
            showSearch
            optionFilterProp="label"
            placeholder={tClient("fieldSpace")}
            notFoundContent="Não existem espaços disponíveis para reserva."
            options={availableSpaces.map((space) => ({
              value: space.id,
              label: `${space.name} · ${space.status} · ${space.capacity} pessoas · ${rateLabel(
                space,
              )}`,
            }))}
          />
        </Form.Item>
        <Form.Item
          name="start_time"
          label={tClient("fieldStart")}
          rules={[{ required: true, message: tClient("fieldRequired") }]}
        >
          <DatePicker
            disabledDate={(date) =>
              disabledBookingDate(date, bookingWindows.data, selectedSpaceId)
            }
            disabledTime={(date) =>
              disabledBookingTime(date, bookingWindows.data, selectedSpaceId)
            }
            format="YYYY-MM-DD HH:mm"
            showTime={{ format: "HH:mm", minuteStep: 30 }}
            style={{ width: "100%" }}
          />
        </Form.Item>
        <Form.Item
          name="end_time"
          label={tClient("fieldEnd")}
          dependencies={["start_time"]}
          rules={[
            { required: true, message: tClient("fieldRequired") },
            ({ getFieldValue }) => ({
              validator(_, value: Dayjs | undefined) {
                const start = getFieldValue("start_time") as Dayjs | undefined;
                if (!value || !start || !value.isAfter(start)) {
                  return Promise.reject(new Error("O fim deve ser posterior ao início."));
                }
                if (!bookingRangeOverlaps(bookingWindows.data, selectedSpaceId, start, value)) {
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
            format="YYYY-MM-DD HH:mm"
            showTime={{ format: "HH:mm", minuteStep: 30 }}
            style={{ width: "100%" }}
          />
        </Form.Item>
        <Form.Item name="equipment_ids" label={tClient("fieldEquipment")}>
          <Select
            mode="multiple"
            optionFilterProp="label"
            placeholder="Selecione equipamento opcional"
            options={availableEquipment.map((item) => ({
              value: item.id,
              label: equipmentLabel(item),
            }))}
          />
        </Form.Item>
        <Card size="small" className="booking-estimate-card">
          <AntSpace direction="vertical" size={4} style={{ width: "100%" }}>
            <Typography.Text type="secondary">{tClient("fieldQuotedPrice")}</Typography.Text>
            <Statistic value={estimatedPrice} precision={2} prefix="€" />
            <Typography.Text type="secondary">
              {durationHours > 0
                ? `${durationHours}h · espaço ${formatMoney(estimate.spaceCost)} · equipamento ${formatMoney(
                    estimate.equipmentCost,
                  )}`
                : "Escolha o horário para calcular a estimativa automaticamente."}
            </Typography.Text>
          </AntSpace>
        </Card>
        <Alert
          type="info"
          showIcon
          style={{ margin: "16px 0" }}
          message="O valor é calculado automaticamente e validado pela equipa antes da aprovação."
        />
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
