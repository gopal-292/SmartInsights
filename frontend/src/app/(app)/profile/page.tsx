"use client";

import { FormEvent, useEffect, useState } from "react";
import {
  Button,
  ErrorBanner,
  Input,
  LoadingBlock,
  PageHeader,
  Panel,
  Select,
} from "@/components/ui";
import { businessApi, type BusinessProfile } from "@/lib/api";

export default function ProfilePage() {
  const [form, setForm] = useState({
    business_name: "",
    business_type: "",
    industry: "",
    location: "",
    currency: "INR",
    business_size: "SME",
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    businessApi
      .get()
      .then((profile: BusinessProfile | null) => {
        if (profile) {
          setForm({
            business_name: profile.business_name,
            business_type: profile.business_type,
            industry: profile.industry,
            location: profile.location,
            currency: profile.currency,
            business_size: profile.business_size,
          });
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setSaving(true);
    setError("");
    setMessage("");
    try {
      await businessApi.save(form);
      setMessage("Business profile saved.");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  if (loading) return <LoadingBlock />;

  return (
    <div>
      <PageHeader
        title="Business Profile"
        subtitle="Tell SmartInsights about your business so reports feel contextual."
      />
      {error ? <ErrorBanner message={error} /> : null}
      {message ? (
        <div className="mb-4 rounded-xl border border-teal-200 bg-teal-50 px-4 py-3 text-sm text-teal-800">
          {message}
        </div>
      ) : null}
      <Panel>
        <form onSubmit={onSubmit} className="grid gap-4 md:grid-cols-2">
          <div className="md:col-span-2">
            <label className="mb-1 block text-xs uppercase tracking-wide text-[var(--muted)]">
              Business name
            </label>
            <Input
              required
              value={form.business_name}
              onChange={(e) => setForm({ ...form, business_name: e.target.value })}
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-[var(--muted)]">
              Business type
            </label>
            <Input
              value={form.business_type}
              onChange={(e) => setForm({ ...form, business_type: e.target.value })}
              placeholder="Retail / Services / Manufacturing"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-[var(--muted)]">
              Industry
            </label>
            <Input
              value={form.industry}
              onChange={(e) => setForm({ ...form, industry: e.target.value })}
              placeholder="Electronics"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-[var(--muted)]">
              Location
            </label>
            <Input
              value={form.location}
              onChange={(e) => setForm({ ...form, location: e.target.value })}
              placeholder="Pune, India"
            />
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-[var(--muted)]">
              Currency
            </label>
            <Select
              value={form.currency}
              onChange={(e) => setForm({ ...form, currency: e.target.value })}
            >
              <option value="INR">INR</option>
              <option value="USD">USD</option>
              <option value="EUR">EUR</option>
            </Select>
          </div>
          <div>
            <label className="mb-1 block text-xs uppercase tracking-wide text-[var(--muted)]">
              Business size
            </label>
            <Select
              value={form.business_size}
              onChange={(e) => setForm({ ...form, business_size: e.target.value })}
            >
              <option value="Micro">Micro</option>
              <option value="SME">SME</option>
              <option value="Mid-Market">Mid-Market</option>
            </Select>
          </div>
          <div className="md:col-span-2">
            <Button disabled={saving}>{saving ? "Saving..." : "Save profile"}</Button>
          </div>
        </form>
      </Panel>
    </div>
  );
}
