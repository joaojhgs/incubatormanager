"use client";

import { ConfigProvider, theme as antdTheme } from "antd";
import ptPT from "antd/locale/pt_PT";
import type { ReactNode } from "react";

export function AppThemeProvider({ children }: { children: ReactNode }) {
  return (
    <ConfigProvider
      locale={ptPT}
      theme={{
        algorithm: antdTheme.darkAlgorithm,
        token: {
          colorPrimary: "#38bdf8",
          colorInfo: "#38bdf8",
          colorSuccess: "#22c55e",
          colorWarning: "#f59e0b",
          colorError: "#fb7185",
          colorBgBase: "#08111f",
          colorBgContainer: "#101b2d",
          colorBgElevated: "#142037",
          colorBorder: "rgba(148, 163, 184, 0.22)",
          colorSplit: "rgba(148, 163, 184, 0.16)",
          colorText: "rgba(255, 255, 255, 0.92)",
          colorTextSecondary: "rgba(226, 232, 240, 0.68)",
          borderRadius: 14,
          fontFamily:
            "Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
        },
        components: {
          Layout: {
            bodyBg: "#08111f",
            headerBg: "rgba(8, 17, 31, 0.82)",
            siderBg: "#06101d",
          },
          Card: {
            colorBgContainer: "rgba(16, 27, 45, 0.86)",
            boxShadowTertiary: "0 22px 70px rgba(0, 0, 0, 0.28)",
          },
          Table: {
            headerBg: "rgba(30, 41, 59, 0.96)",
            rowHoverBg: "rgba(56, 189, 248, 0.08)",
          },
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
}
