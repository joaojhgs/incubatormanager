"use client";

import {
  AppstoreOutlined,
  BankOutlined,
  CalendarOutlined,
  CustomerServiceOutlined,
  DashboardOutlined,
  DollarOutlined,
  FileTextOutlined,
  GlobalOutlined,
  HomeOutlined,
  UserOutlined,
} from "@ant-design/icons";
import type { MenuProps } from "antd";
import { Avatar, Breadcrumb, Button, Dropdown, Layout, Menu, Space, Typography } from "antd";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useCallback, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { logoutSession, redirectToCookieClearingLogout } from "@/lib/api/auth";
import { isDirectorRole } from "@/lib/auth/constants";
import { useLanguagePreference, type UiLanguage } from "@/lib/i18n/language";
import { tStaff, type StaffI18nKey } from "@/lib/i18n/staffNav";

import styles from "./StaffShell.module.css";

const { Header, Sider, Content } = Layout;

const pathToTitleKey: Record<string, StaffI18nKey> = {
  dashboard: "navDashboard",
  companies: "navCompanies",
  contracts: "navContracts",
  finance: "navFinance",
  spaces: "navSpaces",
  bookings: "navBookings",
  inventory: "navInventory",
  tickets: "navTickets",
  users: "navUsers",
};

function menuBasePath(pathname: string): string {
  if (pathname === "/" || pathname === "") {
    return "/dashboard";
  }
  const segment = pathname.split("/").filter(Boolean)[0];
  return segment ? `/${segment}` : "/dashboard";
}

function breadcrumbItemsForPath(pathname: string | null): { title: ReactNode }[] {
  const path = pathname ?? "/";
  const homeCrumb = {
    title: (
      <Link href="/dashboard" prefetch={false}>
        <HomeOutlined aria-hidden />
        <span>{tStaff("breadcrumbHome")}</span>
      </Link>
    ),
  };

  if (path === "/" || path === "/dashboard") {
    return [
      homeCrumb,
      {
        title: <Typography.Text>{tStaff("navDashboard")}</Typography.Text>,
      },
    ];
  }

  const segments = path.split("/").filter(Boolean);
  if (segments[0] === "users" && segments[1] === "new") {
    return [
      homeCrumb,
      {
        title: (
          <Link href="/users" prefetch={false}>
            {tStaff("navUsers")}
          </Link>
        ),
      },
      {
        title: <Typography.Text>{tStaff("breadcrumbUserCreate")}</Typography.Text>,
      },
    ];
  }

  const segment = segments[0];
  const titleKey = segment ? pathToTitleKey[segment] : undefined;
  if (!titleKey) {
    return [homeCrumb];
  }

  return [
    homeCrumb,
    {
      title: <Typography.Text>{tStaff(titleKey)}</Typography.Text>,
    },
  ];
}

export function StaffShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [collapsed, setCollapsed] = useState(false);
  const { user, isReady, logoutLocal } = useAuth();
  const { languageLabel, setLanguage } = useLanguagePreference();

  const selectedKey = menuBasePath(pathname ?? "/");

  const menuItems: MenuProps["items"] = useMemo(() => {
    const items: MenuProps["items"] = [
      {
        key: "/dashboard",
        icon: <DashboardOutlined aria-hidden />,
        label: (
          <Link href="/dashboard" prefetch={false}>
            {tStaff("navDashboard")}
          </Link>
        ),
      },
      {
        key: "/companies",
        icon: <BankOutlined aria-hidden />,
        label: (
          <Link href="/companies" prefetch={false}>
            {tStaff("navCompanies")}
          </Link>
        ),
      },
      {
        key: "/contracts",
        icon: <FileTextOutlined aria-hidden />,
        label: (
          <Link href="/contracts" prefetch={false}>
            {tStaff("navContracts")}
          </Link>
        ),
      },
      {
        key: "/finance",
        icon: <DollarOutlined aria-hidden />,
        label: (
          <Link href="/finance" prefetch={false}>
            {tStaff("navFinance")}
          </Link>
        ),
      },
      {
        key: "/spaces",
        icon: <HomeOutlined aria-hidden />,
        label: (
          <Link href="/spaces" prefetch={false}>
            {tStaff("navSpaces")}
          </Link>
        ),
      },
      {
        key: "/bookings",
        icon: <CalendarOutlined aria-hidden />,
        label: (
          <Link href="/bookings" prefetch={false}>
            {tStaff("navBookings")}
          </Link>
        ),
      },
      {
        key: "/inventory",
        icon: <AppstoreOutlined aria-hidden />,
        label: (
          <Link href="/inventory" prefetch={false}>
            {tStaff("navInventory")}
          </Link>
        ),
      },
      {
        key: "/tickets",
        icon: <CustomerServiceOutlined aria-hidden />,
        label: (
          <Link href="/tickets" prefetch={false}>
            {tStaff("navTickets")}
          </Link>
        ),
      },
    ];

    if (isReady && user && isDirectorRole(user.role)) {
      items.push({
        key: "/users",
        icon: <UserOutlined aria-hidden />,
        label: (
          <Link href="/users" prefetch={false}>
            {tStaff("navUsers")}
          </Link>
        ),
      });
    }

    return items;
  }, [isReady, user]);

  const breadcrumbItems = useMemo(() => breadcrumbItemsForPath(pathname), [pathname]);

  const languageMenu = useMemo(
    () => ({
      onClick: ({ key }: { key: string }) => setLanguage(key as UiLanguage),
      items: [{ key: "pt", label: tStaff("languagePt") }],
    }),
    [setLanguage],
  );

  const handleLogout = useCallback(() => {
    void (async () => {
      try {
        await logoutSession();
        logoutLocal();
        router.push("/login");
      } catch {
        logoutLocal();
        redirectToCookieClearingLogout("/login");
      }
    })();
  }, [logoutLocal, router]);

  const accountMenu = useMemo(
    () => ({
      items: [
        { key: "profile", label: tStaff("menuProfile") },
        {
          key: "logout",
          label: tStaff("menuLogout"),
          onClick: handleLogout,
        },
      ],
    }),
    [handleLogout],
  );

  return (
    <Layout className={styles.staffLayout} hasSider>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        breakpoint="lg"
      >
        <div className={styles.siderBrand}>{tStaff("siderBrand")}</div>
        <Menu theme="dark" mode="inline" selectedKeys={[selectedKey]} items={menuItems} />
      </Sider>
      <Layout>
        <Header className={styles.headerBar}>
          <Typography.Title level={4} className={styles.headerTitle}>
            {tStaff("headerWorkspace")}
          </Typography.Title>
          <Space size="middle">
            <Dropdown menu={languageMenu} trigger={["click"]}>
              <Button
                type="text"
                icon={<GlobalOutlined aria-hidden />}
                aria-label={tStaff("headerLanguage")}
              >
                {languageLabel}
              </Button>
            </Dropdown>
            <Dropdown menu={accountMenu} trigger={["click"]}>
              <Button type="text" className={styles.accountTrigger}>
                <Space>
                  <Avatar size="small" icon={<UserOutlined aria-hidden />} />
                  <Typography.Text>{tStaff("headerAccount")}</Typography.Text>
                </Space>
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content className={styles.contentArea}>
          <Breadcrumb className={styles.breadcrumbRow} items={breadcrumbItems} />
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
