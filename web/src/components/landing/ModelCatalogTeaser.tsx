import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { ScrollReveal } from "@/components/ui/ScrollReveal";

export function ModelCatalogTeaser() {
  return (
    <section className="px-6 py-20 sm:py-24">
      <ScrollReveal className="mx-auto flex max-w-3xl flex-col items-center gap-4 rounded-2xl border border-teal-200 bg-teal-50 px-8 py-10 text-center sm:flex-row sm:justify-between sm:text-left">
        <p className="text-balance text-base text-heading sm:text-lg">
          Argos supports{" "}
          <span className="font-mono font-medium text-teal-700">SmolVLA</span>
          , with more open-source VLA models on the way.
        </p>
        <Link
          href="/docs/models"
          className="group inline-flex shrink-0 items-center gap-1.5 rounded-lg bg-teal-500 px-4 py-2.5 font-mono text-sm font-medium text-white transition-colors hover:bg-teal-700"
        >
          View the model catalog
          <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
        </Link>
      </ScrollReveal>
    </section>
  );
}
