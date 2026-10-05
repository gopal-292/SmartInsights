"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { Sidebar } from "@/components/Sidebar";
import { TopBar } from "@/components/TopBar";
import { LoadingBlock } from "@/components/ui";
import { useAuth } from "@/lib/auth";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  if (loading || !user) {
    return (
      <main className="si-mesh flex min-h-screen items-center justify-center">
        <LoadingBlock label="Loading SmartInsights..." />
      </main>
    );
  }

  return (
    <div className="flex min-h-screen flex-col lg:flex-row">
      <Sidebar />
      <div className="relative flex min-h-screen flex-1 flex-col">
        <div className="si-mesh si-grid-bg pointer-events-none absolute inset-0" />
        <main className="si-scroll relative flex-1 overflow-y-auto">
          <div className="mx-auto w-full max-w-[88rem] px-4 py-4 sm:px-6 sm:py-5 lg:px-8 lg:py-6">
            <TopBar />
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
