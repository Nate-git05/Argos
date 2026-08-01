"use client";

import { motion } from "motion/react";
import {
  getBenchmarkRows,
  getCompatibilityStatus,
  getPrerequisites,
  type ModelEntry,
} from "@/lib/model-types";
import { StatusBadge } from "@/components/docs/StatusBadge";
import { StickyNav, type NavSection } from "@/components/docs/StickyNav";

function fmt(value: number | undefined, suffix = ""): string {
  return value === undefined ? "—" : `${value}${suffix}`;
}

export function ModelDetail({ model }: { model: ModelEntry }) {
  const status = getCompatibilityStatus(model);
  const prerequisites = getPrerequisites(model);
  const benchmarkRows = getBenchmarkRows(model);

  const sections: NavSection[] = [
    { id: "overview", label: "Overview" },
    { id: "architecture", label: "Architecture" },
    ...(prerequisites.length > 0 ? [{ id: "prerequisites", label: "Prerequisites" }] : []),
    { id: "hardware-fit", label: "Hardware fit" },
    ...(benchmarkRows.length > 0 ? [{ id: "benchmarks", label: "Benchmarks" }] : []),
  ];

  return (
    <div className="mx-auto max-w-4xl px-8 py-12 sm:px-12">
      <motion.div
        layoutId={`model-card-${model.slug}`}
        className="rounded-xl border border-border bg-surface p-6"
      >
        <div className="flex flex-wrap items-center gap-3">
          <h1 className="font-mono text-2xl font-semibold text-heading">{model.slug}</h1>
          <StatusBadge status={status} />
        </div>
        {model.params && <p className="mt-1 font-mono text-sm text-muted">{model.params} params</p>}
      </motion.div>

      <div className="mt-8">
        <StickyNav sections={sections} />
      </div>

      <div className="mt-10 flex flex-col gap-16">
        <section id="overview">
          <h2 className="font-mono text-sm text-teal-700">Overview</h2>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-body">
            {model.notes?.trim() ?? model.status ?? "No overview available yet."}
          </p>
        </section>

        <section id="architecture">
          <h2 className="font-mono text-sm text-teal-700">Architecture</h2>
          <dl className="mt-4 grid max-w-2xl grid-cols-1 gap-x-8 gap-y-3 rounded-xl border border-border bg-surface p-6 sm:grid-cols-2">
            {model.vision_backbone && (
              <div>
                <dt className="font-mono text-xs text-muted">Vision backbone</dt>
                <dd className="mt-0.5 text-sm text-heading">{model.vision_backbone}</dd>
              </div>
            )}
            {model.language_backbone && (
              <div>
                <dt className="font-mono text-xs text-muted">Language backbone</dt>
                <dd className="mt-0.5 text-sm text-heading">{model.language_backbone}</dd>
              </div>
            )}
            {model.action_head && (
              <div className="sm:col-span-2">
                <dt className="font-mono text-xs text-muted">Action head</dt>
                <dd className="mt-0.5 text-sm text-heading">{model.action_head}</dd>
              </div>
            )}
            {model.n_action_steps !== undefined && (
              <div>
                <dt className="font-mono text-xs text-muted">Action steps per chunk</dt>
                <dd className="mt-0.5 text-sm text-heading">{model.n_action_steps}</dd>
              </div>
            )}
            {model.solver_steps !== undefined && (
              <div>
                <dt className="font-mono text-xs text-muted">Solver steps</dt>
                <dd className="mt-0.5 text-sm text-heading">{model.solver_steps}</dd>
              </div>
            )}
            {model.camera_views && (
              <div className="sm:col-span-2">
                <dt className="font-mono text-xs text-muted">Camera views</dt>
                <dd className="mt-0.5 text-sm text-heading">
                  {model.camera_views.count}
                  {model.camera_views.keys && ` — ${model.camera_views.keys.join(", ")}`}
                </dd>
                {model.camera_views.note && (
                  <dd className="mt-1 text-xs text-muted">{model.camera_views.note}</dd>
                )}
              </div>
            )}
          </dl>
        </section>

        {prerequisites.length > 0 && (
          <section id="prerequisites">
            <h2 className="font-mono text-sm text-teal-700">Prerequisites</h2>
            <ul className="mt-4 flex max-w-2xl flex-col gap-3">
              {prerequisites.map((p) => (
                <li key={p.label} className="rounded-xl border border-teal-200 bg-teal-50 p-4">
                  <p className="text-sm font-medium text-teal-700">{p.label}</p>
                  <p className="mt-1 text-sm text-body">{p.detail}</p>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section id="hardware-fit">
          <h2 className="font-mono text-sm text-teal-700">Hardware fit</h2>
          <div
            className={`mt-4 max-w-2xl rounded-xl border p-5 ${
              model.fits_orin_nano_8gb === false
                ? "border-border bg-surface-alt"
                : "border-teal-200 bg-teal-50"
            }`}
          >
            <p
              className={`text-sm font-medium ${
                model.fits_orin_nano_8gb === false ? "text-heading" : "text-teal-700"
              }`}
            >
              {model.fits_orin_nano_8gb === false
                ? "Does not fit the 8GB Orin Nano target"
                : "Fits the 8GB Orin Nano target"}
            </p>
            {model.fits_orin_nano_8gb_note && (
              <p className="mt-1.5 text-sm text-body">{model.fits_orin_nano_8gb_note}</p>
            )}
          </div>
        </section>

        {benchmarkRows.length > 0 && (
          <section id="benchmarks">
            <h2 className="font-mono text-sm text-teal-700">Benchmarks</h2>
            <div className="mt-4 overflow-x-auto rounded-xl border border-border">
              <table className="w-full min-w-[560px] text-left text-sm">
                <thead>
                  <tr className="border-b border-border bg-surface-alt text-xs text-muted">
                    <th className="px-4 py-3 font-mono font-medium">Hardware</th>
                    <th className="px-4 py-3 font-mono font-medium">Success rate</th>
                    <th className="px-4 py-3 font-mono font-medium">Step time</th>
                    <th className="px-4 py-3 font-mono font-medium">Inference time</th>
                    <th className="px-4 py-3 font-mono font-medium">Memory</th>
                  </tr>
                </thead>
                <tbody>
                  {benchmarkRows.map((row) => (
                    <tr key={row.label} className="border-b border-border last:border-0">
                      <td className="px-4 py-3 font-medium text-heading">{row.label}</td>
                      <td className="px-4 py-3 text-body">{fmt(row.successRate, "%")}</td>
                      <td className="px-4 py-3 text-body">{fmt(row.stepMs, " ms")}</td>
                      <td className="px-4 py-3 text-body">{fmt(row.inferenceMs, " ms")}</td>
                      <td className="px-4 py-3 text-body">
                        {row.vramMib !== undefined
                          ? `${row.vramMib} MiB VRAM`
                          : row.peakRssMib !== undefined
                            ? `${row.peakRssMib} MiB RSS`
                            : "—"}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}
      </div>
    </div>
  );
}
