"use client";

import { useEffect, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
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
import { inr, pct } from "@/lib/format";

type Prediction = {
  period: string;
  predicted_revenue: number;
  lower_bound?: number;
  upper_bound?: number;
  change_vs_recent_avg?: number | null;
};

type Accuracy = {
  mae?: number;
  rmse?: number;
  mape?: number | null;
  skill_vs_naive?: number | null;
  direction_accuracy?: number | null;
  folds?: number;
};

type EvaluationRow = {
  model: string;
  mae: number;
  mape?: number | null;
  skill_vs_naive?: number | null;
  direction_accuracy?: number | null;
};

type ForecastData = {
  history?: Array<{ period: string; revenue: number }>;
  predictions?: Prediction[];
  next_month_revenue?: number;
  horizon_total?: number;
  selected_model?: string;
  selection_basis?: string;
  models_used?: string[];
  confidence?: string;
  accuracy?: Accuracy | null;
  evaluation?: EvaluationRow[];
  validation?: string;
  key_findings?: string[];
  patterns?: {
    headlines?: string[];
    trend?: { direction?: string; summary?: string };
    seasonality?: { detected?: boolean; summary?: string };
  };
  message?: string;
};

function confidenceTone(level?: string): "emerald" | "amber" | "neutral" {
  if (level === "high") return "emerald";
  if (level === "medium") return "amber";
  return "neutral";
}

export default function ForecastPage() {
  const [data, setData] = useState<ForecastData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<ForecastData>("/ml/forecast?periods=6")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBanner message={error} />;
  if (!data) return null;

  const history = data.history || [];
  const predictions = data.predictions || [];
  const findings = data.key_findings || data.patterns?.headlines || [];

  const chartData = [
    ...history.map((h) => ({
      period: h.period,
      actual: h.revenue,
      forecast: undefined as number | undefined,
      lower: undefined as number | undefined,
      upper: undefined as number | undefined,
    })),
    ...predictions.map((p) => ({
      period: p.period,
      actual: undefined as number | undefined,
      forecast: p.predicted_revenue,
      lower: p.lower_bound,
      upper: p.upper_bound,
    })),
  ];

  // Bridge the last actual into the forecast series so the line connects.
  if (history.length && predictions.length) {
    const last = history[history.length - 1];
    chartData[history.length - 1] = {
      ...chartData[history.length - 1],
      forecast: last.revenue,
      lower: last.revenue,
      upper: last.revenue,
    };
  }

  return (
    <div>
      <PageHeader
        eyebrow="Intelligence"
        title="Sales Forecasting"
        subtitle="Walk-forward model selection across trend, seasonality, and residual learners — scored on your own history."
      />
      {data.message && !predictions.length ? (
        <EmptyState title="Not enough history" body={data.message} />
      ) : (
        <>
          <DataGrid className="mb-6 sm:grid-cols-2 xl:grid-cols-4">
            <KpiCard
              label="Next Month"
              value={inr(data.next_month_revenue)}
              tone="accent"
              hint={
                predictions[0]?.change_vs_recent_avg != null
                  ? `${predictions[0].change_vs_recent_avg > 0 ? "+" : ""}${predictions[0].change_vs_recent_avg}% vs recent avg`
                  : data.selected_model
              }
            />
            <KpiCard
              label="6-Month Total"
              value={inr(data.horizon_total)}
              hint={`${predictions.length} months ahead`}
            />
            <KpiCard
              label="Backtest MAPE"
              value={
                data.accuracy?.mape != null ? pct(data.accuracy.mape) : "—"
              }
              tone="amber"
              hint={
                data.accuracy?.folds
                  ? `${data.accuracy.folds} walk-forward folds`
                  : "Needs more history"
              }
            />
            <KpiCard
              label="Direction Accuracy"
              value={
                data.accuracy?.direction_accuracy != null
                  ? pct(data.accuracy.direction_accuracy)
                  : "—"
              }
              tone="emerald"
              hint="Share of months the trend direction was correct"
            />
          </DataGrid>

          <Panel className="mb-6" interactive>
            <div className="mb-3 flex flex-wrap items-center gap-2">
              <h2 className="font-[family-name:var(--font-display)] text-xl">
                History + forecast
              </h2>
              {data.confidence ? (
                <Badge tone={confidenceTone(data.confidence)}>
                  {data.confidence} confidence
                </Badge>
              ) : null}
              {data.selected_model ? (
                <span className="text-xs text-[var(--muted)]">
                  · {data.selected_model}
                </span>
              ) : null}
            </div>
            <div className="h-80 w-full">
              <ResponsiveContainer>
                <LineChart data={chartData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#d7e3de" />
                  <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                  <YAxis tick={{ fontSize: 12 }} />
                  <Tooltip
                    formatter={(value) =>
                      typeof value === "number" ? inr(value) : value
                    }
                  />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="upper"
                    name="Upper (80%)"
                    stroke="#99f6e4"
                    strokeDasharray="4 4"
                    dot={false}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="lower"
                    name="Lower (80%)"
                    stroke="#99f6e4"
                    strokeDasharray="4 4"
                    dot={false}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="actual"
                    name="Actual"
                    stroke="#0f766e"
                    strokeWidth={2.5}
                    dot={{ r: 2 }}
                    connectNulls={false}
                  />
                  <Line
                    type="monotone"
                    dataKey="forecast"
                    name="Forecast"
                    stroke="#c2410c"
                    strokeWidth={2.5}
                    strokeDasharray="6 4"
                    dot={{ r: 3 }}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            {data.selection_basis ? (
              <p className="mt-3 text-xs text-[var(--muted)]">
                {data.selection_basis}
                {data.validation ? ` · ${data.validation}` : ""}
              </p>
            ) : null}
          </Panel>

          <div className="mb-6 grid gap-6 lg:grid-cols-2">
            <Panel interactive>
              <SectionTitle title="Month-by-month outlook" />
              <DataGrid className="sm:grid-cols-1">
                {predictions.map((p) => (
                  <div
                    key={p.period}
                    className="rounded-xl border border-[var(--line)] bg-[var(--wash)] px-4 py-3 text-sm transition hover:bg-white"
                  >
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <p className="font-medium">{p.period}</p>
                      <p className="font-[family-name:var(--font-display)] text-lg">
                        {inr(p.predicted_revenue)}
                      </p>
                    </div>
                    <p className="mt-1 text-[var(--muted)]">
                      80% range {inr(p.lower_bound)} – {inr(p.upper_bound)}
                      {p.change_vs_recent_avg != null
                        ? ` · ${p.change_vs_recent_avg > 0 ? "+" : ""}${p.change_vs_recent_avg}% vs recent`
                        : ""}
                    </p>
                  </div>
                ))}
              </DataGrid>
            </Panel>

            <Panel interactive>
              <SectionTitle title="Model leaderboard" subtitle="Lower MAE wins" />
              {(data.evaluation || []).length ? (
                <div className="space-y-2">
                  {(data.evaluation || []).map((row, idx) => (
                    <div
                      key={row.model}
                      className="flex items-start justify-between gap-3 rounded-xl border border-[var(--line)] px-3 py-2.5 text-sm transition hover:bg-[var(--wash)]"
                    >
                      <div>
                        <p className="font-medium">
                          {idx === 0 ? "★ " : ""}
                          {row.model}
                        </p>
                        <p className="text-xs text-[var(--muted)]">
                          MAPE {row.mape != null ? pct(row.mape) : "—"}
                          {row.direction_accuracy != null
                            ? ` · dir ${pct(row.direction_accuracy)}`
                            : ""}
                          {row.skill_vs_naive != null
                            ? ` · skill ${row.skill_vs_naive}`
                            : ""}
                        </p>
                      </div>
                      <p className="shrink-0 text-xs text-[var(--muted)]">
                        MAE {inr(row.mae)}
                      </p>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-[var(--muted)]">
                  History is too short to backtest competing models yet. Upload
                  6+ months of sales to unlock accuracy scores.
                </p>
              )}
            </Panel>
          </div>

          {findings.length ? (
            <Panel>
              <h2 className="mb-3 font-[family-name:var(--font-display)] text-xl">
                Patterns in your history
              </h2>
              <ul className="list-disc space-y-2 pl-5 text-sm text-[var(--ink)]">
                {findings.map((line) => (
                  <li key={line}>{line}</li>
                ))}
              </ul>
            </Panel>
          ) : null}
        </>
      )}
    </div>
  );
}
