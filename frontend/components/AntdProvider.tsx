"use client";

import { ConfigProvider } from "antd";
import ptPT from "antd/locale/pt_PT";
import type { ReactNode } from "react";

export function AntdProvider({ children }: { children: ReactNode }) {
  return (
    <ConfigProvider
      locale={ptPT}
      theme={{
        token: {
          colorPrimary: "#005A9C",
          borderRadius: 6,
        },
      }}
    >
      {children}
    </ConfigProvider>
  );
}
