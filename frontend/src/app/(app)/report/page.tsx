"use client";

import { useEffect, useState } from "react";
import {
  Button,
  DataGrid,
  ErrorBanner,
  KpiCard,
  LoadingBlock,
  PageHeader,
  Panel,
  SectionTitle,
} from "@/components/ui";
import { api, downloadFile } from "@/lib/api";
import { inr, pct } from "@/lib/format";

type Report = {
  executive_summary: { summary: string; insights: string[] };
  kpis: Record<string, number>;
  sales: { top_product?: { product: string; revenue: number; units: number } };
  expenses: { highest_category?: { category: string; amount: number } };
  inventory: { reorder_required?: Array<{ product: string }> };
  sentiment: { distribution?: Record<string, number>; main_complaint?: string };
  forecast: { next_month_revenue?: number };
  anomalies: { count?: number };
  recommendations: {
    recommendations: Array<{ area: string; recommendation: string; action?: string }>;
  };
};

export default function ReportPage() {
  const [report, setReport] = useState<Report | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState("");

  useEffect(() => {
    api<Report>("/ai/report")
      .then(setReport)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function handleDownloadPdf() {
    setDownloadError("");
    setDownloading(true);
    try {
      await downloadFile("/ai/report/pdf", "smartinsights-report.pdf");
    } catch (e) {
      setDownloadError(e instanceof Error ? e.message : "PDF download failed");
    } finally {
      setDownloading(false);
    }
  }

  async function handlePreviewHtml() {
    setDownloadError("");
    try {
      await downloadFile("/ai/report/html", "smartinsights-report.html");
    } catch (e) {
      setDownloadError(e instanceof Error ? e.message : "HTML report failed");
    }
  }

  if (loading) return <LoadingBlock label="Generating report..." />;
  if (error) return <ErrorBanner message={error} />;
  if (!report) return null;

  const k = report.kpis;
  const findings = [
    report.sales.top_product
      ? `Top product: ${report.sales.top_product.product} (${inr(report.sales.top_product.revenue)})`
      : null,
    report.expenses.highest_category
      ? `Highest expense: ${report.expenses.highest_category.category} (${inr(report.expenses.highest_category.amount)})`
      : null,
    `Reorder needed: ${(report.inventory.reorder_required || []).map((i) => i.product).join(", ") || "none"}`,
    `Sentiment theme: ${report.sentiment.main_complaint || "N/A"}`,
    `Forecast next month: ${inr(report.forecast.next_month_revenue)}`,
    `Anomalies detected: ${report.anomalies.count || 0}`,
  ].filter(Boolean) as string[];

  return (
    <div>
      <PageHeader
        eyebrow="Output"
        title="Business Performance Report"
        subtitle="Generated with Jinja2 + WeasyPrint — download PDF for submissions and demos."
        action={
          <div className="flex flex-wrap gap-2">
            <Button onClick={handleDownloadPdf} disabled={downloading}>
              {downloading ? "Preparing PDF..." : "Download PDF"}
            </Button>
            <Button variant="secondary" onClick={handlePreviewHtml}>
              Download HTML
            </Button>
            <Button variant="ghost" onClick={() => window.print()}>
              Print
            </Button>
          </div>
        }
      />
      {downloadError ? <ErrorBanner message={downloadError} /> : null}

      <DataGrid className="mb-6 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Revenue" value={inr(k.total_revenue)} tone="accent" />
        <KpiCard label="Expenses" value={inr(k.total_expenses)} tone="amber" />
        <KpiCard label="Net Profit" value={inr(k.net_profit)} tone="emerald" />
        <KpiCard label="Margin" value={pct(k.profit_margin)} />
      </DataGrid>

      <div className="grid gap-4 xl:grid-cols-5">
        <Panel className="xl:col-span-3" interactive>
          <SectionTitle title="Executive summary" />
          <p className="leading-relaxed text-[var(--ink)]">
            {report.executive_summary.summary}
          </p>
        </Panel>
        <Panel className="xl:col-span-2" interactive>
          <SectionTitle title="At a glance" />
          <div className="space-y-2 text-sm">
            <p>Orders: <strong>{k.total_orders}</strong></p>
            <p>Customers: <strong>{k.total_customers}</strong></p>
            <p>Next month forecast: <strong>{inr(report.forecast.next_month_revenue)}</strong></p>
            <p>Anomalies: <strong>{report.anomalies.count || 0}</strong></p>
          </div>
        </Panel>
      </div>

      <div className="mt-4">
        <SectionTitle title="Key findings" />
        <DataGrid className="sm:grid-cols-2 xl:grid-cols-3">
          {findings.map((f) => (
            <Panel key={f} interactive className="text-sm leading-relaxed">
              {f}
            </Panel>
          ))}
        </DataGrid>
      </div>

      <div className="mt-6">
        <SectionTitle title="Recommendations" />
        <DataGrid className="sm:grid-cols-2">
          {(report.recommendations.recommendations || []).map((r, idx) => (
            <Panel key={idx} interactive>
              <p className="text-[11px] font-semibold uppercase tracking-wide text-[var(--accent)]">
                {r.area}
              </p>
              <p className="mt-2 text-sm leading-relaxed">
                {r.action || r.recommendation}
              </p>
            </Panel>
          ))}
        </DataGrid>
      </div>
    </div>
  );
}
