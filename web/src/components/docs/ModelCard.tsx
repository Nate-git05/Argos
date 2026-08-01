"use client";

import { FileStack, Lock } from "lucide-react";
import { motion } from "motion/react";
import Link from "next/link";
import {
  getCompatibilityStatus,
  getPrerequisites,
  getSummary,
  type ModelEntry,
} from "@/lib/model-types";
import { StatusBadge } from "@/components/docs/StatusBadge";

export function ModelCard({ model }: { model: ModelEntry }) {
  const status = getCompatibilityStatus(model);
  const prerequisites = getPrerequisites(model);
  const summary = getSummary(model);

  return (
    <Link href={`/docs/models/${model.slug}`} className="block">
      <motion.div
        layoutId={`model-card-${model.slug}`}
        className="flex h-full flex-col rounded-xl border border-border bg-surface p-6 shadow-sm shadow-heading/[0.02] transition-shadow hover:shadow-md hover:shadow-teal-900/[0.06]"
      >
        <div className="flex items-start justify-between gap-3">
          <h3 className="font-mono text-base font-semibold text-heading">{model.slug}</h3>
          <StatusBadge status={status} />
        </div>

        {model.params && <p className="mt-1 font-mono text-xs text-muted">{model.params} params</p>}

        <p className="mt-3 flex-1 text-sm leading-relaxed text-body">{summary}</p>

        {prerequisites.length > 0 && (
          <div className="mt-4 flex flex-wrap gap-2 border-t border-border pt-3">
            {prerequisites.map((p) => (
              <span
                key={p.label}
                className="inline-flex items-center gap-1 rounded-md bg-surface-alt px-2 py-1 text-xs text-muted"
              >
                {p.label === "Gated tokenizer access" ? (
                  <Lock className="h-3 w-3" strokeWidth={2} />
                ) : (
                  <FileStack className="h-3 w-3" strokeWidth={2} />
                )}
                {p.label}
              </span>
            ))}
          </div>
        )}
      </motion.div>
    </Link>
  );
}
