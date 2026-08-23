"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  FileSpreadsheet,
  FileText,
  Trash2,
  Upload as UploadIcon,
} from "lucide-react";
import {
  Badge,
  Button,
  DataGrid,
  ErrorBanner,
  LoadingBlock,
  PageHeader,
  Panel,
  SectionTitle,
  Select,
} from "@/components/ui";
import { uploadApi } from "@/lib/api";

type Dataset = {
  id: number;
  filename: string;
  data_type: string;
  row_count: number;
  status: string;
  notes: string;
  uploaded_at: string;
};

const typeHints = [
  { type: "sales", label: "Sales", hint: "date, product, qty, price" },
  { type: "expenses", label: "Expenses", hint: "date, category, amount" },
  { type: "inventory", label: "Inventory", hint: "product, stock, reorder" },
  { type: "reviews", label: "Reviews", hint: "rating, review text" },
  { type: "customers", label: "Customers", hint: "id, spend, frequency" },
];

export default function UploadPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [dataType, setDataType] = useState("auto");
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function refresh() {
    const rows = (await uploadApi.list()) as Dataset[];
    setDatasets(rows);
  }

  useEffect(() => {
    refresh()
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setUploading(true);
    setError("");
    setMessage("");
    try {
      const result = (await uploadApi.upload(file, dataType)) as Dataset;
      setMessage(
        `Uploaded ${result.filename} as ${result.data_type} (${result.row_count} rows). ${result.notes}`
      );
      setFile(null);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed");
    } finally {
      setUploading(false);
    }
  }

  async function remove(id: number) {
    await uploadApi.remove(id);
    await refresh();
  }

  if (loading) return <LoadingBlock />;

  return (
    <div>
      <PageHeader
        eyebrow="Data"
        title="Upload workspace"
        subtitle="Drop CSV/Excel for analytics, or TXT/MD/PDF for the RAG assistant."
      />

      {error ? <ErrorBanner message={error} /> : null}
      {message ? (
        <div className="mb-4 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-800">
          {message}
        </div>
      ) : null}

      <div className="grid gap-4 xl:grid-cols-5">
        <Panel className="xl:col-span-3" glow>
          <SectionTitle title="Add a dataset" subtitle="Drag & drop or browse" />
          <form onSubmit={onSubmit} className="space-y-4">
            <label
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={(e) => {
                e.preventDefault();
                setDragOver(false);
                const dropped = e.dataTransfer.files?.[0];
                if (dropped) setFile(dropped);
              }}
              className={
                dragOver
                  ? "flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[var(--accent)] bg-teal-50/60 px-6 py-12 text-center transition"
                  : "flex cursor-pointer flex-col items-center justify-center rounded-2xl border-2 border-dashed border-[var(--line)] bg-[var(--wash)]/70 px-6 py-12 text-center transition hover:border-[var(--accent)] hover:bg-teal-50/40"
              }
            >
              <span className="mb-3 inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--accent)] text-white shadow-sm">
                <UploadIcon size={20} />
              </span>
              <p className="font-medium text-[var(--ink)]">
                {file ? file.name : "Drop a file here"}
              </p>
              <p className="mt-1 text-xs text-[var(--muted)]">
                CSV, Excel, TXT, MD, or PDF
              </p>
              <input
                type="file"
                accept=".csv,.xlsx,.xls,.txt,.md,.pdf"
                className="hidden"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
            </label>

            <div className="grid gap-3 sm:grid-cols-[1fr_auto]">
              <Select value={dataType} onChange={(e) => setDataType(e.target.value)}>
                <option value="auto">Auto-detect type</option>
                <option value="sales">Sales</option>
                <option value="expenses">Expenses</option>
                <option value="inventory">Inventory</option>
                <option value="customers">Customers</option>
                <option value="reviews">Reviews</option>
                <option value="financial">Financial</option>
              </Select>
              <Button disabled={uploading || !file}>
                {uploading ? "Processing..." : "Upload & process"}
              </Button>
            </div>
          </form>
        </Panel>

        <Panel className="xl:col-span-2">
          <SectionTitle title="Expected schemas" subtitle="Helps auto-detect" />
          <DataGrid className="sm:grid-cols-1">
            {typeHints.map((t) => (
              <button
                key={t.type}
                type="button"
                onClick={() => setDataType(t.type)}
                className={
                  dataType === t.type
                    ? "rounded-xl border border-[var(--accent)] bg-teal-50/70 px-3 py-3 text-left transition"
                    : "rounded-xl border border-[var(--line)] bg-[var(--wash)]/50 px-3 py-3 text-left transition hover:bg-white"
                }
              >
                <p className="text-sm font-medium">{t.label}</p>
                <p className="mt-0.5 text-xs text-[var(--muted)]">{t.hint}</p>
              </button>
            ))}
          </DataGrid>
        </Panel>
      </div>

      <div className="mt-6">
        <SectionTitle
          title="Uploaded datasets"
          subtitle={`${datasets.length} file${datasets.length === 1 ? "" : "s"} in your workspace`}
        />
        {datasets.length ? (
          <DataGrid className="sm:grid-cols-2 xl:grid-cols-3">
            {datasets.map((d) => {
              const isDoc = ["txt", "md", "pdf"].some((ext) =>
                d.filename.toLowerCase().endsWith(`.${ext}`)
              );
              return (
                <Panel key={d.id} interactive className="flex flex-col">
                  <div className="flex items-start justify-between gap-3">
                    <span className="inline-flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--wash)] text-[var(--accent)] ring-1 ring-[var(--line)]">
                      {isDoc ? <FileText size={18} /> : <FileSpreadsheet size={18} />}
                    </span>
                    <Badge
                      tone={
                        d.status === "indexed" || d.status === "processed"
                          ? "teal"
                          : "amber"
                      }
                    >
                      {d.status}
                    </Badge>
                  </div>
                  <p className="mt-4 truncate font-medium">{d.filename}</p>
                  <p className="mt-1 text-xs capitalize text-[var(--muted)]">
                    {d.data_type} · {d.row_count} rows
                  </p>
                  {d.notes ? (
                    <p className="mt-2 line-clamp-2 text-xs text-[var(--muted)]">
                      {d.notes}
                    </p>
                  ) : null}
                  <div className="mt-auto flex items-center justify-between pt-4">
                    <p className="text-[11px] text-[var(--muted)]">
                      {new Date(d.uploaded_at).toLocaleDateString()}
                    </p>
                    <Button variant="ghost" onClick={() => remove(d.id)}>
                      <Trash2 size={14} className="mr-1" /> Delete
                    </Button>
                  </div>
                </Panel>
              );
            })}
          </DataGrid>
        ) : (
          <Panel>
            <p className="py-8 text-center text-sm text-[var(--muted)]">
              No datasets yet — start with the sample files in{" "}
              <code>backend/sample_data/</code>.
            </p>
          </Panel>
        )}
      </div>
    </div>
  );
}
