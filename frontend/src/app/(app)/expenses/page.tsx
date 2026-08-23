"use client";

import { useEffect, useState } from "react";
import { PieChart as PieIcon, TrendingDown, Wallet } from "lucide-react";
import { BarBlock, TrendChart } from "@/components/Charts";
import {
  DataGrid,
  EmptyState,
  ErrorBanner,
  KpiCard,
  LoadingBlock,
  PageHeader,
  Panel,
  SectionTitle,
} from "@/components/ui";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";

type ExpenseData = {
  total_expenses?: number;
  expense_growth?: number;
  monthly: Array<{ period: string; value: number }>;
  by_category: Array<{ category: string; amount: number }>;
  highest_category?: { category: string; amount: number };
  message?: string;
};

export default function ExpensesPage() {
  const [data, setData] = useState<ExpenseData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    api<ExpenseData>("/analytics/expenses")
      .then((res) => {
        setData(res);
        if (res.highest_category) setSelected(res.highest_category.category);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBanner message={error} />;
  if (!data || data.message)
    return (
      <EmptyState title="No expense data" body="Upload an expenses CSV/Excel file." />
    );

  const total = (data.by_category || []).reduce((s, c) => s + c.amount, 0);
  const active = (data.by_category || []).find((c) => c.category === selected);

  return (
    <div>
      <PageHeader
        eyebrow="Analytics"
        title="Expense Analysis"
        subtitle="See where money goes — click a category tile to inspect its share."
      />

      <DataGrid className="mb-6 sm:grid-cols-3">
        <KpiCard
          label="Total Expenses"
          value={inr(data.total_expenses)}
          icon={Wallet}
          tone="amber"
        />
        <KpiCard
          label="Expense Growth"
          value={pct(data.expense_growth)}
          icon={TrendingDown}
          tone={(data.expense_growth || 0) > 10 ? "rose" : "default"}
          trend={(data.expense_growth || 0) > 0 ? "up" : "down"}
        />
        <KpiCard
          label="Top Category"
          value={data.highest_category?.category || "—"}
          hint={data.highest_category ? inr(data.highest_category.amount) : undefined}
          icon={PieIcon}
        />
      </DataGrid>

      <DataGrid className="mb-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
        {(data.by_category || []).map((c) => {
          const share = total ? (c.amount / total) * 100 : 0;
          const isActive = selected === c.category;
          return (
            <button
              key={c.category}
              type="button"
              onClick={() => setSelected(c.category)}
              className={
                isActive
                  ? "rounded-[var(--radius)] border border-[var(--accent)] bg-teal-50/70 p-4 text-left shadow-[var(--shadow-soft)] transition"
                  : "rounded-[var(--radius)] border border-[var(--line)] bg-[var(--panel)] p-4 text-left shadow-[var(--shadow-soft)] transition hover:-translate-y-0.5 hover:shadow-[var(--shadow-lift)]"
              }
            >
              <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
                {share.toFixed(1)}% of spend
              </p>
              <p className="mt-2 font-[family-name:var(--font-display)] text-lg">
                {c.category}
              </p>
              <p className="mt-1 text-sm font-medium">{inr(c.amount)}</p>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--wash)]">
                <div
                  className="h-full rounded-full bg-[var(--amber)]"
                  style={{ width: `${Math.min(share, 100)}%` }}
                />
              </div>
            </button>
          );
        })}
      </DataGrid>

      {active ? (
        <Panel className="mb-4" glow>
          <p className="text-sm text-[var(--muted)]">Selected category</p>
          <p className="mt-1 font-[family-name:var(--font-display)] text-2xl">
            {active.category}
          </p>
          <p className="mt-1 text-sm">
            {inr(active.amount)} ·{" "}
            {total ? ((active.amount / total) * 100).toFixed(1) : 0}% of total expenses
          </p>
        </Panel>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel interactive>
          <SectionTitle title="Monthly expenses" />
          <TrendChart data={data.monthly || []} name="Expenses" color="#c45c26" />
        </Panel>
        <Panel interactive>
          <SectionTitle title="By category" />
          <BarBlock
            data={data.by_category || []}
            xKey="category"
            yKey="amount"
            name="Amount"
          />
        </Panel>
      </div>
    </div>
  );
}
