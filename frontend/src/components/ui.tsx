"use client";

import clsx from "clsx";
import type { LucideIcon } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";

export function Panel({
  children,
  className,
  interactive = false,
  glow = false,
}: {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
  glow?: boolean;
}) {
  return (
    <section
      className={clsx(
        "rounded-[var(--radius)] border border-[var(--line)] bg-[var(--panel)] p-5 shadow-[var(--shadow-soft)] transition duration-200",
        interactive &&
          "hover:-translate-y-0.5 hover:border-[var(--line-strong)] hover:shadow-[var(--shadow-lift)]",
        glow && "ring-1 ring-[var(--accent)]/10",
        className
      )}
    >
      {children}
    </section>
  );
}

export function PageHeader({
  title,
  subtitle,
  action,
  eyebrow,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
  eyebrow?: string;
}) {
  return (
    <div className="mb-7 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-3xl">
        {eyebrow ? (
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--accent)]">
            {eyebrow}
          </p>
        ) : null}
        <h1 className="font-[family-name:var(--font-display)] text-3xl tracking-tight text-[var(--ink)] sm:text-4xl">
          {title}
        </h1>
        {subtitle ? (
          <p className="mt-2 max-w-2xl text-sm leading-relaxed text-[var(--muted)]">
            {subtitle}
          </p>
        ) : null}
      </div>
      {action}
    </div>
  );
}

export function SectionTitle({
  title,
  subtitle,
  action,
}: {
  title: string;
  subtitle?: string;
  action?: ReactNode;
}) {
  return (
    <div className="mb-4 flex flex-wrap items-end justify-between gap-3">
      <div>
        <h2 className="font-[family-name:var(--font-display)] text-xl text-[var(--ink)]">
          {title}
        </h2>
        {subtitle ? (
          <p className="mt-0.5 text-xs text-[var(--muted)]">{subtitle}</p>
        ) : null}
      </div>
      {action}
    </div>
  );
}

export function KpiCard({
  label,
  value,
  hint,
  icon: Icon,
  tone = "default",
  trend,
}: {
  label: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
  tone?: "default" | "accent" | "amber" | "rose" | "emerald";
  trend?: "up" | "down" | "flat";
}) {
  const tones = {
    default: "from-white to-[var(--wash)]",
    accent: "from-teal-50/80 to-white",
    amber: "from-orange-50/80 to-white",
    rose: "from-rose-50/70 to-white",
    emerald: "from-emerald-50/80 to-white",
  };

  return (
    <div
      className={clsx(
        "group relative overflow-hidden rounded-[var(--radius)] border border-[var(--line)] bg-gradient-to-br p-4 shadow-[var(--shadow-soft)] transition duration-200 hover:-translate-y-0.5 hover:shadow-[var(--shadow-lift)]",
        tones[tone]
      )}
    >
      <div className="pointer-events-none absolute -right-6 -top-6 h-20 w-20 rounded-full bg-[var(--accent)]/5 transition group-hover:scale-125" />
      <div className="relative flex items-start justify-between gap-3">
        <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-[var(--muted)]">
          {label}
        </p>
        {Icon ? (
          <span className="rounded-xl bg-white/80 p-1.5 text-[var(--accent)] shadow-sm ring-1 ring-[var(--line)]">
            <Icon size={14} />
          </span>
        ) : null}
      </div>
      <p className="relative mt-3 font-[family-name:var(--font-display)] text-2xl tracking-tight text-[var(--ink)] sm:text-[1.7rem]">
        {value}
      </p>
      {(hint || trend) && (
        <div className="relative mt-2 flex items-center gap-2 text-xs text-[var(--muted)]">
          {trend ? (
            <span
              className={clsx(
                "inline-flex items-center rounded-full px-1.5 py-0.5 text-[10px] font-semibold uppercase",
                trend === "up" && "bg-emerald-100 text-emerald-800",
                trend === "down" && "bg-rose-100 text-rose-800",
                trend === "flat" && "bg-stone-100 text-stone-600"
              )}
            >
              {trend === "up" ? "▲" : trend === "down" ? "▼" : "●"} {trend}
            </span>
          ) : null}
          {hint ? <span className="truncate">{hint}</span> : null}
        </div>
      )}
    </div>
  );
}

export function FeatureCard({
  href,
  title,
  description,
  icon: Icon,
  meta,
  accent = "teal",
}: {
  href: string;
  title: string;
  description: string;
  icon: LucideIcon;
  meta?: string;
  accent?: "teal" | "amber" | "slate" | "rose";
}) {
  const accents = {
    teal: "bg-teal-600 text-white",
    amber: "bg-orange-600 text-white",
    slate: "bg-slate-700 text-white",
    rose: "bg-rose-600 text-white",
  };

  return (
    <Link
      href={href}
      className="group relative flex h-full flex-col overflow-hidden rounded-[var(--radius)] border border-[var(--line)] bg-[var(--panel)] p-5 shadow-[var(--shadow-soft)] transition duration-200 hover:-translate-y-1 hover:border-[var(--line-strong)] hover:shadow-[var(--shadow-lift)]"
    >
      <div className="absolute inset-x-0 top-0 h-1 origin-left scale-x-0 bg-gradient-to-r from-[var(--accent)] to-[var(--amber)] transition duration-300 group-hover:scale-x-100" />
      <div className="flex items-start justify-between gap-3">
        <span
          className={clsx(
            "inline-flex h-10 w-10 items-center justify-center rounded-2xl shadow-sm transition group-hover:scale-105",
            accents[accent]
          )}
        >
          <Icon size={18} />
        </span>
        <span className="text-lg text-[var(--muted)] transition group-hover:translate-x-0.5 group-hover:text-[var(--accent)]">
          →
        </span>
      </div>
      <h3 className="mt-4 font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
        {title}
      </h3>
      <p className="mt-1.5 flex-1 text-sm leading-relaxed text-[var(--muted)]">
        {description}
      </p>
      {meta ? (
        <p className="mt-4 border-t border-[var(--line)] pt-3 text-xs font-medium text-[var(--accent)]">
          {meta}
        </p>
      ) : null}
    </Link>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "neutral" | "teal" | "amber" | "rose" | "emerald" | "critical";
}) {
  const tones = {
    neutral: "bg-stone-100 text-stone-700",
    teal: "bg-teal-100 text-teal-800",
    amber: "bg-orange-100 text-orange-900",
    rose: "bg-rose-100 text-rose-800",
    emerald: "bg-emerald-100 text-emerald-800",
    critical: "bg-rose-600 text-white",
  };
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-wide",
        tones[tone]
      )}
    >
      {children}
    </span>
  );
}

export function Button({
  children,
  variant = "primary",
  className,
  ...props
}: React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "secondary";
}) {
  return (
    <button
      className={clsx(
        "inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-medium transition disabled:opacity-50",
        variant === "primary" &&
          "bg-[var(--accent)] text-white shadow-sm hover:bg-[var(--accent-strong)] hover:shadow-md active:scale-[0.98]",
        variant === "secondary" &&
          "border border-[var(--line)] bg-white text-[var(--ink)] hover:border-[var(--line-strong)] hover:bg-[var(--wash)]",
        variant === "ghost" &&
          "text-[var(--muted)] hover:bg-[var(--wash)] hover:text-[var(--ink)]",
        className
      )}
      {...props}
    >
      {children}
    </button>
  );
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={clsx(
        "w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 text-sm text-[var(--ink)] outline-none transition placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20",
        props.className
      )}
    />
  );
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={clsx(
        "w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 text-sm text-[var(--ink)] outline-none transition focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20",
        props.className
      )}
    />
  );
}

export function TextArea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      {...props}
      className={clsx(
        "w-full rounded-xl border border-[var(--line)] bg-white px-3 py-2.5 text-sm text-[var(--ink)] outline-none transition placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/20",
        props.className
      )}
    />
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-[var(--radius)] border border-dashed border-[var(--line-strong)] bg-[var(--wash)]/80 px-6 py-12 text-center">
      <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-[var(--muted)] shadow-sm ring-1 ring-[var(--line)]">
        ∅
      </div>
      <p className="font-[family-name:var(--font-display)] text-xl text-[var(--ink)]">
        {title}
      </p>
      <p className="mx-auto mt-2 max-w-md text-sm leading-relaxed text-[var(--muted)]">
        {body}
      </p>
    </div>
  );
}

export function LoadingBlock({ label = "Loading..." }: { label?: string }) {
  return (
    <div className="flex min-h-48 flex-col items-center justify-center gap-3">
      <div className="h-8 w-8 animate-spin rounded-full border-2 border-[var(--line)] border-t-[var(--accent)]" />
      <p className="text-sm text-[var(--muted)]">{label}</p>
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
      {message}
    </div>
  );
}

export function DataGrid({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={clsx("si-stagger grid gap-4", className)}>{children}</div>
  );
}
