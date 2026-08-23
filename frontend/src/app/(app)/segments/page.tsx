"use client";

import { useEffect, useState } from "react";
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

type Segment = {
  segment: string;
  count: number;
  avg_spending: number;
  avg_frequency: number;
};

type SegmentData = {
  algorithm?: string;
  features?: string[];
  total_customers?: number;
  segments?: Segment[];
  message?: string;
};

function segmentTone(name: string): "teal" | "amber" | "rose" | "emerald" | "neutral" {
  if (name.includes("High")) return "emerald";
  if (name.includes("Inactive")) return "rose";
  if (name.includes("Regular")) return "teal";
  if (name.includes("Occasional")) return "amber";
  return "neutral";
}

export default function SegmentsPage() {
  const [data, setData] = useState<SegmentData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [selected, setSelected] = useState<string | null>(null);

  useEffect(() => {
    api<SegmentData>("/ml/segments")
      .then((res) => {
        setData(res);
        if (res.segments?.[0]) setSelected(res.segments[0].segment);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBanner message={error} />;
  if (!data || data.message)
    return (
      <EmptyState
        title="No segments yet"
        body="Upload customers or enough sales history for K-Means clustering."
      />
    );

  const segments = data.segments || [];
  const total = segments.reduce((s, seg) => s + seg.count, 0) || 1;
  const active = segments.find((s) => s.segment === selected);

  return (
    <div>
      <PageHeader
        eyebrow="Intelligence"
        title="Customer Segmentation"
        subtitle={`${data.algorithm} on ${(data.features || []).join(", ")}`}
      />

      <DataGrid className="mb-6 sm:grid-cols-3">
        <KpiCard label="Customers" value={String(data.total_customers || 0)} tone="accent" />
        <KpiCard label="Segments" value={String(segments.length)} />
        <KpiCard
          label="Features"
          value={String((data.features || []).length)}
          hint={(data.features || []).join(" · ")}
        />
      </DataGrid>

      <DataGrid className="mb-4 sm:grid-cols-2 xl:grid-cols-4">
        {segments.map((seg) => {
          const share = (seg.count / total) * 100;
          const isActive = selected === seg.segment;
          return (
            <button
              key={seg.segment}
              type="button"
              onClick={() => setSelected(seg.segment)}
              className={
                isActive
                  ? "rounded-[var(--radius)] border border-[var(--accent)] bg-teal-50/60 p-5 text-left shadow-[var(--shadow-lift)] transition"
                  : "rounded-[var(--radius)] border border-[var(--line)] bg-[var(--panel)] p-5 text-left shadow-[var(--shadow-soft)] transition hover:-translate-y-1 hover:shadow-[var(--shadow-lift)]"
              }
            >
              <Badge tone={segmentTone(seg.segment)}>{seg.segment}</Badge>
              <p className="mt-4 font-[family-name:var(--font-display)] text-3xl">
                {seg.count}
              </p>
              <p className="text-xs text-[var(--muted)]">customers · {share.toFixed(0)}%</p>
              <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--wash)]">
                <div
                  className="h-full rounded-full bg-[var(--accent)]"
                  style={{ width: `${share}%` }}
                />
              </div>
              <p className="mt-3 text-sm">Avg spend {inr(seg.avg_spending)}</p>
              <p className="text-xs text-[var(--muted)]">
                Frequency {seg.avg_frequency.toFixed(1)}
              </p>
            </button>
          );
        })}
      </DataGrid>

      {active ? (
        <Panel glow>
          <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
            Selected segment
          </p>
          <p className="mt-1 font-[family-name:var(--font-display)] text-2xl">
            {active.segment}
          </p>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <div className="rounded-xl bg-[var(--wash)] px-4 py-3">
              <p className="text-xs text-[var(--muted)]">Size</p>
              <p className="mt-1 text-lg font-semibold">{active.count}</p>
            </div>
            <div className="rounded-xl bg-[var(--wash)] px-4 py-3">
              <p className="text-xs text-[var(--muted)]">Avg spending</p>
              <p className="mt-1 text-lg font-semibold">{inr(active.avg_spending)}</p>
            </div>
            <div className="rounded-xl bg-[var(--wash)] px-4 py-3">
              <p className="text-xs text-[var(--muted)]">Avg frequency</p>
              <p className="mt-1 text-lg font-semibold">
                {active.avg_frequency.toFixed(1)}
              </p>
            </div>
          </div>
        </Panel>
      ) : null}
    </div>
  );
}
