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
  SectionTitle,
} from "@/components/ui";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";

type Action = {
  priority: string;
  area: string;
  situation?: string;
  problem?: string;
  recommendation?: string;
  action?: string;
  expected_impact?: string;
  confidence?: string;
  evidence?: string[];
  timeframe?: string;
};

type RecsData = {
  recommendations: Action[];
  count?: number;
  market_context?: {
    outlook?: string;
    summary?: string;
    demand_direction?: string;
    next_month_forecast?: number;
    forecast_vs_recent_pct?: number | null;
    cost_pressure?: string;
    profit_margin_pct?: number;
    forecast_confidence?: string;
  };
  key_findings?: string[];
  forecast_summary?: {
    next_month_revenue?: number;
    horizon_total?: number;
    selected_model?: string;
    confidence?: string;
    accuracy?: { mape?: number | null; direction_accuracy?: number | null };
  };
  counts?: Record<string, number>;
};

type InsightsData = {
  summary: string;
  insights: string[];
  patterns?: { headlines?: string[] };
};

function priorityTone(
  priority: string
): "critical" | "amber" | "teal" | "neutral" | "rose" {
  const p = priority.toLowerCase();
  if (p === "critical") return "critical";
  if (p === "high") return "rose";
  if (p === "medium") return "amber";
  return "teal";
}

export default function InsightsPage() {
  const [insights, setInsights] = useState<InsightsData | null>(null);
  const [recs, setRecs] = useState<RecsData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [priorityFilter, setPriorityFilter] = useState("all");
  const [expanded, setExpanded] = useState<number | null>(0);

  useEffect(() => {
    Promise.all([
      api<InsightsData>("/ai/insights"),
      api<RecsData>("/ai/recommendations"),
    ])
      .then(([i, r]) => {
        setInsights(i);
        setRecs(r);
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  const actions = useMemo(() => {
    const all = recs?.recommendations || [];
    if (priorityFilter === "all") return all;
    return all.filter((a) => a.priority.toLowerCase() === priorityFilter);
  }, [recs, priorityFilter]);

  if (loading) return <LoadingBlock />;
  if (error) return <ErrorBanner message={error} />;

  const context = recs?.market_context;
  const findings =
    recs?.key_findings ||
    insights?.patterns?.headlines ||
    insights?.insights ||
    [];
  const forecast = recs?.forecast_summary;
  const counts = recs?.counts || {};
  const filters = ["all", "critical", "high", "medium", "low"];

  return (
    <div>
      <PageHeader
        eyebrow="Intelligence"
        title="AI Insights & Actions"
        subtitle="Market situation, pattern headlines, and a filterable action board."
        action={
          <div className="flex flex-wrap gap-1 rounded-xl border border-[var(--line)] bg-[var(--wash)] p-1">
            {filters.map((f) => (
              <button
                key={f}
                type="button"
                onClick={() => setPriorityFilter(f)}
                className={
                  priorityFilter === f
                    ? "rounded-lg bg-white px-3 py-1.5 text-xs font-medium capitalize shadow-sm"
                    : "rounded-lg px-3 py-1.5 text-xs capitalize text-[var(--muted)]"
                }
              >
                {f}
                {f !== "all" && counts[f] != null ? ` (${counts[f]})` : ""}
              </button>
            ))}
          </div>
        }
      />

      {context?.summary ? (
        <Panel className="mb-6 border-teal-200 bg-gradient-to-br from-teal-50/90 via-white to-orange-50/40" glow>
          <p className="text-[11px] font-semibold uppercase tracking-[0.16em] text-teal-800">
            Market situation
          </p>
          <p className="mt-2 text-lg leading-relaxed text-[var(--ink)]">
            {context.summary}
          </p>
          <div className="mt-4 flex flex-wrap gap-2">
            {context.outlook ? <Badge tone="teal">Outlook: {context.outlook}</Badge> : null}
            {context.demand_direction ? (
              <Badge tone="neutral">Demand: {context.demand_direction}</Badge>
            ) : null}
            {context.cost_pressure ? (
              <Badge tone="amber">Costs: {context.cost_pressure}</Badge>
            ) : null}
            {context.forecast_confidence ? (
              <Badge tone="emerald">
                Forecast: {context.forecast_confidence}
              </Badge>
            ) : null}
          </div>
        </Panel>
      ) : null}

      <DataGrid className="mb-6 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard
          label="Next Month Forecast"
          value={inr(forecast?.next_month_revenue ?? context?.next_month_forecast)}
          tone="accent"
          hint={
            context?.forecast_vs_recent_pct != null
              ? `${context.forecast_vs_recent_pct > 0 ? "+" : ""}${context.forecast_vs_recent_pct}% vs recent`
              : forecast?.selected_model
          }
        />
        <KpiCard
          label="Forecast Accuracy"
          value={
            forecast?.accuracy?.mape != null ? pct(forecast.accuracy.mape) : "—"
          }
          hint="Backtest MAPE"
        />
        <KpiCard
          label="Profit Margin"
          value={
            context?.profit_margin_pct != null
              ? pct(context.profit_margin_pct)
              : "—"
          }
        />
        <KpiCard
          label="Action Queue"
          value={String((recs?.recommendations || []).length)}
          tone="amber"
          hint={[
            counts.critical ? `${counts.critical} critical` : null,
            counts.high ? `${counts.high} high` : null,
          ]
            .filter(Boolean)
            .join(" · ") || "Prioritised by impact"}
        />
      </DataGrid>

      <div className="mb-6 grid gap-4 xl:grid-cols-5">
        <Panel className="xl:col-span-2" interactive>
          <SectionTitle title="Key findings" />
          {findings.length ? (
            <ul className="space-y-2.5 text-sm leading-relaxed">
              {findings.map((item) => (
                <li
                  key={item}
                  className="rounded-xl border border-[var(--line)] bg-[var(--wash)]/70 px-3 py-2.5"
                >
                  {item}
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-[var(--muted)]">{insights?.summary}</p>
          )}
        </Panel>

        <div className="xl:col-span-3">
          <SectionTitle
            title="Recommended actions"
            subtitle="Click a card to expand evidence"
          />
          {actions.length ? (
            <DataGrid className="sm:grid-cols-1 lg:grid-cols-2">
              {actions.map((rec, idx) => {
                const situation = rec.situation || rec.problem || "";
                const action = rec.action || rec.recommendation || "";
                const open = expanded === idx;
                return (
                  <button
                    key={`${rec.area}-${idx}`}
                    type="button"
                    onClick={() => setExpanded(open ? null : idx)}
                    className="rounded-[var(--radius)] border border-[var(--line)] bg-[var(--panel)] p-4 text-left shadow-[var(--shadow-soft)] transition hover:-translate-y-0.5 hover:shadow-[var(--shadow-lift)]"
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge tone={priorityTone(rec.priority)}>{rec.priority}</Badge>
                      <span className="text-[11px] uppercase tracking-wide text-[var(--muted)]">
                        {rec.area}
                      </span>
                      {rec.timeframe ? (
                        <span className="text-xs text-[var(--muted)]">
                          · {rec.timeframe}
                        </span>
                      ) : null}
                    </div>
                    <p className="mt-3 text-sm font-medium leading-snug">{situation}</p>
                    <p className="mt-2 text-sm leading-relaxed text-[var(--muted)]">
                      {action}
                    </p>
                    {rec.expected_impact ? (
                      <p className="mt-2 text-xs font-medium text-teal-800">
                        Impact: {rec.expected_impact}
                      </p>
                    ) : null}
                    {open && rec.evidence?.length ? (
                      <ul className="mt-3 space-y-1 border-t border-[var(--line)] pt-3 text-xs text-[var(--muted)]">
                        {rec.evidence.map((e) => (
                          <li key={e}>· {e}</li>
                        ))}
                      </ul>
                    ) : (
                      <p className="mt-3 text-[11px] text-[var(--accent)]">
                        {open ? "" : "Tap for evidence →"}
                      </p>
                    )}
                  </button>
                );
              })}
            </DataGrid>
          ) : (
            <EmptyState
              title="No actions in this filter"
              body="Try another priority, or upload more dated business data."
            />
          )}
        </div>
      </div>
    </div>
  );
}
