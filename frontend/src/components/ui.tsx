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
  glass = true,
}: {
  children: ReactNode;
  className?: string;
  interactive?: boolean;
  glow?: boolean;
  glass?: boolean;
}) {
  return (
    <section
      className={clsx(
        "si-card-border rounded-[var(--radius-lg)] p-5 transition duration-300",
        glass ? "si-glass" : "border border-[var(--line)] bg-[var(--panel-solid)] shadow-[var(--shadow-soft)]",
        interactive &&
          "cursor-default hover:-translate-y-1 hover:shadow-[var(--shadow-lift)]",
        glow && "shadow-[var(--shadow-glow)]",
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
    <div className="relative mb-8 flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
      <div className="max-w-3xl">
        {eyebrow ? (
          <span className="mb-3 inline-flex items-center rounded-full border border-[var(--accent)]/20 bg-[var(--accent-soft)] px-3 py-1 text-[10px] font-bold uppercase tracking-[0.2em] text-[var(--accent)]">
            {eyebrow}
          </span>
        ) : null}
        <h1 className="font-[family-name:var(--font-display)] text-3xl tracking-tight text-[var(--ink)] sm:text-[2.35rem] sm:leading-tight">
          {title}
        </h1>
        {subtitle ? (
          <p className="mt-2.5 max-w-2xl text-sm leading-relaxed text-[var(--muted)] sm:text-[0.9375rem]">
            {subtitle}
          </p>
        ) : null}
        <div className="mt-4 h-px w-16 bg-gradient-to-r from-[var(--accent)] to-transparent" />
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function HeroBanner({
  title,
  subtitle,
  children,
  className,
}: {
  title: ReactNode;
  subtitle?: string;
  children?: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "si-card-border si-hero-gradient relative mb-8 overflow-hidden rounded-[var(--radius-lg)] border border-[var(--line)] p-6 sm:p-8",
        className
      )}
    >
      <div className="si-orb -left-16 -top-16 h-48 w-48 bg-teal-400/30" />
      <div className="si-orb -right-10 top-10 h-36 w-36 bg-orange-300/25 animation-delay-2000" />
      <div className="relative">
        <h2 className="font-[family-name:var(--font-display)] text-2xl tracking-tight text-[var(--ink)] sm:text-3xl">
          {title}
        </h2>
        {subtitle ? (
          <p className="mt-2 max-w-xl text-sm leading-relaxed text-[var(--muted)]">
            {subtitle}
          </p>
        ) : null}
        {children ? <div className="mt-6">{children}</div> : null}
      </div>
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
        <h2 className="font-[family-name:var(--font-display)] text-lg text-[var(--ink)] sm:text-xl">
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

export function SegmentedControl<T extends string>({
  options,
  value,
  onChange,
  className,
}: {
  options: Array<{ value: T; label: string }>;
  value: T;
  onChange: (v: T) => void;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "inline-flex rounded-xl border border-[var(--line)] bg-[var(--wash)]/80 p-1 backdrop-blur-sm",
        className
      )}
    >
      {options.map((opt) => (
        <button
          key={opt.value}
          type="button"
          onClick={() => onChange(opt.value)}
          className={clsx(
            "rounded-lg px-3 py-1.5 text-xs font-medium transition-all duration-200",
            value === opt.value
              ? "bg-white text-[var(--ink)] shadow-sm ring-1 ring-[var(--line)]"
              : "text-[var(--muted)] hover:text-[var(--ink)]"
          )}
        >
          {opt.label}
        </button>
      ))}
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
  spark,
}: {
  label: string;
  value: string;
  hint?: string;
  icon?: LucideIcon;
  tone?: "default" | "accent" | "amber" | "rose" | "emerald";
  trend?: "up" | "down" | "flat";
  spark?: number[];
}) {
  const accents = {
    default: "from-white/90 via-white/70 to-[var(--wash)]",
    accent: "from-teal-50/90 via-white/80 to-teal-50/30",
    amber: "from-orange-50/90 via-white/80 to-orange-50/30",
    rose: "from-rose-50/80 via-white/80 to-rose-50/20",
    emerald: "from-emerald-50/90 via-white/80 to-emerald-50/30",
  };

  const iconBg = {
    default: "from-slate-500 to-slate-600",
    accent: "from-teal-600 to-teal-500",
    amber: "from-orange-600 to-amber-500",
    rose: "from-rose-600 to-rose-500",
    emerald: "from-emerald-600 to-emerald-500",
  };

  return (
    <div
      className={clsx(
        "si-card-border group relative overflow-hidden rounded-[var(--radius-lg)] bg-gradient-to-br p-4 shadow-[var(--shadow-soft)] transition duration-300 hover:-translate-y-1 hover:shadow-[var(--shadow-lift)] sm:p-5",
        accents[tone]
      )}
    >
      <div className="pointer-events-none absolute -right-8 -top-8 h-24 w-24 rounded-full bg-[var(--accent)]/5 blur-2xl transition group-hover:bg-[var(--accent)]/10" />

      <div className="relative flex items-start justify-between gap-3">
        <p className="text-[10px] font-bold uppercase tracking-[0.16em] text-[var(--muted)]">
          {label}
        </p>
        {Icon ? (
          <span
            className={clsx(
              "inline-flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-br text-white shadow-md",
              iconBg[tone]
            )}
          >
            <Icon size={15} strokeWidth={2.2} />
          </span>
        ) : null}
      </div>

      <p className="relative mt-3 font-[family-name:var(--font-display)] text-[1.65rem] leading-none tracking-tight text-[var(--ink)] sm:text-[1.85rem]">
        {value}
      </p>

      {spark && spark.length > 1 ? (
        <svg
          viewBox={`0 0 ${spark.length - 1} 24`}
          className="relative mt-3 h-6 w-full opacity-60"
          preserveAspectRatio="none"
        >
          <polyline
            fill="none"
            stroke="var(--accent)"
            strokeWidth="1.5"
            strokeLinecap="round"
            strokeLinejoin="round"
            points={spark
              .map((v, i) => {
                const max = Math.max(...spark);
                const min = Math.min(...spark);
                const range = max - min || 1;
                const y = 22 - ((v - min) / range) * 18;
                return `${i},${y}`;
              })
              .join(" ")}
          />
        </svg>
      ) : null}

      {(hint || trend) && (
        <div className="relative mt-2 flex flex-wrap items-center gap-2 text-xs text-[var(--muted)]">
          {trend ? (
            <span
              className={clsx(
                "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-bold uppercase tracking-wide",
                trend === "up" && "bg-emerald-100/90 text-emerald-800",
                trend === "down" && "bg-rose-100/90 text-rose-800",
                trend === "flat" && "bg-stone-100/90 text-stone-600"
              )}
            >
              {trend === "up" ? "↑" : trend === "down" ? "↓" : "→"} {trend}
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
  const gradients = {
    teal: "from-teal-600 via-teal-500 to-emerald-500",
    amber: "from-orange-600 via-amber-500 to-orange-400",
    slate: "from-slate-700 via-slate-600 to-slate-500",
    rose: "from-rose-600 via-rose-500 to-pink-500",
  };

  return (
    <Link
      href={href}
      className="si-card-border group relative flex h-full flex-col overflow-hidden rounded-[var(--radius-lg)] si-glass p-5 transition duration-300 hover:-translate-y-1.5 hover:shadow-[var(--shadow-glow)]"
    >
      <div className="absolute inset-0 bg-gradient-to-br from-[var(--accent)]/0 to-[var(--accent)]/5 opacity-0 transition group-hover:opacity-100" />
      <div className="relative flex items-start justify-between gap-3">
        <span
          className={clsx(
            "inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-gradient-to-br shadow-lg transition group-hover:scale-110 group-hover:shadow-xl",
            gradients[accent]
          )}
        >
          <Icon size={19} className="text-white" strokeWidth={2} />
        </span>
        <span className="flex h-8 w-8 items-center justify-center rounded-full border border-[var(--line)] bg-white/80 text-sm text-[var(--muted)] transition group-hover:border-[var(--accent)]/30 group-hover:text-[var(--accent)]">
          ↗
        </span>
      </div>
      <h3 className="relative mt-5 font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
        {title}
      </h3>
      <p className="relative mt-1.5 flex-1 text-sm leading-relaxed text-[var(--muted)]">
        {description}
      </p>
      {meta ? (
        <p className="relative mt-4 border-t border-[var(--line)] pt-3 text-[11px] font-semibold uppercase tracking-wide text-[var(--accent)]">
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
    neutral: "bg-stone-100/90 text-stone-700 ring-1 ring-stone-200/60",
    teal: "bg-teal-100/90 text-teal-800 ring-1 ring-teal-200/60",
    amber: "bg-orange-100/90 text-orange-900 ring-1 ring-orange-200/60",
    rose: "bg-rose-100/90 text-rose-800 ring-1 ring-rose-200/60",
    emerald: "bg-emerald-100/90 text-emerald-800 ring-1 ring-emerald-200/60",
    critical: "bg-gradient-to-r from-rose-600 to-rose-500 text-white shadow-sm",
  };
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-full px-2.5 py-1 text-[10px] font-bold uppercase tracking-wide",
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
        "inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-semibold transition-all duration-200 disabled:opacity-50",
        variant === "primary" &&
          "bg-gradient-to-r from-[var(--accent)] to-teal-600 text-white shadow-md shadow-teal-900/15 hover:shadow-lg hover:shadow-teal-900/20 active:scale-[0.98]",
        variant === "secondary" &&
          "border border-[var(--line)] bg-white/90 text-[var(--ink)] backdrop-blur-sm hover:border-[var(--accent)]/25 hover:bg-white",
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
        "w-full rounded-xl border border-[var(--line)] bg-white/90 px-3.5 py-2.5 text-sm text-[var(--ink)] outline-none backdrop-blur-sm transition placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/15",
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
        "w-full rounded-xl border border-[var(--line)] bg-white/90 px-3.5 py-2.5 text-sm text-[var(--ink)] outline-none backdrop-blur-sm transition focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/15",
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
        "w-full rounded-xl border border-[var(--line)] bg-white/90 px-3.5 py-2.5 text-sm text-[var(--ink)] outline-none backdrop-blur-sm transition placeholder:text-[var(--muted)] focus:border-[var(--accent)] focus:ring-2 focus:ring-[var(--accent)]/15",
        props.className
      )}
    />
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="si-card-border rounded-[var(--radius-lg)] border border-dashed border-[var(--line-strong)] bg-[var(--wash)]/60 px-6 py-14 text-center backdrop-blur-sm">
      <div className="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-[var(--accent)]/10 to-[var(--amber)]/10 text-2xl text-[var(--muted)] ring-1 ring-[var(--line)]">
        ◌
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
    <div className="flex min-h-56 flex-col items-center justify-center gap-4">
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 animate-spin rounded-full border-2 border-[var(--line)] border-t-[var(--accent)]" />
        <div className="absolute inset-1 animate-pulse rounded-full bg-[var(--accent)]/10" />
      </div>
      <p className="text-sm font-medium text-[var(--muted)]">{label}</p>
    </div>
  );
}

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div className="mb-4 rounded-xl border border-rose-200/80 bg-gradient-to-r from-rose-50 to-white px-4 py-3 text-sm text-rose-700 shadow-sm">
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

export function BentoGrid({
  children,
  className,
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div
      className={clsx(
        "si-stagger grid auto-rows-fr gap-4 sm:grid-cols-2 xl:grid-cols-4",
        className
      )}
    >
      {children}
    </div>
  );
}
