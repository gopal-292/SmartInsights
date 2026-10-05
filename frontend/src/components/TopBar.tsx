"use client";

import clsx from "clsx";
import { Bell, Search, Sparkles } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";

export function TopBar() {
  const pathname = usePathname();
  const { user } = useAuth();
  const initials = (user?.full_name || "U")
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <header className="mb-6 flex flex-wrap items-center justify-between gap-3 rounded-[var(--radius-lg)] border border-[var(--line)] bg-[var(--panel)]/85 px-4 py-2.5 shadow-[var(--shadow-soft)] backdrop-blur-xl sm:px-5">
      <div className="flex min-w-0 flex-1 items-center gap-2 rounded-xl border border-[var(--line)] bg-white/70 px-3 py-2 text-[var(--muted)] sm:max-w-xs md:max-w-sm lg:max-w-md">
        <Search size={14} className="shrink-0 opacity-45" />
        <span className="truncate text-xs">Quick search modules...</span>
      </div>

      <div className="flex items-center gap-2 sm:gap-2.5">
        <Link
          href="/insights"
          className={clsx(
            "inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition-all",
            pathname === "/insights"
              ? "bg-gradient-to-r from-[var(--accent)] to-teal-600 text-white shadow-[var(--shadow-glow)]"
              : "border border-[var(--line)] bg-white/80 text-[var(--ink)] hover:border-[var(--accent)]/30 hover:shadow-sm"
          )}
        >
          <Sparkles size={13} />
          <span className="hidden sm:inline">AI Insights</span>
        </Link>

        <Link
          href="/assistant"
          className={clsx(
            "hidden rounded-xl border px-3 py-2 text-xs font-semibold transition sm:inline-flex",
            pathname === "/assistant"
              ? "border-[var(--accent)]/30 bg-[var(--accent-soft)] text-[var(--accent)]"
              : "border-[var(--line)] bg-white/80 text-[var(--muted)] hover:text-[var(--ink)]"
          )}
        >
          Assistant
        </Link>

        <button
          type="button"
          aria-label="Notifications"
          className="rounded-xl border border-[var(--line)] bg-white/80 p-2 text-[var(--muted)] transition hover:border-[var(--accent)]/20 hover:text-[var(--accent)]"
        >
          <Bell size={16} />
        </button>

        <div className="flex items-center gap-2 rounded-xl border border-[var(--line)] bg-white/80 py-1 pl-1 pr-2.5 sm:pr-3">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-gradient-to-br from-[var(--accent)] to-teal-500 text-[11px] font-bold text-white shadow-sm">
            {initials}
          </span>
          <span className="hidden max-w-[100px] truncate text-xs font-semibold text-[var(--ink)] md:block">
            {user?.full_name?.split(" ")[0]}
          </span>
        </div>
      </div>
    </header>
  );
}
