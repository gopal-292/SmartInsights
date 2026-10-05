"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { Sparkles, Zap } from "lucide-react";
import { Button, ErrorBanner, Input, Panel } from "@/components/ui";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      await login(email, password);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="relative flex min-h-screen">
      <div className="si-mesh si-grid-bg absolute inset-0" />
      <div className="relative hidden w-1/2 flex-col justify-between border-r border-[var(--line)] bg-gradient-to-br from-[var(--sidebar)] via-[#0a3530] to-[#061f1c] p-12 lg:flex">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-gradient-to-br from-teal-400 to-teal-600 shadow-lg">
            <Zap size={20} className="text-white" fill="white" />
          </span>
          <span className="font-[family-name:var(--font-display)] text-2xl text-white">
            SmartInsights
          </span>
        </div>
        <div>
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-teal-300/60">
            Business Intelligence
          </p>
          <h1 className="mt-4 font-[family-name:var(--font-display)] text-4xl leading-tight text-white">
            Analytics, forecasting & AI — unified
          </h1>
          <p className="mt-4 max-w-md text-sm leading-relaxed text-teal-100/60">
            Upload your data once. Get KPIs, ML predictions, anomaly detection,
            and prioritised recommendations in a single workspace.
          </p>
        </div>
        <p className="text-xs text-teal-100/40">© SmartInsights · AI Business Analyzer</p>
      </div>

      <div className="relative flex flex-1 items-center justify-center px-4 py-12">
        <Panel className="w-full max-w-md" glow glass>
          <span className="mb-4 inline-flex items-center gap-1.5 rounded-full bg-[var(--accent-soft)] px-2.5 py-1 text-[10px] font-bold uppercase tracking-wider text-[var(--accent)]">
            <Sparkles size={11} /> Sign in
          </span>
          <h2 className="font-[family-name:var(--font-display)] text-2xl text-[var(--ink)]">
            Welcome back
          </h2>
          <p className="mt-1 text-sm text-[var(--muted)]">
            Access your business workspace
          </p>
          {error ? (
            <div className="mt-4">
              <ErrorBanner message={error} />
            </div>
          ) : null}
          <form onSubmit={onSubmit} className="mt-6 space-y-4">
            <div>
              <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-wide text-[var(--muted)]">
                Email
              </label>
              <Input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@business.com"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-[11px] font-bold uppercase tracking-wide text-[var(--muted)]">
                Password
              </label>
              <Input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
              />
            </div>
            <Button className="w-full" disabled={loading}>
              {loading ? "Signing in..." : "Sign in"}
            </Button>
          </form>
          <p className="mt-5 text-center text-sm text-[var(--muted)]">
            New here?{" "}
            <Link href="/register" className="font-semibold text-[var(--accent)] hover:underline">
              Create an account
            </Link>
          </p>
        </Panel>
      </div>
    </main>
  );
}
