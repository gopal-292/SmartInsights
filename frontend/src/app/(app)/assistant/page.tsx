"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import {
  Button,
  DataGrid,
  PageHeader,
  Panel,
  SectionTitle,
  TextArea,
} from "@/components/ui";
import { api } from "@/lib/api";

type Message = { role: "user" | "assistant"; content: string; sources?: string[] };

const suggestions = [
  "Why did my profit decrease?",
  "Which product generates the highest revenue?",
  "Which products need to be reordered?",
  "What are my biggest expenses?",
  "What is my expected revenue next month?",
  "What are customers complaining about?",
  "What patterns do you see in my sales?",
  "What should I do next?",
];

export default function AssistantPage() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Ask me about your business performance. I use your uploaded analytics data and any business documents (RAG).",
    },
  ]);
  const [loading, setLoading] = useState(false);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  async function ask(q: string) {
    if (!q.trim() || loading) return;
    setMessages((prev) => [...prev, { role: "user", content: q }]);
    setLoading(true);
    try {
      const res = await api<{ answer: string; sources: string[] }>("/ai/assistant", {
        method: "POST",
        body: JSON.stringify({ question: q }),
      });
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "assistant",
          content: err instanceof Error ? err.message : "Assistant failed",
        },
      ]);
    } finally {
      setLoading(false);
      setQuestion("");
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    ask(question);
  }

  return (
    <div>
      <PageHeader
        eyebrow="Intelligence"
        title="AI Business Assistant"
        subtitle="Natural-language Q&A over your analytics and uploaded documents."
      />

      <div className="grid gap-4 xl:grid-cols-5">
        <Panel className="xl:col-span-2" interactive>
          <SectionTitle
            title="Suggested prompts"
            subtitle="Click any card to ask instantly"
          />
          <DataGrid className="sm:grid-cols-1">
            {suggestions.map((s) => (
              <button
                key={s}
                type="button"
                disabled={loading}
                onClick={() => ask(s)}
                className="rounded-xl border border-[var(--line)] bg-[var(--wash)]/70 px-3 py-3 text-left text-sm transition hover:-translate-y-0.5 hover:border-[var(--accent)] hover:bg-white disabled:opacity-50"
              >
                {s}
              </button>
            ))}
          </DataGrid>
        </Panel>

        <div className="flex min-h-[32rem] flex-col xl:col-span-3">
          <Panel className="si-scroll mb-3 flex-1 space-y-3 overflow-y-auto">
            {messages.map((m, idx) => (
              <div
                key={idx}
                className={
                  m.role === "user"
                    ? "ml-6 rounded-2xl bg-[var(--accent)] px-4 py-3 text-sm text-white shadow-sm"
                    : "mr-6 rounded-2xl border border-[var(--line)] bg-[var(--wash)] px-4 py-3 text-sm text-[var(--ink)]"
                }
              >
                <p className="whitespace-pre-wrap leading-relaxed">{m.content}</p>
                {m.sources?.length ? (
                  <p className="mt-2 text-xs opacity-70">
                    Sources: {m.sources.join(" | ").slice(0, 240)}
                  </p>
                ) : null}
              </div>
            ))}
            {loading ? (
              <div className="mr-6 rounded-2xl border border-dashed border-[var(--line)] bg-white px-4 py-3 text-sm text-[var(--muted)]">
                <span className="inline-flex items-center gap-2">
                  <span className="h-2 w-2 animate-pulse rounded-full bg-[var(--accent)]" />
                  Thinking through your data...
                </span>
              </div>
            ) : null}
            <div ref={endRef} />
          </Panel>

          <form
            onSubmit={onSubmit}
            className="flex flex-col gap-3 rounded-[var(--radius)] border border-[var(--line)] bg-[var(--panel)] p-3 shadow-[var(--shadow-soft)] sm:flex-row"
          >
            <TextArea
              rows={2}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Ask a business question..."
              className="border-0 bg-transparent shadow-none focus:ring-0"
            />
            <Button disabled={loading || !question.trim()} className="sm:self-end">
              <Send size={14} className="mr-1.5" />
              {loading ? "..." : "Ask"}
            </Button>
          </form>
        </div>
      </div>
    </div>
  );
}
