import { ScrollReveal } from "@/components/ui/ScrollReveal";

export function Problem() {
  return (
    <section className="border-y border-border bg-surface-alt px-6 py-28 sm:py-36">
      <div className="mx-auto max-w-3xl text-center">
        <ScrollReveal>
          <p className="font-mono text-sm text-teal-700">The problem</p>
        </ScrollReveal>

        <ScrollReveal delay={0.08}>
          <p className="mt-5 text-balance text-2xl leading-snug font-medium text-heading sm:text-3xl">
            Running an open-source VLA model on real hardware shouldn&apos;t
            mean fighting mismatched environments, hunting down outdated
            SDKs, and rebuilding a CLI setup every time something breaks.
          </p>
        </ScrollReveal>

        <ScrollReveal delay={0.16}>
          <p className="mt-6 text-balance text-base text-body sm:text-lg">
            You didn&apos;t start building a robot to debug dependency
            conflicts. You started to make it move.
          </p>
        </ScrollReveal>
      </div>
    </section>
  );
}
