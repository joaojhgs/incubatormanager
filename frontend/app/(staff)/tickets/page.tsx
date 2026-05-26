"use client";

import { useEffect, useMemo, useState } from "react";
import type { ColumnsType } from "antd/es/table";
import {
  Button,
  Card,
  Drawer,
  Empty,
  Form,
  Input,
  Result,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
} from "antd";

import {
  useAddTicketMessageAction,
  useCompanies,
  useTicketDetail,
  useTickets,
  useUpdateTicket,
  useUsersList,
} from "@/lib/hooks";
import { tStaff } from "@/lib/i18n/staffNav";
import type { Ticket } from "@/lib/hooks/useTickets";

const { Title, Text, Paragraph } = Typography;

const ticketStatusOptions = ["Open", "In progress", "Waiting response", "Resolved", "Closed"].map(
  (status) => ({ label: statusLabel(status), value: status }),
);

function statusLabel(status: string): string {
  if (status === "Open") return tStaff("ticketStatusOpen");
  if (status === "In progress") return tStaff("ticketStatusInProgress");
  if (status === "Waiting response") return tStaff("ticketStatusWaitingResponse");
  if (status === "Resolved") return tStaff("ticketStatusResolved");
  if (status === "Closed") return tStaff("ticketStatusClosed");
  return status;
}

function statusTag(status: string) {
  if (status === "Open") return <Tag color="red">{statusLabel(status)}</Tag>;
  if (status === "In progress") return <Tag color="blue">{statusLabel(status)}</Tag>;
  if (status === "Waiting response") return <Tag color="gold">{statusLabel(status)}</Tag>;
  if (status === "Resolved") return <Tag color="green">{statusLabel(status)}</Tag>;
  if (status === "Closed") return <Tag color="default">{statusLabel(status)}</Tag>;
  return <Tag>{status}</Tag>;
}

function formatDate(value: string): string {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-PT", { dateStyle: "short", timeStyle: "short" });
}

function rowKey(row: Ticket): string {
  return row.id;
}

function TicketDrawer({ ticketId, onClose }: { ticketId: string | null; onClose: () => void }) {
  const ticket = useTicketDetail(ticketId ?? "");
  const users = useUsersList(Boolean(ticketId));
  const updateTicket = useUpdateTicket();
  const addMessage = useAddTicketMessageAction();
  const [statusForm] = Form.useForm<{ status: string; assigned_to?: string }>();
  const [replyForm] = Form.useForm<{ content: string }>();

  useEffect(() => {
    if (ticket.data) {
      statusForm.setFieldsValue({
        status: ticket.data.status,
        assigned_to: ticket.data.assigned_to ?? undefined,
      });
    }
  }, [statusForm, ticket.data]);

  const loading = ticket.isLoading || updateTicket.isPending || addMessage.isPending;
  const assigneeOptions = useMemo(
    () =>
      (users.data ?? [])
        .filter((user) => user.is_active && ["Director", "Staff"].includes(user.role))
        .map((user) => ({
          label: `${user.first_name} ${user.last_name} · ${user.email}`,
          value: user.id,
        })),
    [users.data],
  );

  return (
    <Drawer open={Boolean(ticketId)} onClose={onClose} title="Detalhe do pedido" width={720}>
      {ticket.isLoading ? <Spin /> : null}
      {ticket.isError ? <Result status="error" title={tStaff("ticketsLoadError")} /> : null}
      {ticket.data ? (
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <Card size="small">
            <Title level={4}>{ticket.data.subject}</Title>
            <Paragraph>{ticket.data.description || "—"}</Paragraph>
            <Space wrap>
              {statusTag(ticket.data.status)}
              <Text type="secondary">{ticket.data.company_id}</Text>
              <Text type="secondary">{formatDate(ticket.data.updated_at)}</Text>
            </Space>
          </Card>

          <Card size="small" title="Fluxo de trabalho">
            <Form
              form={statusForm}
              layout="vertical"
              onFinish={(values) => {
                updateTicket.mutate({
                  ticketId: ticket.data.id,
                  payload: {
                    status: values.status,
                    assigned_to: values.assigned_to?.trim() || null,
                  },
                });
              }}
            >
              <Space align="end" wrap>
                <Form.Item name="status" label="Estado" rules={[{ required: true }]}>
                  <Select options={ticketStatusOptions} style={{ width: 220 }} />
                </Form.Item>
                <Form.Item name="assigned_to" label="Atribuir a">
                  <Select
                    aria-label="Atribuir colaborador"
                    allowClear
                    showSearch
                    optionFilterProp="label"
                    options={assigneeOptions}
                    placeholder={
                      users.isError
                        ? "Lista de colaboradores indisponível"
                        : "Selecionar colaborador"
                    }
                    notFoundContent={
                      users.isError ? "Sem permissão para listar utilizadores" : "Sem resultados"
                    }
                    style={{ width: 320 }}
                  />
                </Form.Item>
                <Form.Item>
                  <Button type="primary" htmlType="submit" loading={loading}>
                    Atualizar
                  </Button>
                </Form.Item>
              </Space>
            </Form>
          </Card>

          <Card size="small" title="Conversa">
            {ticket.data.messages.length === 0 ? (
              <Empty description="Sem mensagens." />
            ) : (
              <Space direction="vertical" style={{ width: "100%" }}>
                {ticket.data.messages.map((message) => (
                  <Card key={message.id} size="small" type="inner">
                    <Space direction="vertical" size={0}>
                      <Text strong>{message.author_role}</Text>
                      <Text type="secondary">{formatDate(message.created_at)}</Text>
                      <Paragraph style={{ marginBottom: 0 }}>{message.content}</Paragraph>
                    </Space>
                  </Card>
                ))}
              </Space>
            )}
            <Form
              form={replyForm}
              layout="vertical"
              style={{ marginTop: 16 }}
              onFinish={(values) => {
                addMessage.mutate(
                  { ticketId: ticket.data.id, payload: { content: values.content } },
                  { onSuccess: () => replyForm.resetFields() },
                );
              }}
            >
              <Form.Item name="content" label="Responder" rules={[{ required: true }]}>
                <Input.TextArea rows={3} placeholder="Escrever resposta…" />
              </Form.Item>
              <Button type="primary" htmlType="submit" loading={loading}>
                Enviar resposta
              </Button>
            </Form>
          </Card>
        </Space>
      ) : null}
    </Drawer>
  );
}

export default function TicketsPage() {
  const { data, isLoading, isError } = useTickets();
  const companies = useCompanies({ page_size: 200, is_active: true });
  const [selectedTicketId, setSelectedTicketId] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string | undefined>();

  useEffect(() => {
    const status = new URLSearchParams(window.location.search).get("status") ?? undefined;
    if (status) setStatusFilter(status);
  }, []);

  const companyNames = useMemo(
    () => new Map((companies.data?.results ?? []).map((company) => [company.id, company.name])),
    [companies.data],
  );

  const filteredTickets = useMemo(
    () => (data ?? []).filter((ticket) => !statusFilter || ticket.status === statusFilter),
    [data, statusFilter],
  );

  const columns: ColumnsType<Ticket> = [
    {
      title: tStaff("ticketsColumnCompany"),
      dataIndex: "company_id",
      key: "company_id",
      width: 260,
      ellipsis: true,
      render: (companyId: string | null) =>
        companyId ? (companyNames.get(companyId) ?? companyId) : "—",
    },
    {
      title: tStaff("ticketsColumnSubject"),
      dataIndex: "subject",
      key: "subject",
      width: 260,
    },
    {
      title: tStaff("ticketsColumnStatus"),
      dataIndex: "status",
      key: "status",
      width: 180,
      render: (status: string) => statusTag(status),
    },
    {
      title: tStaff("ticketsColumnOwner"),
      key: "owner",
      width: 180,
      render: (_: unknown, row: Ticket) => (
        <Text>
          {row.created_by_role || "Cliente"}
          <br />
          <Text type="secondary">Solicitante</Text>
        </Text>
      ),
    },
    {
      title: tStaff("ticketsColumnUpdatedAt"),
      dataIndex: "updated_at",
      key: "updated_at",
      render: (value: string) => formatDate(value),
    },
    {
      title: tStaff("columnActions"),
      key: "actions",
      width: 130,
      render: (_: unknown, row: Ticket) => (
        <Button size="small" onClick={() => setSelectedTicketId(row.id)}>
          Abrir
        </Button>
      ),
    },
  ];

  if (isLoading || companies.isLoading) {
    return <Spin size="large" tip={tStaff("pageLoading")} />;
  }

  if (isError || companies.isError) {
    return <Result status="error" title={tStaff("ticketsLoadError")} />;
  }

  return (
    <>
      <Title level={3}>{tStaff("ticketsListTitle")}</Title>
      <Card>
        <Space wrap style={{ marginBottom: 16 }}>
          <Select
            allowClear
            placeholder="Filtrar por estado"
            value={statusFilter}
            onChange={setStatusFilter}
            options={ticketStatusOptions}
            style={{ width: 220 }}
          />
        </Space>
        <Table<Ticket>
          rowKey={rowKey}
          columns={columns}
          dataSource={filteredTickets}
          locale={{ emptyText: tStaff("ticketsEmpty") }}
          pagination={{ pageSize: 10, hideOnSinglePage: true }}
          scroll={{ x: 1100 }}
          size="middle"
        />
      </Card>
      <TicketDrawer ticketId={selectedTicketId} onClose={() => setSelectedTicketId(null)} />
    </>
  );
}
