"use client";

import { useEffect, useMemo, useState } from "react";
import { AlertTriangle, Boxes, PackageCheck } from "lucide-react";
import {
  Badge,
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

type Item = {
  product: string;
  current_stock: number;
  reorder_level: number;
  supplier: string;
  stock_value: number;
  status: string;
};

type InventoryData = {
  items: Item[];
  reorder_required: Array<{ product: string }>;
  overstocked: Array<{ product: string }>;
  total_stock_value: number;
  message?: string;
};

type Filter = "all" | "reorder" | "ok" | "overstock";

export default function InventoryPage() {
  const [data, setData] = useState<InventoryData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<Filter>("all");

  useEffect(() => {
    api<InventoryData>("/analytics/inventory")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const overstockNames = useMemo(
    () => new Set((data?.overstocked || []).map((o) => o.product)),
    [data]
  );

  const filtered = useMemo(() => {
    if (!data) return [];
    return data.items.filter((item) => {
      if (filter === "reorder") return item.status === "Reorder Required";
      if (filter === "ok")
        return item.status !== "Reorder Required" && !overstockNames.has(item.product);
      if (filter === "overstock") return overstockNames.has(item.product);
      return true;
    });
  }, [data, filter, overstockNames]);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBanner message={error} />;
  if (!data || data.message)
    return <EmptyState title="No inventory data" body="Upload an inventory CSV/Excel file." />;

  const filters: Array<{ key: Filter; label: string }> = [
    { key: "all", label: `All (${data.items.length})` },
    { key: "reorder", label: `Reorder (${data.reorder_required.length})` },
    { key: "overstock", label: `Overstock (${data.overstocked.length})` },
    { key: "ok", label: "Healthy" },
  ];

  return (
    <div>
      <PageHeader
        eyebrow="Analytics"
        title="Inventory grid"
        subtitle="Filter stock cards by risk — reorder, overstock, or healthy cover."
        action={
          <div className="flex flex-wrap gap-1 rounded-xl border border-[var(--line)] bg-[var(--wash)] p-1">
            {filters.map((f) => (
              <button
                key={f.key}
                type="button"
                onClick={() => setFilter(f.key)}
                className={
                  filter === f.key
                    ? "rounded-lg bg-white px-3 py-1.5 text-xs font-medium shadow-sm"
                    : "rounded-lg px-3 py-1.5 text-xs text-[var(--muted)]"
                }
              >
                {f.label}
              </button>
            ))}
          </div>
        }
      />

      <DataGrid className="mb-6 sm:grid-cols-3">
        <KpiCard
          label="Stock Value"
          value={inr(data.total_stock_value)}
          icon={Boxes}
          tone="accent"
        />
        <KpiCard
          label="Reorder Required"
          value={String(data.reorder_required.length)}
          icon={AlertTriangle}
          tone={data.reorder_required.length ? "rose" : "emerald"}
        />
        <KpiCard
          label="Overstocked"
          value={String(data.overstocked.length)}
          icon={PackageCheck}
          tone="amber"
        />
      </DataGrid>

      {filtered.length ? (
        <DataGrid className="sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4">
          {filtered.map((item) => {
            const cover =
              item.reorder_level > 0
                ? item.current_stock / item.reorder_level
                : 1;
            const isReorder = item.status === "Reorder Required";
            const isOver = overstockNames.has(item.product);
            return (
              <Panel key={item.product} interactive className="flex flex-col">
                <div className="flex items-start justify-between gap-2">
                  <p className="font-[family-name:var(--font-display)] text-lg leading-snug">
                    {item.product}
                  </p>
                  <Badge tone={isReorder ? "rose" : isOver ? "amber" : "teal"}>
                    {isReorder ? "Reorder" : isOver ? "Overstock" : "OK"}
                  </Badge>
                </div>
                <p className="mt-2 text-xs text-[var(--muted)]">{item.supplier || "—"}</p>

                <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
                  <div>
                    <p className="text-[11px] uppercase tracking-wide text-[var(--muted)]">
                      Stock
                    </p>
                    <p className="mt-0.5 font-semibold">{item.current_stock}</p>
                  </div>
                  <div>
                    <p className="text-[11px] uppercase tracking-wide text-[var(--muted)]">
                      Reorder at
                    </p>
                    <p className="mt-0.5 font-semibold">{item.reorder_level}</p>
                  </div>
                </div>

                <div className="mt-4">
                  <div className="mb-1 flex justify-between text-[11px] text-[var(--muted)]">
                    <span>Cover vs reorder</span>
                    <span>{cover.toFixed(1)}×</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-[var(--wash)]">
                    <div
                      className={
                        isReorder
                          ? "h-full rounded-full bg-rose-500"
                          : isOver
                            ? "h-full rounded-full bg-orange-500"
                            : "h-full rounded-full bg-teal-600"
                      }
                      style={{ width: `${Math.min(cover * 33, 100)}%` }}
                    />
                  </div>
                </div>

                <p className="mt-auto pt-4 text-sm font-medium text-[var(--ink)]">
                  {inr(item.stock_value)}
                </p>
              </Panel>
            );
          })}
        </DataGrid>
      ) : (
        <EmptyState title="Nothing in this filter" body="Try another stock status." />
      )}

      {!filtered.length ? null : (
        <Panel className="mt-6">
          <SectionTitle title="Quick table" subtitle="Same items as the grid above" />
          <div className="si-scroll overflow-x-auto">
            <table className="min-w-full text-left text-sm">
              <thead className="text-[11px] uppercase tracking-wide text-[var(--muted)]">
                <tr>
                  <th className="pb-3 pr-4">Product</th>
                  <th className="pb-3 pr-4">Stock</th>
                  <th className="pb-3 pr-4">Reorder</th>
                  <th className="pb-3 pr-4">Value</th>
                  <th className="pb-3">Status</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((item) => (
                  <tr key={item.product} className="border-t border-[var(--line)]">
                    <td className="py-3 pr-4 font-medium">{item.product}</td>
                    <td className="py-3 pr-4">{item.current_stock}</td>
                    <td className="py-3 pr-4">{item.reorder_level}</td>
                    <td className="py-3 pr-4">{inr(item.stock_value)}</td>
                    <td className="py-3">{item.status}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Panel>
      )}
    </div>
  );
}
