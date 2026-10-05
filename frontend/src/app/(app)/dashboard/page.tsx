"use client";

import { useEffect, useState } from "react";
import {
  AlertTriangle,
  BarChart3,
  Bot,
  FileText,
  IndianRupee,
  Package,
  Percent,
  ShoppingCart,
  Sparkles,
  TrendingUp,
  Upload,
  Users,
  Wallet,
} from "lucide-react";
import { DualLineChart, TrendChart } from "@/components/Charts";
import {
  DataGrid,
  EmptyState,
  ErrorBanner,
  FeatureCard,
  HeroBanner,
  KpiCard,
  LoadingBlock,
  PageHeader,
  Panel,
  SectionTitle,
} from "@/components/ui";
import { api } from "@/lib/api";
import { inr, pct } from "@/lib/format";
import { useAuth } from "@/lib/auth";

type DashboardData = {
  kpis: Record<string, number>;
  sales: { monthly: Array<{ period: string; value: number }> };
  expenses: { monthly: Array<{ period: string; value: number }> };
  profitability: {
    monthly: Array<{
      period: string;
      revenue: number;
      expenses: number;
      profit: number;
    }>;
  };
};

export default function DashboardPage() {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api<DashboardData>("/analytics/dashboard")
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <LoadingBlock label="Loading dashboard..." />;
  if (error) return <ErrorBanner message={error} />;
  if (!data)
    return <EmptyState title="No data" body="Upload business files to begin." />;

  const k = data.kpis;
  const hasSales = (data.sales.monthly || []).length > 0;
  const firstName = user?.full_name?.split(" ")[0] || "there";

  const modules = [
    {
      href: "/upload",
      title: "Upload Data",
      description: "Bring in sales, expenses, inventory, reviews, or documents.",
      icon: Upload,
      meta: "CSV · Excel · PDF",
      accent: "teal" as const,
    },
    {
      href: "/sales",
      title: "Sales Analytics",
      description: "Revenue trends, top products, and regional performance.",
      icon: BarChart3,
      meta: hasSales ? `${data.sales.monthly.length} months tracked` : "Needs sales data",
      accent: "teal" as const,
    },
    {
      href: "/expenses",
      title: "Expense Analysis",
      description: "See where spend is rising and which categories dominate.",
      icon: Wallet,
      meta: k.total_expenses ? inr(k.total_expenses) : "Needs expenses",
      accent: "amber" as const,
    },
    {
      href: "/inventory",
      title: "Inventory",
      description: "Stock cover, reorder alerts, and dead-stock signals.",
      icon: Package,
      meta: k.inventory_value ? inr(k.inventory_value) : "Needs inventory",
      accent: "slate" as const,
    },
    {
      href: "/forecast",
      title: "Sales Forecast",
      description: "Walk-forward ML forecasts with accuracy scores.",
      icon: TrendingUp,
      meta: "6-month horizon",
      accent: "teal" as const,
    },
    {
      href: "/anomalies",
      title: "Anomalies",
      description: "Spot unusual sales days and expense spikes early.",
      icon: AlertTriangle,
      meta: "Isolation Forest + MAD",
      accent: "rose" as const,
    },
    {
      href: "/segments",
      title: "Customer Segments",
      description: "K-Means clusters for high-value and at-risk buyers.",
      icon: Users,
      meta: k.total_customers ? `${k.total_customers} customers` : "Needs customers",
      accent: "slate" as const,
    },
    {
      href: "/insights",
      title: "AI Insights",
      description: "Market situation and prioritised recommended actions.",
      icon: Sparkles,
      meta: "Pattern + advisor engine",
      accent: "amber" as const,
    },
    {
      href: "/assistant",
      title: "AI Assistant",
      description: "Ask business questions over analytics and documents.",
      icon: Bot,
      meta: "LangChain RAG",
      accent: "teal" as const,
    },
    {
      href: "/report",
      title: "Business Report",
      description: "Download a Jinja2 + WeasyPrint PDF board pack.",
      icon: FileText,
      meta: "HTML · PDF",
      accent: "slate" as const,
    },
  ];

  const revenueSpark = (data.sales.monthly || []).map((m) => m.value);
  const profitSpark = (data.profitability.monthly || []).map((m) => m.profit);

  return (
    <div>
      <HeroBanner
        title={
          <>
            Welcome back, <span className="si-gradient-text">{firstName}</span>
          </>
        }
        subtitle="Your command center for KPIs, ML forecasts, and AI-driven business actions."
      >
        <DataGrid className="sm:grid-cols-2 lg:grid-cols-4">
          <KpiCard
            label="Revenue"
            value={inr(k.total_revenue)}
            icon={IndianRupee}
            tone="accent"
            spark={revenueSpark.length > 1 ? revenueSpark : undefined}
          />
          <KpiCard
            label="Net Profit"
            value={inr(k.net_profit)}
            icon={TrendingUp}
            tone={k.net_profit >= 0 ? "emerald" : "rose"}
            trend={k.net_profit >= 0 ? "up" : "down"}
            spark={profitSpark.length > 1 ? profitSpark : undefined}
          />
          <KpiCard label="Margin" value={pct(k.profit_margin)} icon={Percent} />
          <KpiCard
            label="Growth"
            value={pct(k.sales_growth)}
            icon={ShoppingCart}
            tone={k.sales_growth >= 0 ? "emerald" : "rose"}
            trend={k.sales_growth > 0 ? "up" : k.sales_growth < 0 ? "down" : "flat"}
          />
        </DataGrid>
      </HeroBanner>

      <PageHeader
        eyebrow="Metrics"
        title="Performance overview"
        subtitle="Core financial indicators from your uploaded datasets."
      />

      <DataGrid className="sm:grid-cols-2 xl:grid-cols-5">
        <KpiCard
          label="Total Revenue"
          value={inr(k.total_revenue)}
          icon={IndianRupee}
          tone="accent"
          hint={`${k.total_orders || 0} orders`}
        />
        <KpiCard
          label="Total Expenses"
          value={inr(k.total_expenses)}
          icon={Wallet}
          tone="amber"
        />
        <KpiCard
          label="Net Profit"
          value={inr(k.net_profit)}
          icon={TrendingUp}
          tone={k.net_profit >= 0 ? "emerald" : "rose"}
          trend={k.net_profit >= 0 ? "up" : "down"}
        />
        <KpiCard
          label="Profit Margin"
          value={pct(k.profit_margin)}
          icon={Percent}
          tone="default"
        />
        <KpiCard
          label="Sales Growth"
          value={pct(k.sales_growth)}
          icon={ShoppingCart}
          tone={k.sales_growth >= 0 ? "emerald" : "rose"}
          trend={k.sales_growth > 0 ? "up" : k.sales_growth < 0 ? "down" : "flat"}
          hint="vs previous month"
        />
      </DataGrid>

      <div className="mt-8">
        <SectionTitle
          title="Feature modules"
          subtitle="Jump into any capability — each card opens a dedicated interactive workspace."
        />
        <DataGrid className="sm:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-5">
          {modules.map((m) => (
            <FeatureCard key={m.href} {...m} />
          ))}
        </DataGrid>
      </div>

      <div className="mt-8 grid gap-4 xl:grid-cols-2">
        <Panel interactive>
          <SectionTitle title="Revenue trend" subtitle="Monthly sales from uploaded data" />
          {hasSales ? (
            <TrendChart data={data.sales.monthly} name="Revenue" />
          ) : (
            <EmptyState title="No sales trend" body="Upload a sales CSV to unlock this chart." />
          )}
        </Panel>
        <Panel interactive>
          <SectionTitle
            title="Revenue vs costs"
            subtitle="Profitability across the same months"
          />
          {data.profitability.monthly?.length ? (
            <DualLineChart data={data.profitability.monthly} />
          ) : (
            <EmptyState
              title="No profitability trend"
              body="Upload sales and expenses to compare."
            />
          )}
        </Panel>
      </div>

      <DataGrid className="mt-4 sm:grid-cols-2 xl:grid-cols-4">
        <KpiCard label="Avg Order Value" value={inr(k.average_order_value)} />
        <KpiCard label="Customers" value={String(k.total_customers || 0)} icon={Users} />
        <KpiCard label="Inventory Value" value={inr(k.inventory_value)} icon={Package} />
        <KpiCard
          label="Satisfaction"
          value={k.customer_satisfaction ? `${k.customer_satisfaction}/5` : "—"}
          hint="From review ratings"
        />
      </DataGrid>
    </div>
  );
}
