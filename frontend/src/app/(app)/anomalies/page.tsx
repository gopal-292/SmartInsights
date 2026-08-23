"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Badge,
  DataGrid,
  EmptyState,
  ErrorBanner,
  KpiCard,
  LoadingBlock,
  PageHeader,
  Panel,
} from "@/components/ui";
import { api } from "@/lib/api";
import { inr } from "@/lib/format";

type Anomaly = {
  type: string;
  date?: string;
  product?: string;
  category?: string;
  value: number;
  expected_range?: number[];
  expected?: number;
  z_score?: number;
  severity?: string;
  status: string;
  message: string;
};

type AnomalyData = {
  count: number;
  anomalies: Anomaly[];
  techniques: string[];
  method?: string;
};

export default function AnomaliesPage() {
  const [data, setData] = useState<AnomalyData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [typeFilter, setTypeFilter] = useState<string>("all");

  useEffect(() => {
    api<AnomalyData>("/ml/anomalies")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const types = useMemo(() => {
    const set = new Set((data?.anomalies || []).map((a) => a.type));
    return ["all", ...Array.from(set)];
  }, [data]);

  const filtered = useMemo(() => {
    if (!data) return [];
    if (typeFilter === "all") return data.anomalies;
    return data.anomalies.filter((a) => a.type === typeFilter);
  }, [data, typeFilter]);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  return (
    <div>
      <PageHeader
        eyebrow="Intelligence"
        title="Anomaly Detection"
        subtitle={
          data.method ||
          `Techniques: ${(data.techniques || []).join(", ")}`
        }
        action={
          <div className="flex flex-wrap gap-1 rounded-xl border border-[var(--line)] bg-[var(--wash)] p-1">
            {types.map((t) => (
              <button
                key={t}
                type="button"
                onClick={() => setTypeFilter(t)}
                className={
                  typeFilter === t
                    ? "rounded-lg bg-white px-3 py-1.5 text-xs font-medium capitalize shadow-sm"
                    : "rounded-lg px-3 py-1.5 text-xs capitalize text-[var(--muted)]"
                }
              >
                {t}
              </button>
            ))}
          </div>
        }
      />

      <DataGrid className="mb-6 sm:grid-cols-3">
        <KpiCard label="Flagged points" value={String(data.count)} tone="rose" />
        <KpiCard
          label="Showing"
          value={String(filtered.length)}
          hint={typeFilter === "all" ? "All types" : typeFilter}
        />
        <KpiCard
          label="Methods"
          value={String((data.techniques || []).length)}
          hint={(data.techniques || []).slice(0, 2).join(" · ")}
        />
      </DataGrid>

      {!filtered.length ? (
        <EmptyState
          title="No anomalies in this view"
          body="Upload more historical sales/expense data or clear the type filter."
        />
      ) : (
        <DataGrid className="sm:grid-cols-2 xl:grid-cols-3">
          {filtered.map((a, idx) => (
            <Panel key={`${a.type}-${a.date}-${idx}`} interactive>
              <div className="flex flex-wrap items-center gap-2">
                <Badge tone={a.severity === "high" ? "critical" : "amber"}>
                  {a.severity || a.status}
                </Badge>
                <Badge tone="neutral">{a.type}</Badge>
              </div>
              <p className="mt-3 font-medium leading-snug">{a.message}</p>
              <div className="mt-3 space-y-1 text-xs text-[var(--muted)]">
                <p>Value: {inr(a.value)}</p>
                {a.expected_range ? (
                  <p>
                    Expected: {inr(a.expected_range[0])} – {inr(a.expected_range[1])}
                  </p>
                ) : null}
                {a.z_score != null ? <p>Robust z: {a.z_score}</p> : null}
                {a.date ? <p>Date: {a.date}</p> : null}
                {a.product ? <p>Product: {a.product}</p> : null}
                {a.category ? <p>Category: {a.category}</p> : null}
              </div>
            </Panel>
          ))}
        </DataGrid>
      )}
    </div>
  );
}
