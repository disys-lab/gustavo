import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from "@/lib/context/AuthContext";
import { ConfigProvider } from "@/lib/context/ConfigContext";
import QueryProvider from "./QueryProvider";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Gustavo — Container Orchestration",
  description: "Gustavo Nebula platform management UI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <QueryProvider>
          <AuthProvider>
            <ConfigProvider>
              {children}
              <Toaster />
            </ConfigProvider>
          </AuthProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
