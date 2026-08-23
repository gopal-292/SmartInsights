"use client";

import clsx from "clsx";
import {
  AlertTriangle,
  BarChart3,
  Bot,
  Building2,
  FileText,
  LayoutDashboard,
  LogOut,
  Menu,
  MessageSquareHeart,
  Package,
  Sparkles,
  TrendingUp,
  Upload,
  Users,
  Wallet,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import { useAuth } from "@/lib/auth";

const groups = [
  {
    label: "Overview",
    links: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/upload", label: "Upload Data", icon: Upload },
    ],
  },
  {
    label: "Analytics",
    links: [
      { href: "/sales", label: "Sales", icon: BarChart3 },
      { href: "/expenses", label: "Expenses", icon: Wallet },
      { href: "/inventory", label: "Inventory", icon: Package },
    ],
  },
  {
    label: "Intelligence",
    links: [
      { href: "/forecast", label: "Forecast", icon: TrendingUp },
      { href: "/anomalies", label: "Anomalies", icon: AlertTriangle },
      { href: "/sentiment", label: "Sentiment", icon: MessageSquareHeart },
      { href: "/segments", label: "Segments", icon: Users },
      { href: "/insights", label: "AI Insights", icon: Sparkles },
      { href: "/assistant", label: "Assistant", icon: Bot },
    ],
  },
  {
    label: "Output",
    links: [
      { href: "/report", label: "Report", icon: FileText },
      { href: "/profile", label: "Business Profile", icon: Building2 },
    ],
  },
];

function NavBody({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate?: () => void;
}) {
  const { user, logout } = useAuth();

  return (
    <>
      <div className="border-b border-white/10 px-5 py-5">
        <Link href="/dashboard" onClick={onNavigate} className="block">
          <p className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-white">
            SmartInsights
          </p>
          <p className="mt-1 text-xs text-teal-100/65">AI Business Analyzer</p>
        </Link>
      </div>

      <nav className="si-scroll flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {groups.map((group) => (
          <div key={group.label}>
            <p className="mb-1.5 px-3 text-[10px] font-semibold uppercase tracking-[0.16em] text-teal-100/40">
              {group.label}
            </p>
            <div className="space-y-0.5">
              {group.links.map(({ href, label, icon: Icon }) => {
                const active = pathname === href;
                return (
                  <Link
                    key={href}
                    href={href}
                    onClick={onNavigate}
                    className={clsx(
                      "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-sm transition",
                      active
                        ? "bg-white/12 text-white shadow-inner"
                        : "text-teal-50/70 hover:bg-white/8 hover:text-white"
                    )}
                  >
                    <span
                      className={clsx(
                        "flex h-7 w-7 items-center justify-center rounded-lg transition",
                        active
                          ? "bg-teal-400/20 text-teal-100"
                          : "bg-white/5 text-teal-100/70 group-hover:bg-white/10"
                      )}
                    >
                      <Icon size={14} />
                    </span>
                    {label}
                    {active ? (
                      <span className="ml-auto h-1.5 w-1.5 rounded-full bg-teal-300" />
                    ) : null}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/10 p-4">
        <div className="rounded-xl bg-white/5 px-3 py-3">
          <p className="truncate text-sm font-medium text-white">
            {user?.full_name}
          </p>
          <p className="truncate text-xs text-teal-100/55">{user?.email}</p>
          <button
            onClick={logout}
            className="mt-3 inline-flex items-center gap-2 text-xs text-teal-100/75 transition hover:text-white"
          >
            <LogOut size={13} /> Sign out
          </button>
        </div>
      </div>
    </>
  );
}

export function Sidebar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <>
      <aside className="sticky top-0 hidden h-screen w-64 shrink-0 flex-col border-r border-white/5 bg-[var(--sidebar)] text-[var(--sidebar-ink)] lg:flex">
        <NavBody pathname={pathname} />
      </aside>

      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--line)] bg-[var(--panel)]/90 px-4 py-3 backdrop-blur lg:hidden">
        <p className="font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
          SmartInsights
        </p>
        <button
          type="button"
          aria-label="Open menu"
          onClick={() => setOpen(true)}
          className="rounded-xl border border-[var(--line)] p-2 text-[var(--ink)]"
        >
          <Menu size={18} />
        </button>
      </div>

      {open ? (
        <div className="fixed inset-0 z-40 lg:hidden">
          <button
            type="button"
            aria-label="Close menu"
            className="absolute inset-0 bg-black/40"
            onClick={() => setOpen(false)}
          />
          <aside className="absolute inset-y-0 left-0 flex w-72 flex-col bg-[var(--sidebar)] text-[var(--sidebar-ink)] shadow-2xl">
            <button
              type="button"
              aria-label="Close"
              onClick={() => setOpen(false)}
              className="absolute right-3 top-4 rounded-lg p-1.5 text-teal-100/70 hover:bg-white/10"
            >
              <X size={16} />
            </button>
            <NavBody pathname={pathname} onNavigate={() => setOpen(false)} />
          </aside>
        </div>
      ) : null}
    </>
  );
}
