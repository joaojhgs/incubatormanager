import { AntdRegistry } from "@ant-design/nextjs-registry";
import type { Metadata } from "next";
import type { ReactNode } from "react";

import { AuthProvider } from "@/components/auth/AuthProvider";
import { AppThemeProvider } from "@/components/ui/AppThemeProvider";
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
          <AppThemeProvider>
            <QueryProvider>
              <AuthProvider>{children}</AuthProvider>
            </QueryProvider>
          </AppThemeProvider>
        </AntdRegistry>
      </body>
    </html>
  );
}
