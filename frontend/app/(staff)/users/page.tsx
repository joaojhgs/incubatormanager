"use client";

import { FilterOutlined, UserOutlined } from "@ant-design/icons";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Button,
  Card,
  Drawer,
  Flex,
  Input,
  Radio,
  Result,
  Select,
  Space,
  Spin,
  Table,
  Tag,
  Typography,
  message,
} from "antd";
import type { ColumnsType } from "antd/es/table";
import Link from "next/link";

import { useAuth } from "@/components/auth/AuthProvider";
import { isDirectorRole, ROLE_CLIENT } from "@/lib/auth/constants";
import type { UserRead } from "@/lib/api/users";
import { useUsersList } from "@/lib/hooks/useUsers";
import { tUsers, userRoleDisplay } from "@/lib/i18n/users";

const { Title } = Typography;

const PAGE_SIZE = 20;

type ActiveFilter = "all" | "active" | "inactive";

function roleTagColor(role: string): string | undefined {
  const r = role.toLowerCase();
  if (r === "director") return "gold";
  if (r === "manager") return "blue";
  if (r === "coordinator") return "cyan";
  if (r === "staff") return "default";
  if (r === ROLE_CLIENT) return "green";
  return "purple";
}

function roleFilterOptions(): { value: string; label: string }[] {
  return [
    { value: "director", label: tUsers("roleFilterDirector") },
    { value: "manager", label: tUsers("roleFilterManager") },
    { value: "coordinator", label: tUsers("roleFilterCoordinator") },
    { value: "staff", label: tUsers("roleFilterStaff") },
    { value: ROLE_CLIENT, label: tUsers("roleFilterClient") },
  ];
}

export default function UsersListPage() {
  const { user, isReady } = useAuth();
  const director = Boolean(isReady && user && isDirectorRole(user.role));

  const { data, isLoading, isError } = useUsersList(director);

  const [searchInput, setSearchInput] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const debounceTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const [drawerOpen, setDrawerOpen] = useState(false);
  const [roleFilter, setRoleFilter] = useState<string | undefined>(undefined);
  const [activeFilter, setActiveFilter] = useState<ActiveFilter>("all");

  const [draftRole, setDraftRole] = useState<string | undefined>(undefined);
  const [draftActive, setDraftActive] = useState<ActiveFilter>("all");

  useEffect(() => {
    if (debounceTimer.current !== null) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(() => setDebouncedSearch(searchInput), 300);
    return () => {
      if (debounceTimer.current !== null) clearTimeout(debounceTimer.current);
    };
  }, [searchInput]);

  useEffect(() => {
    if (isError) {
      message.error(tUsers("listLoadError"));
    }
  }, [isError]);

  const openDrawer = useCallback(() => {
    setDraftRole(roleFilter);
    setDraftActive(activeFilter);
    setDrawerOpen(true);
  }, [roleFilter, activeFilter]);

  const applyDrawerFilters = useCallback(() => {
    setRoleFilter(draftRole);
    setActiveFilter(draftActive);
    setDrawerOpen(false);
    setPage(1);
  }, [draftRole, draftActive]);

  const clearDrawerFilters = useCallback(() => {
    setDraftRole(undefined);
    setDraftActive("all");
    setRoleFilter(undefined);
    setActiveFilter("all");
    setDrawerOpen(false);
    setPage(1);
  }, []);

  const [page, setPage] = useState(1);

  const filteredRows = useMemo(() => {
    const list = data ?? [];
    const q = debouncedSearch.trim().toLowerCase();
    return list.filter((row) => {
      if (roleFilter) {
        if (row.role.toLowerCase() !== roleFilter.toLowerCase()) return false;
      }
      if (activeFilter === "active" && !row.is_active) return false;
      if (activeFilter === "inactive" && row.is_active) return false;
      if (!q) return true;
      const hay = `${row.email} ${row.first_name} ${row.last_name}`.toLowerCase();
      return hay.includes(q);
    });
  }, [data, debouncedSearch, roleFilter, activeFilter]);

  const columns: ColumnsType<UserRead> = useMemo(
    () => [
      {
        title: tUsers("listColumnEmail"),
        dataIndex: "email",
        key: "email",
        width: 260,
      },
      {
        title: tUsers("listColumnName"),
        key: "name",
        render: (_: unknown, row: UserRead) => `${row.first_name} ${row.last_name}`.trim(),
      },
      {
        title: tUsers("listColumnRole"),
        dataIndex: "role",
        key: "role",
        width: 140,
        render: (role: string) => <Tag color={roleTagColor(role)}>{userRoleDisplay(role)}</Tag>,
      },
      {
        title: tUsers("listColumnStatus"),
        dataIndex: "is_active",
        key: "is_active",
        width: 120,
        render: (active: boolean) => (
          <Tag color={active ? "success" : "default"}>
            {active ? tUsers("listStatusActive") : tUsers("listStatusInactive")}
          </Tag>
        ),
      },
    ],
    [],
  );

  if (!isReady) {
    return (
      <Flex align="center" justify="center" style={{ minHeight: 240 }}>
        <Spin size="large" />
      </Flex>
    );
  }

  if (!director) {
    return (
      <Result
        status="403"
        title={tUsers("listForbiddenTitle")}
        subTitle={tUsers("listForbiddenDescription")}
        extra={
          <Link href="/dashboard" prefetch={false}>
            <Button type="primary">{tUsers("listForbiddenBack")}</Button>
          </Link>
        }
      />
    );
  }

  return (
    <>
      <Flex justify="space-between" align="center" wrap gap="small" style={{ marginBottom: 16 }}>
        <Title level={3} style={{ margin: 0 }}>
          <UserOutlined aria-hidden style={{ marginRight: 8 }} />
          {tUsers("listTitle")}
        </Title>
        <Space wrap>
          <Link href="/users/new" prefetch={false}>
            <Button type="primary">{tUsers("listCreateUser")}</Button>
          </Link>
          <Button type="default" icon={<FilterOutlined aria-hidden />} onClick={openDrawer}>
            {tUsers("listOpenFilters")}
          </Button>
        </Space>
      </Flex>

      <Card>
        <Space wrap size="middle" style={{ marginBottom: 16 }}>
          <Input
            placeholder={tUsers("listSearchPlaceholder")}
            allowClear
            value={searchInput}
            onChange={(e) => {
              setSearchInput(e.target.value);
              setPage(1);
            }}
            style={{ width: 320 }}
            aria-label={tUsers("listSearchPlaceholder")}
          />
        </Space>

        <Table<UserRead>
          rowKey="id"
          columns={columns}
          dataSource={filteredRows}
          loading={isLoading}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total: filteredRows.length,
            showSizeChanger: false,
            showTotal: (total, range) =>
              tUsers("listShowingPagination")
                .replace("{from}", String(total === 0 ? 0 : range[0]))
                .replace("{to}", String(range[1]))
                .replace("{total}", String(total)),
          }}
          onChange={(pagination) => {
            setPage(pagination.current ?? 1);
          }}
        />
      </Card>

      <Drawer
        title={tUsers("listDrawerTitle")}
        placement="right"
        width={320}
        onClose={() => setDrawerOpen(false)}
        open={drawerOpen}
        footer={
          <Space>
            <Button type="primary" onClick={applyDrawerFilters}>
              {tUsers("listApplyFilters")}
            </Button>
            <Button onClick={clearDrawerFilters}>{tUsers("listClearFilters")}</Button>
          </Space>
        }
      >
        <Space direction="vertical" size="large" style={{ width: "100%" }}>
          <div>
            <Typography.Text strong>{tUsers("listFilterRoleLabel")}</Typography.Text>
            <Select
              allowClear
              placeholder={tUsers("listFilterRoleAll")}
              style={{ width: "100%", marginTop: 8 }}
              value={draftRole}
              onChange={(v) => setDraftRole(v)}
              options={roleFilterOptions()}
            />
          </div>
          <div>
            <Typography.Text strong>{tUsers("listFilterActiveLabel")}</Typography.Text>
            <Radio.Group
              style={{ marginTop: 8, display: "flex", flexDirection: "column", gap: 8 }}
              value={draftActive}
              onChange={(e) => setDraftActive(e.target.value as ActiveFilter)}
            >
              <Radio value="all">{tUsers("listFilterActiveAll")}</Radio>
              <Radio value="active">{tUsers("listFilterActiveYes")}</Radio>
              <Radio value="inactive">{tUsers("listFilterActiveNo")}</Radio>
            </Radio.Group>
          </div>
        </Space>
      </Drawer>
    </>
  );
}
