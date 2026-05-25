import { AntdRegistry } from "@ant-design/nextjs-registry";
import { ConfigProvider } from "antd";
import ptPT from "antd/locale/pt_PT";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthProvider } from "@/components/auth/AuthProvider";
import { tApp } from "@/lib/i18n/app";
import { QueryProvider } from "@/lib/query";

import "./globals.css";

export const metadata: Metadata = {
  title: tApp("metadataTitle"),
  description: tApp("metadataDescription"),
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-PT">
      <body>
        <AntdRegistry>
          <ConfigProvider
            locale={ptPT}
            theme={{
              token: {
                colorPrimary: "#005A9C",
                borderRadius: 6,
              },
            }}
          >
            <QueryProvider>
              <AuthProvider>{children}</AuthProvider>
            </QueryProvider>
          </ConfigProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
