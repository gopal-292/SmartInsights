"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import {
  ArrowRight,
  BarChart3,
  Bot,
  Sparkles,
  TrendingUp,
  Upload,
  Zap,
} from "lucide-react";
import { Button } from "@/components/ui";
import { useAuth } from "@/lib/auth";

const features = [
  {
    icon: BarChart3,
    title: "Live KPI Dashboard",
    desc: "Revenue, profit, margins and growth in one command center.",
  },
  {
    icon: TrendingUp,
    title: "ML Forecasting",
    desc: "Walk-forward model selection with accuracy scores.",
  },
  {
    icon: Sparkles,
    title: "AI Recommendations",
    desc: "Prioritised actions based on your market situation.",
  },
  {
    icon: Bot,
    title: "RAG Assistant",
    desc: "Ask questions over analytics and uploaded documents.",
  },
];

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="si-mesh si-grid-bg absolute inset-0" />
      <div className="si-orb left-[10%] top-[15%] h-72 w-72 bg-teal-400/25" />
      <div className="si-orb right-[5%] top-[30%] h-64 w-64 bg-orange-300/20" />

      <div className="relative mx-auto max-w-6xl px-6 py-12 sm:py-20">
        <nav className="mb-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-teal-500 to-teal-600 text-white shadow-lg shadow-teal-900/25">
              <Zap size={18} fill="white" />
            </span>
            <span className="font-[family-name:var(--font-display)] text-xl text-[var(--ink)]">
              SmartInsights
            </span>
          </div>
          <div className="flex gap-2">
            <Link href="/login">
              <Button variant="ghost">Sign in</Button>
            </Link>
            <Link href="/register">
              <Button>Get started</Button>
            </Link>
          </div>
        </nav>

        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div>
            <span className="mb-4 inline-flex items-center gap-2 rounded-full border border-[var(--accent)]/20 bg-[var(--accent-soft)] px-3 py-1 text-[11px] font-bold uppercase tracking-[0.18em] text-[var(--accent)]">
              <Sparkles size={12} /> AI-Powered Analytics
            </span>
            <h1 className="font-[family-name:var(--font-display)] text-4xl leading-[1.1] tracking-tight text-[var(--ink)] sm:text-5xl lg:text-[3.25rem]">
              Turn business data into{" "}
              <span className="si-gradient-text">decisions that scale</span>
            </h1>
            <p className="mt-5 max-w-lg text-base leading-relaxed text-[var(--muted)] sm:text-lg">
              Upload sales, expenses, inventory, and reviews. Get KPIs, ML
              forecasts, anomaly alerts, sentiment analysis, and actionable AI
              recommendations — all in one workspace.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/register">
                <Button className="gap-2 px-6">
                  Create free account <ArrowRight size={16} />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="secondary">Sign in</Button>
              </Link>
            </div>

            <div className="mt-10 flex flex-wrap gap-6 border-t border-[var(--line)] pt-8">
              {[
                { n: "6+", l: "ML models" },
                { n: "24mo", l: "Forecast depth" },
                { n: "RAG", l: "Document AI" },
              ].map((s) => (
                <div key={s.l}>
                  <p className="font-[family-name:var(--font-display)] text-2xl text-[var(--ink)]">
                    {s.n}
                  </p>
                  <p className="text-xs text-[var(--muted)]">{s.l}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="si-stagger grid gap-3 sm:grid-cols-2">
            {features.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="si-card-border si-glass rounded-[var(--radius-lg)] p-5 transition hover:-translate-y-1 hover:shadow-[var(--shadow-glow)]"
              >
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-[var(--accent)] to-teal-500 text-white shadow-md">
                  <Icon size={18} />
                </span>
                <h3 className="mt-4 font-[family-name:var(--font-display)] text-lg text-[var(--ink)]">
                  {title}
                </h3>
                <p className="mt-1.5 text-sm leading-relaxed text-[var(--muted)]">
                  {desc}
                </p>
              </div>
            ))}
            <div className="si-card-border si-hero-gradient col-span-full flex items-center gap-4 rounded-[var(--radius-lg)] p-5 sm:col-span-2">
              <Upload size={24} className="shrink-0 text-[var(--accent)]" />
              <div>
                <p className="font-medium text-[var(--ink)]">
                  Start with sample data
                </p>
                <p className="text-sm text-[var(--muted)]">
                  CSV files in <code className="text-[var(--accent)]">backend/sample_data/</code>
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
