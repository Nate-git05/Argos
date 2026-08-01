"use client";

import { ArrowLeft } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ModelEntry } from "@/lib/model-types";
import { getCompatibilityStatus } from "@/lib/model-types";

const statusDotColor: Record<string, string> = {
  Supported: "bg-teal-500",
  Candidate: "bg-teal-200",
  "Not compatible": "bg-muted",
};

export function Sidebar({ models }: { models: ModelEntry[] }) {
  const pathname = usePathname();
  const inModels = pathname.startsWith("/docs/models");

  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 flex-col border-r border-border bg-surface-alt">
      <div className="flex items-center gap-2 border-b border-border px-5 py-5">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 font-mono text-sm text-muted transition-colors hover:text-heading"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          argos
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-5">
        <p className="px-2 font-mono text-xs tracking-wide text-muted uppercase">Docs</p>

        <div className="mt-2 flex flex-col gap-0.5">
          <Link
            href="/docs/models"
            className={`rounded-md px-2 py-1.5 text-sm font-medium transition-colors ${
              inModels ? "bg-teal-50 text-teal-700" : "text-body hover:bg-black/[0.03] hover:text-heading"
            }`}
          >
            Models
          </Link>

          {inModels && (
            <div className="mt-0.5 mb-1 ml-2 flex flex-col gap-0.5 border-l border-border pl-3">
              {models.map((model) => {
                const status = getCompatibilityStatus(model);
                const active = pathname === `/docs/models/${model.slug}`;
                return (
                  <Link
                    key={model.slug}
                    href={`/docs/models/${model.slug}`}
                    className={`flex items-center gap-2 rounded-md px-2 py-1 font-mono text-xs transition-colors ${
                      active ? "bg-teal-50 text-teal-700" : "text-muted hover:bg-black/[0.03] hover:text-body"
                    }`}
                  >
                    <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${statusDotColor[status]}`} />
                    {model.slug}
                  </Link>
                );
              })}
            </div>
          )}

          <span className="mt-1 flex items-center justify-between rounded-md px-2 py-1.5 text-sm font-medium text-muted">
            CLI
            <span className="font-mono text-[10px] tracking-wide uppercase">soon</span>
          </span>
          <span className="flex items-center justify-between rounded-md px-2 py-1.5 text-sm font-medium text-muted">
            SDK
            <span className="font-mono text-[10px] tracking-wide uppercase">soon</span>
          </span>
        </div>
      </nav>
    </aside>
  );
}
