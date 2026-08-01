import "server-only";

import fs from "node:fs";
import path from "node:path";
import { load } from "js-yaml";
import type { ModelEntry } from "@/lib/model-types";

export * from "@/lib/model-types";

/**
 * Reads directly from the same models.yaml the Python daemon reads --
 * the catalog has exactly one source of truth, and this docs site
 * regenerates from it at build time rather than duplicating its content
 * by hand. If a model's data here looks wrong, the fix belongs in
 * models.yaml, not in this file or in a page component.
 *
 * "server-only" makes this a build error if a client component ever
 * imports it -- fs/path can't run in the browser, and Next won't
 * silently strip it, it just fails the build. Client components should
 * import from @/lib/model-types instead, which has zero Node dependencies.
 */
const MODELS_YAML_PATH = path.join(
  process.cwd(),
  "..",
  "application",
  "server",
  "local",
  "services",
  "models",
  "models.yaml",
);

let cache: ModelEntry[] | null = null;

export function getAllModels(): ModelEntry[] {
  if (cache) return cache;

  const raw = fs.readFileSync(MODELS_YAML_PATH, "utf8");
  const parsed = load(raw) as Record<string, Omit<ModelEntry, "slug">>;

  cache = Object.entries(parsed).map(([slug, entry]) => ({ slug, ...entry }));
  return cache;
}

export function getModelBySlug(slug: string): ModelEntry | undefined {
  return getAllModels().find((m) => m.slug === slug);
}
