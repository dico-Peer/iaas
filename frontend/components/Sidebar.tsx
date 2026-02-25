"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuthStore } from "@/lib/store";
import { useState } from "react";

const NAV_ITEMS = [
  { href: "/dashboard", label: "Dashboard", icon: "📊" },
  { href: "/projects", label: "Projects", icon: "📋" },
  { href: "/templates", label: "Templates", icon: "📑" },
  { href: "/team", label: "Team", icon: "👥", adminOnly: true },
  { href: "/settings", label: "Settings", icon: "⚙️" },
] as const;

export function Sidebar() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);
  const [mobileOpen, setMobileOpen] = useState(false);
  const isAdmin = user?.role === "org_admin" || user?.role === "system_admin";

  return (
    <>
      <button
        type="button"
        className="fixed left-4 top-4 z-50 rounded p-2 md:hidden"
        onClick={() => setMobileOpen(!mobileOpen)}
        aria-label="Toggle menu"
        data-testid="hamburger-menu"
      >
        ☰
      </button>
      <aside
        className={`fixed left-0 top-0 z-40 h-full w-56 border-r bg-white transition-transform md:translate-x-0 ${
          mobileOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"
        }`}
        data-testid="sidebar"
      >
        <nav className="flex flex-col gap-1 p-4 pt-16">
          {NAV_ITEMS.filter((item) => !("adminOnly" in item && item.adminOnly) || isAdmin).map(
            (item) => (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-2 rounded px-3 py-2 ${
                  pathname === item.href ? "bg-gray-100 font-medium" : ""
                }`}
              >
                <span>{item.icon}</span>
                <span>{item.label}</span>
              </Link>
            )
          )}
        </nav>
      </aside>
    </>
  );
}
