"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Button } from "@/components/ui";
import { useAuth } from "@/lib/auth";

export default function HomePage() {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && user) router.replace("/dashboard");
  }, [loading, user, router]);

  return (
    <main className="relative min-h-screen overflow-hidden">
      <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(15,118,110,0.16),transparent_35%),radial-gradient(circle_at_80%_10%,rgba(194,65,12,0.12),transparent_30%),linear-gradient(160deg,#f7faf8,#e7f1ec_45%,#f4efe8)]" />
      <div className="relative mx-auto flex min-h-screen max-w-6xl flex-col justify-center px-6 py-16">
        <p className="font-[family-name:var(--font-display)] text-5xl tracking-tight text-[var(--ink)] sm:text-6xl">
          SmartInsights
        </p>
        <h1 className="mt-4 max-w-2xl text-2xl font-medium text-[var(--ink)] sm:text-3xl">
          AI-powered business analysis for SMEs
        </h1>
        <p className="mt-4 max-w-xl text-base leading-relaxed text-[var(--muted)]">
          Upload sales, expenses, inventory, and reviews. Get KPIs, forecasts,
          anomaly alerts, sentiment analysis, and actionable recommendations.
        </p>
        <div className="mt-8 flex flex-wrap gap-3">
          <Link href="/register">
            <Button>Create account</Button>
          </Link>
          <Link href="/login">
            <Button variant="secondary">Sign in</Button>
          </Link>
        </div>
      </div>
    </main>
  );
}
