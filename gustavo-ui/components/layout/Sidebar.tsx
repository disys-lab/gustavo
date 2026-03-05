"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard, LayoutGrid, Database, Users, Activity, Archive, Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/context/AuthContext";
import { ActivitySheet } from "@/components/layout/ActivitySheet";
import { useServiceHealth } from "@/lib/hooks/useServiceHealth";

// "/manager" (Services) is intentionally not in the sidebar — service controls
// live in the Dashboard's expandable "Manage Platform Services" section.
// The route still exists for direct linking if needed in future.
const NAV = [
  { href: "/dashboard",     label: "Dashboard",     icon: LayoutDashboard },
  { href: "/apps",          label: "Apps",          icon: LayoutGrid },
  { href: "/registry",      label: "Registry",      icon: Database },
  { href: "/device-groups", label: "Device Groups", icon: Users },
  { href: "/monitoring",    label: "Monitoring",    icon: Activity },
  { href: "/backups",       label: "Backups",       icon: Archive },
  { href: "/settings",      label: "Settings",      icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { logout } = useAuth();
  const { allUp } = useServiceHealth();

  return (
    <aside className="flex flex-col w-56 min-h-screen bg-white border-r border-gray-200 px-3 py-5 shrink-0">
      {/* Logo */}
      <div className="flex flex-col items-center gap-1 mb-7 px-2">
        <Image
          src="/gustavo_wordmark.png"
          alt="Gustavo"
          width={120}
          height={32}
          priority
        />
      </div>

      <nav className="flex flex-col gap-0.5 flex-1">
        {NAV.map(({ href, label, icon: Icon }) => {
          const isActive = pathname.startsWith(href);
          const isManager = href === "/dashboard";
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-gray-100 text-gray-900"
                  : "text-gray-600 hover:bg-gray-50 hover:text-gray-900"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              <span className="flex-1">{label}</span>
              {isManager && (
                <span
                  className={cn(
                    "h-2 w-2 rounded-full shrink-0",
                    allUp === null ? "bg-gray-300" : allUp ? "bg-green-500" : "bg-red-500"
                  )}
                  title={allUp === null ? "Status unknown" : allUp ? "All services up" : "Some services down"}
                />
              )}
            </Link>
          );
        })}
      </nav>

      <div className="mt-2 border-t pt-2 space-y-0.5">
        <ActivitySheet />
        <button
          onClick={logout}
          className="w-full rounded-md px-3 py-2 text-sm font-medium text-gray-400 hover:bg-gray-50 hover:text-gray-700 transition-colors text-left"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
