"use client";

import {
  Area,
  Bar,
  BarChart,
  CartesianGrid,
  ComposedChart,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = {
  teal: "#0d7377",
  tealLight: "#14b8a6",
  amber: "#d4622a",
  slate: "#64748b",
  profit: "#2563eb",
};

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ name?: string; value?: number; color?: string }>;
  label?: string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-[var(--line)] bg-white/95 px-3 py-2.5 text-xs shadow-[var(--shadow-lift)] backdrop-blur-md">
      <p className="mb-1.5 font-semibold text-[var(--ink)]">{label}</p>
      {payload.map((entry) => (
        <p key={entry.name} className="flex items-center gap-2 text-[var(--muted)]">
          <span
            className="h-2 w-2 rounded-full"
            style={{ background: entry.color || COLORS.teal }}
          />
          {entry.name}:{" "}
          <span className="font-medium text-[var(--ink)]">
            {typeof entry.value === "number"
              ? entry.value.toLocaleString("en-IN")
              : entry.value}
          </span>
        </p>
      ))}
    </div>
  );
}

export function TrendChart({
  data,
  dataKey = "value",
  name = "Value",
  color = COLORS.teal,
}: {
  data: Array<Record<string, string | number>>;
  dataKey?: string;
  name?: string;
  color?: string;
}) {
  const gradientId = `trend-${dataKey}`;
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <ComposedChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <defs>
            <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.25} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid stroke="rgba(13,115,119,0.08)" strokeDasharray="4 4" vertical={false} />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 11, fill: "#5c7369" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#5c7369" }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip content={<ChartTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
          <Area
            type="monotone"
            dataKey={dataKey}
            stroke="none"
            fill={`url(#${gradientId})`}
          />
          <Line
            type="monotone"
            dataKey={dataKey}
            name={name}
            stroke={color}
            strokeWidth={2.5}
            dot={{ r: 3, fill: color, strokeWidth: 0 }}
            activeDot={{ r: 5, strokeWidth: 2, stroke: "#fff" }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}

export function BarBlock({
  data,
  xKey,
  yKey,
  name,
  color = COLORS.amber,
}: {
  data: Array<Record<string, string | number>>;
  xKey: string;
  yKey: string;
  name: string;
  color?: string;
}) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 40 }}>
          <CartesianGrid stroke="rgba(13,115,119,0.08)" strokeDasharray="4 4" vertical={false} />
          <XAxis
            dataKey={xKey}
            tick={{ fontSize: 10, fill: "#5c7369" }}
            interval={0}
            angle={-22}
            textAnchor="end"
            height={56}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#5c7369" }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip content={<ChartTooltip />} cursor={{ fill: "rgba(13,115,119,0.06)" }} />
          <Bar
            dataKey={yKey}
            name={name}
            fill={color}
            radius={[10, 10, 4, 4]}
            maxBarSize={48}
          />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export function DualLineChart({
  data,
}: {
  data: Array<{ period: string; revenue: number; expenses: number; profit: number }>;
}) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 8, left: 0, bottom: 0 }}>
          <CartesianGrid stroke="rgba(13,115,119,0.08)" strokeDasharray="4 4" vertical={false} />
          <XAxis
            dataKey="period"
            tick={{ fontSize: 11, fill: "#5c7369" }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            tick={{ fontSize: 11, fill: "#5c7369" }}
            axisLine={false}
            tickLine={false}
            width={48}
          />
          <Tooltip content={<ChartTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12, paddingTop: 12 }} />
          <Line
            type="monotone"
            dataKey="revenue"
            stroke={COLORS.teal}
            strokeWidth={2.5}
            dot={false}
            name="Revenue"
          />
          <Line
            type="monotone"
            dataKey="expenses"
            stroke={COLORS.amber}
            strokeWidth={2.5}
            dot={false}
            name="Expenses"
          />
          <Line
            type="monotone"
            dataKey="profit"
            stroke={COLORS.profit}
            strokeWidth={2}
            strokeDasharray="6 4"
            dot={false}
            name="Profit"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

const PIE_COLORS = [COLORS.teal, COLORS.slate, COLORS.amber];

export function SentimentPie({
  data,
}: {
  data: Array<{ name: string; value: number }>;
}) {
  return (
    <div className="h-72 w-full">
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            innerRadius={58}
            outerRadius={92}
            paddingAngle={3}
            label={({ name, value }) => `${name} ${value}%`}
          >
            {data.map((_, index) => (
              <Cell
                key={index}
                fill={PIE_COLORS[index % PIE_COLORS.length]}
                stroke="rgba(255,255,255,0.8)"
                strokeWidth={2}
              />
            ))}
          </Pie>
          <Tooltip content={<ChartTooltip />} />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
