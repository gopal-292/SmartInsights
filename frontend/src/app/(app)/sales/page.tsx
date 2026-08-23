"use client";

import { useEffect, useState } from "react";
import { MapPin, Package, Trophy } from "lucide-react";
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
import { inr } from "@/lib/format";

type SalesData = {
  monthly: Array<{ period: string; value: number }>;
  by_product: Array<{ product: string; revenue: number; units: number }>;
  by_region: Array<{ region: string; revenue: number }>;
  top_product?: { product: string; revenue: number; units: number };
  message?: string;
};

export default function SalesPage() {
  const [data, setData] = useState<SalesData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [focus, setFocus] = useState<"product" | "region">("product");

  useEffect(() => {
    api<SalesData>("/analytics/sales")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBanner message={error} />;
  if (!data || data.message)
    return (
      <EmptyState
        title="No sales data"
        body="Upload a sales CSV/Excel file to analyze performance."
      />
    );

  const totalRevenue = (data.by_product || []).reduce((s, p) => s + p.revenue, 0);

  return (
    <div>
      <PageHeader
        eyebrow="Analytics"
        title="Sales Analytics"
        subtitle="Track revenue trends, top products, and regional performance in one grid."
      />

      <DataGrid className="mb-6 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Tracked Months"
          value={String(data.monthly?.length || 0)}
          tone="accent"
        />
        <KpiCard
          label="Product Lines"
          value={String(data.by_product?.length || 0)}
          icon={Package}
        />
        <KpiCard
          label="Regions"
          value={String(data.by_region?.length || 0)}
          icon={MapPin}
        />
        <KpiCard
          label="Top Product"
          value={data.top_product?.product || "—"}
          hint={data.top_product ? inr(data.top_product.revenue) : undefined}
          icon={Trophy}
          tone="amber"
        />
      </DataGrid>

      <div className="grid gap-4 xl:grid-cols-5">
        <Panel className="xl:col-span-3" interactive>
          <SectionTitle title="Monthly sales" subtitle="Revenue over time" />
          <TrendChart data={data.monthly || []} name="Revenue" />
        </Panel>

        <Panel className="xl:col-span-2" interactive glow>
          <SectionTitle title="Leaderboard" subtitle="Tap a product for detail" />
          <div className="si-scroll max-h-80 space-y-2 overflow-y-auto pr-1">
            {(data.by_product || []).slice(0, 8).map((p, idx) => {
              const share = totalRevenue ? (p.revenue / totalRevenue) * 100 : 0;
              return (
                <div
                  key={p.product}
                  className="rounded-xl border border-[var(--line)] bg-[var(--wash)]/60 px-3 py-2.5 transition hover:bg-white"
                >
                  <div className="flex items-center justify-between gap-2 text-sm">
                    <p className="truncate font-medium">
                      <span className="mr-2 text-[var(--muted)]">#{idx + 1}</span>
                      {p.product}
                    </p>
                    <p className="shrink-0 font-medium">{inr(p.revenue)}</p>
                  </div>
                  <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-white">
                    <div
                      className="h-full rounded-full bg-[var(--accent)] transition-all"
                      style={{ width: `${Math.min(share, 100)}%` }}
                    />
                  </div>
                  <p className="mt-1 text-[11px] text-[var(--muted)]">
                    {share.toFixed(1)}% of revenue · {p.units} units
                  </p>
                </div>
              );
            })}
          </div>
        </Panel>
      </div>

      <Panel className="mt-4" interactive>
        <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
          <SectionTitle
            title="Breakdown"
            subtitle="Switch between product and region views"
          />
          <div className="flex rounded-xl border border-[var(--line)] bg-[var(--wash)] p-1">
            {(["product", "region"] as const).map((key) => (
              <button
                key={key}
                type="button"
                onClick={() => setFocus(key)}
                className={
                  focus === key
                    ? "rounded-lg bg-white px-3 py-1.5 text-xs font-medium shadow-sm"
                    : "rounded-lg px-3 py-1.5 text-xs text-[var(--muted)]"
                }
              >
                By {key}
              </button>
            ))}
          </div>
        </div>
        {focus === "product" ? (
          <BarBlock
            data={data.by_product || []}
            xKey="product"
            yKey="revenue"
            name="Revenue"
            color="#0d7377"
          />
        ) : (
          <BarBlock
            data={data.by_region || []}
            xKey="region"
            yKey="revenue"
            name="Revenue"
            color="#c45c26"
          />
        )}
      </Panel>
    </div>
  );
}
