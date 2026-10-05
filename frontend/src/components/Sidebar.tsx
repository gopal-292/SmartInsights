"use client";

import clsx from "clsx";
import {
  AlertTriangle,
  BarChart3,
  Bot,
  Building2,
  ChevronRight,
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
  Zap,
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
      <div className="border-b border-white/[0.06] px-4 py-5">
        <Link href="/dashboard" onClick={onNavigate} className="group flex items-center gap-3">
          <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 shadow-lg shadow-teal-900/40 ring-1 ring-white/10">
            <Zap size={18} className="text-white" fill="white" />
          </span>
          <div>
            <p className="font-[family-name:var(--font-display)] text-lg tracking-tight text-white">
              SmartInsights
            </p>
            <p className="text-[10px] font-medium uppercase tracking-[0.14em] text-teal-200/50">
              Business AI
            </p>
          </div>
        </Link>
      </div>

      <nav className="si-scroll flex-1 space-y-5 overflow-y-auto px-3 py-4">
        {groups.map((group) => (
          <div key={group.label}>
            <p className="mb-2 px-3 text-[9px] font-bold uppercase tracking-[0.2em] text-teal-100/35">
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
                      "group flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-all duration-200",
                      active
                        ? "bg-gradient-to-r from-teal-500/20 to-teal-400/5 text-white shadow-inner ring-1 ring-teal-400/20"
                        : "text-teal-100/60 hover:bg-white/[0.06] hover:text-white"
                    )}
                  >
                    <span
                      className={clsx(
                        "flex h-8 w-8 items-center justify-center rounded-lg transition-all",
                        active
                          ? "bg-teal-400/25 text-teal-100 shadow-sm"
                          : "bg-white/[0.04] text-teal-100/50 group-hover:bg-white/[0.08] group-hover:text-teal-100"
                      )}
                    >
                      <Icon size={15} strokeWidth={active ? 2.2 : 1.8} />
                    </span>
                    <span className="flex-1">{label}</span>
                    {active ? (
                      <ChevronRight size={14} className="text-teal-300/80" />
                    ) : null}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div className="border-t border-white/[0.06] p-3">
        <div className="rounded-xl bg-gradient-to-br from-white/[0.08] to-white/[0.02] p-3 ring-1 ring-white/[0.06]">
          <div className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-emerald-600 text-xs font-bold text-white">
              {(user?.full_name || "U")
                .split(" ")
                .map((n) => n[0])
                .join("")
                .slice(0, 2)
                .toUpperCase()}
            </span>
            <div className="min-w-0 flex-1">
              <p className="truncate text-sm font-medium text-white">
                {user?.full_name}
              </p>
              <p className="truncate text-[11px] text-teal-100/45">{user?.email}</p>
            </div>
          </div>
          <button
            onClick={logout}
            className="mt-3 flex w-full items-center justify-center gap-2 rounded-lg border border-white/[0.08] bg-white/[0.04] py-2 text-xs font-medium text-teal-100/70 transition hover:bg-white/[0.08] hover:text-white"
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
      <aside className="si-glass-dark sticky top-0 hidden h-screen w-[17.5rem] shrink-0 flex-col border-r border-white/[0.06] lg:flex">
        <NavBody pathname={pathname} />
      </aside>

      <div className="sticky top-0 z-30 flex items-center justify-between border-b border-[var(--line)] bg-[var(--panel)]/95 px-4 py-3 backdrop-blur-xl lg:hidden">
        <div className="flex items-center gap-2">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-teal-500 to-teal-600 text-white">
            <Zap size={14} fill="white" />
          </span>
          <p className="font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
            SmartInsights
          </p>
        </div>
        <button
          type="button"
          aria-label="Open menu"
          onClick={() => setOpen(true)}
          className="rounded-xl border border-[var(--line)] bg-white/80 p-2.5 text-[var(--ink)]"
        >
          <Menu size={18} />
        </button>
      </div>

      {open ? (
        <div className="fixed inset-0 z-50 lg:hidden">
          <button
            type="button"
            aria-label="Close menu"
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={() => setOpen(false)}
          />
          <aside className="si-glass-dark absolute inset-y-0 left-0 flex w-[min(85vw,18rem)] flex-col shadow-2xl">
            <button
              type="button"
              aria-label="Close"
              onClick={() => setOpen(false)}
              className="absolute right-3 top-4 z-10 rounded-lg p-2 text-teal-100/70 hover:bg-white/10"
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
