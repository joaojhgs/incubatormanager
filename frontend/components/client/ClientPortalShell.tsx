"use client";

import {
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
import { Avatar, Breadcrumb, Button, Dropdown, Layout, Menu, Space, theme, Typography } from "antd";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useCallback, useMemo, useState } from "react";

import { useAuth } from "@/components/auth/AuthProvider";
import { logoutSession, redirectToCookieClearingLogout } from "@/lib/api/auth";
import { type ClientPortalI18nKey, tClient } from "@/lib/i18n/clientPortal";
import { useLanguagePreference, type UiLanguage } from "@/lib/i18n/language";

import styles from "./ClientPortalShell.module.css";

const { Header, Sider, Content } = Layout;

const pathToTitleKey: Record<string, ClientPortalI18nKey> = {
  portal: "navDashboard",
  company: "navCompany",
  contract: "navContract",
  payments: "navPayments",
  bookings: "navBookings",
  tickets: "navSupport",
};

function menuSelectedKey(pathname: string): string {
  if (pathname === "/portal" || pathname === "/portal/") {
    return "/portal";
  }
  const segments = pathname.split("/").filter(Boolean);
  if (segments.length >= 2) {
    return `/portal/${segments[1]}`;
  }
  return "/portal";
}

function breadcrumbItemsForPath(pathname: string | null): { title: ReactNode }[] {
  const path = pathname ?? "/portal";
  const homeCrumb = {
    title: (
      <Link href="/portal" prefetch={false}>
        <HomeOutlined aria-hidden />
        <span>{tClient("breadcrumbHome")}</span>
      </Link>
    ),
  };

  if (path === "/portal" || path === "/portal/") {
    return [
      homeCrumb,
      {
        title: <Typography.Text>{tClient("navDashboard")}</Typography.Text>,
      },
    ];
  }

  const segments = path.split("/").filter(Boolean);
  const section = segments.length >= 2 ? segments[1] : undefined;
  const titleKey = section ? pathToTitleKey[section] : undefined;
  if (!titleKey) {
    return [homeCrumb];
  }

  return [
    homeCrumb,
    {
      title: <Typography.Text>{tClient(titleKey)}</Typography.Text>,
    },
  ];
}

export function ClientPortalShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logoutLocal } = useAuth();
  const { languageLabel, setLanguage } = useLanguagePreference();
  const [collapsed, setCollapsed] = useState(false);
  const { token } = theme.useToken();

  const selectedKey = menuSelectedKey(pathname ?? "/portal");

  const menuItems: MenuProps["items"] = useMemo(
    () => [
      {
        key: "/portal",
        icon: <DashboardOutlined aria-hidden />,
        label: (
          <Link href="/portal" prefetch={false}>
            {tClient("navDashboard")}
          </Link>
        ),
      },
      {
        key: "/portal/company",
        icon: <BankOutlined aria-hidden />,
        label: (
          <Link href="/portal/company" prefetch={false}>
            {tClient("navCompany")}
          </Link>
        ),
      },
      {
        key: "/portal/contract",
        icon: <FileTextOutlined aria-hidden />,
        label: (
          <Link href="/portal/contract" prefetch={false}>
            {tClient("navContract")}
          </Link>
        ),
      },
      {
        key: "/portal/payments",
        icon: <DollarOutlined aria-hidden />,
        label: (
          <Link href="/portal/payments" prefetch={false}>
            {tClient("navPayments")}
          </Link>
        ),
      },
      {
        key: "/portal/bookings",
        icon: <CalendarOutlined aria-hidden />,
        label: (
          <Link href="/portal/bookings" prefetch={false}>
            {tClient("navBookings")}
          </Link>
        ),
      },
      {
        key: "/portal/tickets",
        icon: <CustomerServiceOutlined aria-hidden />,
        label: (
          <Link href="/portal/tickets" prefetch={false}>
            {tClient("navSupport")}
          </Link>
        ),
      },
    ],
    [],
  );

  const breadcrumbItems = useMemo(() => breadcrumbItemsForPath(pathname), [pathname]);

  const languageMenu = useMemo(
    () => ({
      onClick: ({ key }: { key: string }) => setLanguage(key as UiLanguage),
      items: [{ key: "pt", label: tClient("languagePt") }],
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
        { key: "profile", label: tClient("menuProfile") },
        {
          key: "logout",
          label: tClient("menuLogout"),
          onClick: handleLogout,
        },
      ],
    }),
    [handleLogout],
  );

  return (
    <Layout className={styles.clientLayout} hasSider>
      <Sider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        theme="dark"
        breakpoint="lg"
        style={{ background: "#00474F" }}
      >
        <div className={styles.siderBrand}>{tClient("siderBrand")}</div>
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[selectedKey]}
          items={menuItems}
          style={{ background: "#00474F" }}
        />
      </Sider>
      <Layout>
        <Header
          className={styles.headerBar}
          style={{
            background: token.colorBgContainer,
            borderBottom: `1px solid ${token.colorSplit}`,
          }}
        >
          <Typography.Title level={4} className={styles.headerTitle}>
            {user?.email ?? tClient("headerTitle")}
          </Typography.Title>
          <Space size="middle">
            <Dropdown menu={languageMenu} trigger={["click"]}>
              <Button
                type="text"
                icon={<GlobalOutlined aria-hidden />}
                aria-label={tClient("headerLanguage")}
              >
                {languageLabel}
              </Button>
            </Dropdown>
            <Dropdown menu={accountMenu} trigger={["click"]}>
              <Button type="text" className={styles.accountTrigger}>
                <Space>
                  <Avatar size="small" icon={<UserOutlined aria-hidden />} />
                  <Typography.Text>{tClient("headerAccount")}</Typography.Text>
                </Space>
              </Button>
            </Dropdown>
          </Space>
        </Header>
        <Content
          className={styles.contentArea}
          style={{ background: token.colorBgContainer, border: `1px solid ${token.colorSplit}` }}
        >
          <Breadcrumb className={styles.breadcrumbRow} items={breadcrumbItems} />
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}
