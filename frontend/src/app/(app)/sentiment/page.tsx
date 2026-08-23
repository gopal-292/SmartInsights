"use client";

import { useEffect, useState } from "react";
import { MessageSquareWarning, Star, Users } from "lucide-react";
import { SentimentPie } from "@/components/Charts";
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
import { pct } from "@/lib/format";

type SentimentData = {
  distribution?: Record<string, number>;
  main_complaint?: string;
  average_rating?: number;
  sample_size?: number;
  message?: string;
};

const tones: Record<string, string> = {
  Positive: "from-emerald-50 to-white border-emerald-200",
  Neutral: "from-stone-50 to-white border-stone-200",
  Negative: "from-rose-50 to-white border-rose-200",
};

export default function SentimentPage() {
  const [data, setData] = useState<SentimentData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [active, setActive] = useState<string | null>(null);

  useEffect(() => {
    api<SentimentData>("/ml/sentiment")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBanner message={error} />;
  if (!data || data.message)
    return (
      <EmptyState
        title="No reviews"
        body="Upload a customer reviews CSV to analyze sentiment."
      />
    );

  const pie = Object.entries(data.distribution || {}).map(([name, value]) => ({
    name,
    value,
  }));

  return (
    <div>
      <PageHeader
        eyebrow="Intelligence"
        title="Customer Sentiment"
        subtitle="Review mix broken into interactive tiles — click a mood to highlight it."
      />

      <DataGrid className="mb-6 sm:grid-cols-3">
        <KpiCard
          label="Avg Rating"
          value={data.average_rating ? `${data.average_rating}/5` : "—"}
          icon={Star}
          tone="amber"
        />
        <KpiCard
          label="Reviews Analyzed"
          value={String(data.sample_size || 0)}
          icon={Users}
        />
        <KpiCard
          label="Main Complaint"
          value={data.main_complaint || "—"}
          icon={MessageSquareWarning}
          tone="rose"
        />
      </DataGrid>

      <DataGrid className="mb-4 sm:grid-cols-3">
        {pie.map((slice) => (
          <button
            key={slice.name}
            type="button"
            onClick={() => setActive(active === slice.name ? null : slice.name)}
            className={`rounded-[var(--radius)] border bg-gradient-to-br p-5 text-left shadow-[var(--shadow-soft)] transition hover:-translate-y-0.5 ${
              tones[slice.name] || "from-white to-[var(--wash)]"
            } ${active === slice.name ? "ring-2 ring-[var(--accent)]" : ""}`}
          >
            <p className="text-xs uppercase tracking-wide text-[var(--muted)]">
              {slice.name}
            </p>
            <p className="mt-2 font-[family-name:var(--font-display)] text-3xl">
              {pct(slice.value)}
            </p>
            <p className="mt-1 text-xs text-[var(--muted)]">of reviewed feedback</p>
          </button>
        ))}
      </DataGrid>

      <div className="grid gap-4 xl:grid-cols-2">
        <Panel interactive>
          <SectionTitle title="Distribution" subtitle="Share of sentiment labels" />
          <SentimentPie data={active ? pie.filter((p) => p.name === active) : pie} />
        </Panel>
        <Panel interactive glow>
          <SectionTitle title="What to watch" />
          <ul className="space-y-3 text-sm leading-relaxed text-[var(--muted)]">
            <li>
              · Dominant complaint theme:{" "}
              <strong className="text-[var(--ink)]">
                {data.main_complaint || "None detected"}
              </strong>
            </li>
            <li>
              · Negative share:{" "}
              <strong className="text-[var(--ink)]">
                {pct(data.distribution?.Negative)}
              </strong>
            </li>
            <li>
              · Positive share:{" "}
              <strong className="text-[var(--ink)]">
                {pct(data.distribution?.Positive)}
              </strong>
            </li>
            <li>
              · Use AI Insights for concrete fix actions tied to this complaint theme.
            </li>
          </ul>
        </Panel>
      </div>
    </div>
  );
}
