/**
 * Types + pure derivation functions over ModelEntry -- deliberately
 * separate from models.ts (which reads models.yaml off the filesystem).
 * This file has zero Node-only dependencies, so both server components
 * (pages) and client components (ModelCard, ModelDetail) can safely
 * import from it. Importing fs-touching code into a client component
 * breaks the build; this split is what prevents that.
 */

export interface CameraViews {
  count: number | string;
  keys?: string[];
  note?: string;
}

export interface Benchmark {
  success_rate?: number;
  step_ms?: number;
  inference_ms?: number;
  vram_mib?: number;
  peak_rss_mib?: number;
}

export interface ModelEntry {
  slug: string;
  repo_id: string;
  filename?: string | null;
  params?: string;
  vision_backbone?: string;
  language_backbone?: string;
  action_head?: string;
  n_action_steps?: number;
  solver_steps?: number;
  requires_gated_tokenizer?: boolean;
  gated_tokenizer_repo?: string;
  tokenizer_repo?: string;
  max_state_dim?: number;
  image_size?: number;
  fits_orin_nano_8gb?: boolean;
  fits_orin_nano_8gb_note?: string;
  status?: string;
  notes?: string;
  camera_views?: CameraViews;
  launch_env?: Record<string, string> | null;
  launch_notes?: string;
  info_confidence?: "high" | "medium" | "low" | "flag";
  info_confidence_note?: string;
  requires_stats_files?: boolean;
  stats_files?: string[];
  stats_source_repo?: string;
  extra_env?: Record<string, string>;
  benchmark_rtx_3060?: Benchmark;
  benchmark_orin_nano_8gb?: Benchmark;
  benchmark_orin_nano_8gb_split?: Benchmark;
}

export type CompatibilityStatus = "Supported" | "Candidate" | "Not compatible";

/**
 * Derived entirely from structured fields (fits_orin_nano_8gb, status),
 * never from free-text prose fields like notes/launch_notes/
 * info_confidence_note -- those are for humans reading the yaml
 * directly, not for driving page logic.
 */
export function getCompatibilityStatus(model: ModelEntry): CompatibilityStatus {
  if (model.fits_orin_nano_8gb === false) return "Not compatible";
  if (model.status?.toLowerCase().includes("officially supported")) return "Supported";
  return "Candidate";
}

/** One-line summary for the card grid, derived from real data -- never
 * hardcoded per model. Falls back through notes -> status -> backbone
 * names, in that order, since not every entry has every field. */
export function getSummary(model: ModelEntry): string {
  if (model.notes) {
    const firstSentence = model.notes.trim().split(/(?<=\.)\s/)[0];
    if (firstSentence) return firstSentence;
  }
  if (model.status) return model.status;
  const backbones = [model.vision_backbone, model.language_backbone].filter(Boolean);
  return backbones.length ? backbones.join(" · ") : "No description available yet.";
}

export interface Prerequisite {
  label: string;
  detail: string;
}

/** Only ever built from structured fields -- if a model genuinely has
 * none, this returns an empty array and the caller omits the section
 * entirely rather than rendering an empty/"None" state. */
export function getPrerequisites(model: ModelEntry): Prerequisite[] {
  const prereqs: Prerequisite[] = [];

  if (model.requires_gated_tokenizer) {
    prereqs.push({
      label: "Gated tokenizer access",
      detail: model.gated_tokenizer_repo
        ? `Requires accepting the license for ${model.gated_tokenizer_repo} on Hugging Face before this model's tokenizer can be downloaded.`
        : "Requires accepting a gated license on Hugging Face before this model's tokenizer can be downloaded.",
    });
  }

  if (model.requires_stats_files && model.stats_files?.length) {
    prereqs.push({
      label: "Extra stats files",
      detail: model.stats_source_repo
        ? `Needs ${model.stats_files.join(", ")} from ${model.stats_source_repo}.`
        : `Needs ${model.stats_files.join(", ")}.`,
    });
  }

  return prereqs;
}

export interface BenchmarkRow {
  label: string;
  successRate?: number;
  stepMs?: number;
  inferenceMs?: number;
  vramMib?: number;
  peakRssMib?: number;
}

/** Collects whichever benchmark_* fields actually exist on this entry --
 * not every model has every hardware tier benchmarked. */
export function getBenchmarkRows(model: ModelEntry): BenchmarkRow[] {
  const rows: BenchmarkRow[] = [];

  if (model.benchmark_rtx_3060) {
    rows.push({
      label: "RTX 3060",
      successRate: model.benchmark_rtx_3060.success_rate,
      stepMs: model.benchmark_rtx_3060.step_ms,
      inferenceMs: model.benchmark_rtx_3060.inference_ms,
      vramMib: model.benchmark_rtx_3060.vram_mib,
    });
  }

  if (model.benchmark_orin_nano_8gb) {
    rows.push({
      label: "Orin Nano 8GB",
      stepMs: model.benchmark_orin_nano_8gb.step_ms,
      peakRssMib: model.benchmark_orin_nano_8gb.peak_rss_mib,
    });
  }

  if (model.benchmark_orin_nano_8gb_split) {
    rows.push({
      label: "Orin Nano 8GB (split)",
      stepMs: model.benchmark_orin_nano_8gb_split.step_ms,
      peakRssMib: model.benchmark_orin_nano_8gb_split.peak_rss_mib,
    });
  }

  return rows;
}
