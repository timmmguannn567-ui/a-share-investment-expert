import type { Metadata } from "next";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";

export const metadata: Metadata = {
  title: "见微 · 股市专家",
  description: "个人使用的A股ETF与个股盘后辅助决策系统",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="zh-CN">
      <body><div className="app-shell"><Sidebar /><main className="main">{children}</main></div></body>
    </html>
  );
}

