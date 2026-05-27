"use client";

import {
  Button,
  DatePicker,
  Form,
  Input,
  Modal,
  Popconfirm,
  Select,
  Space,
  Table,
  Tag,
  Typography,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import dayjs, { type Dayjs } from "dayjs";
import { useMemo, useState } from "react";

import type { Employee, EmployeePayload } from "@/lib/api/companies";
import { useEmployeeActions } from "@/lib/hooks/useCompanies";

type EmployeeFormValues = Omit<EmployeePayload, "start_date" | "end_date"> & {
  start_date: Dayjs;
  end_date?: Dayjs | null;
};

const employeeTypeOptions = ["Regular", "Intern", "PhD", "Designer", "Junior", "Senior"].map(
  (value) => ({ label: value, value }),
);

export function EmployeeManager({
  companyId,
  employees,
  canManage = true,
}: {
  companyId: string;
  employees: Employee[];
  canManage?: boolean;
}) {
  const [form] = Form.useForm<EmployeeFormValues>();
  const [editing, setEditing] = useState<Employee | null>(null);
  const [open, setOpen] = useState(false);
  const actions = useEmployeeActions(companyId);

  const activeCount = employees.filter((employee) => employee.is_active).length;
  const roleSummary = useMemo(() => {
    const counts = new Map<string, number>();
    for (const employee of employees) {
      counts.set(employee.type, (counts.get(employee.type) ?? 0) + 1);
    }
    return Array.from(counts, ([type, count]) => `${count} ${type}`).join(" · ");
  }, [employees]);

  const openCreate = () => {
    setEditing(null);
    form.setFieldsValue({
      name: "",
      type: "Regular",
      start_date: dayjs(),
      end_date: null,
      is_active: true,
    });
    setOpen(true);
  };

  const openEdit = (employee: Employee) => {
    setEditing(employee);
    form.setFieldsValue({
      name: employee.name,
      type: employee.type,
      start_date: dayjs(employee.start_date),
      end_date: employee.end_date ? dayjs(employee.end_date) : null,
      is_active: employee.is_active,
    });
    setOpen(true);
  };

  const save = async () => {
    const values = await form.validateFields();
    const payload = {
      ...values,
      start_date: dayjs(values.start_date).format("YYYY-MM-DD"),
      end_date: values.end_date ? dayjs(values.end_date).format("YYYY-MM-DD") : null,
    };
    if (editing) {
      await actions.update.mutateAsync({ employeeId: editing.id, payload });
    } else {
      await actions.create.mutateAsync(payload);
    }
    setOpen(false);
  };

  const columns: ColumnsType<Employee> = [
    { title: "Nome", dataIndex: "name", key: "name", ellipsis: true },
    { title: "Função/categoria", dataIndex: "type", key: "type", width: 160 },
    { title: "Entrada", dataIndex: "start_date", key: "start_date", width: 130 },
    {
      title: "Saída",
      dataIndex: "end_date",
      key: "end_date",
      width: 130,
      render: (value) => value || "—",
    },
    {
      title: "Estado",
      dataIndex: "is_active",
      key: "is_active",
      width: 120,
      render: (active: boolean) => (
        <Tag color={active ? "success" : "default"}>{active ? "Ativo" : "Inativo"}</Tag>
      ),
    },
    ...(canManage
      ? [
          {
            title: "Ações",
            key: "actions",
            width: 170,
            render: (_: unknown, employee: Employee) => (
              <Space>
                <Button size="small" onClick={() => openEdit(employee)}>
                  Editar
                </Button>
                <Popconfirm
                  title="Remover colaborador?"
                  okText="Remover"
                  cancelText="Cancelar"
                  onConfirm={() => actions.remove.mutate(employee.id)}
                >
                  <Button size="small" danger>
                    Remover
                  </Button>
                </Popconfirm>
              </Space>
            ),
          } satisfies ColumnsType<Employee>[number],
        ]
      : []),
  ];

  return (
    <Space direction="vertical" size="middle" style={{ width: "100%" }}>
      <Space style={{ width: "100%", justifyContent: "space-between" }} align="start" wrap>
        <Space direction="vertical" size={0}>
          <Typography.Text type="secondary">
            {employees.length} colaboradores registados, {activeCount} ativos
          </Typography.Text>
          <Typography.Text type="secondary">
            {roleSummary || "Sem categorias registadas"}
          </Typography.Text>
        </Space>
        {canManage ? (
          <Button type="primary" onClick={openCreate}>
            Adicionar colaborador
          </Button>
        ) : null}
      </Space>
      <Table<Employee>
        rowKey="id"
        columns={columns}
        dataSource={employees}
        pagination={{ pageSize: 8, hideOnSinglePage: true }}
        scroll={{ x: 760 }}
      />
      <Modal
        title={editing ? "Editar colaborador" : "Adicionar colaborador"}
        open={open}
        onCancel={() => setOpen(false)}
        onOk={save}
        okText="Guardar"
        confirmLoading={actions.create.isPending || actions.update.isPending}
      >
        <Form form={form} layout="vertical">
          <Form.Item
            name="name"
            label="Nome"
            rules={[{ required: true, message: "Indique o nome." }]}
          >
            <Input />
          </Form.Item>
          <Form.Item name="type" label="Função/categoria" rules={[{ required: true }]}>
            <Select options={employeeTypeOptions} />
          </Form.Item>
          <Form.Item name="start_date" label="Data de entrada" rules={[{ required: true }]}>
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="end_date" label="Data de saída">
            <DatePicker style={{ width: "100%" }} />
          </Form.Item>
          <Form.Item name="is_active" label="Estado" rules={[{ required: true }]}>
            <Select
              options={[
                { value: true, label: "Ativo" },
                { value: false, label: "Inativo" },
              ]}
            />
          </Form.Item>
        </Form>
      </Modal>
    </Space>
  );
}
