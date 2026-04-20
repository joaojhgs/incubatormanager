import { AntdRegistry } from "@ant-design/nextjs-registry";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AntdProvider } from "@/components/AntdProvider";

import "./globals.css";

export const metadata: Metadata = {
  title: "ILB Incubator",
  description: "ILB Incubator Management Platform",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-PT">
      <body>
        <AntdRegistry>
          <AntdProvider>{children}</AntdProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
