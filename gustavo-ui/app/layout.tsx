import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/context/AuthContext";
import { ConfigProvider } from "@/lib/context/ConfigContext";
import QueryProvider from "./QueryProvider";
import { Toaster } from "@/components/ui/toaster";

export const metadata: Metadata = {
  title: "Gustavo — Container Orchestration",
  description: "Gustavo Nebula platform management UI",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">
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
