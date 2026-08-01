import { ScrollReveal } from "@/components/ui/ScrollReveal";

export function WhatItIs() {
  return (
    <section className="px-6 py-28 sm:py-36">
      <div className="mx-auto grid max-w-5xl gap-10 sm:grid-cols-[minmax(0,220px)_1fr] sm:gap-16">
        <ScrollReveal>
          <p className="font-mono text-sm text-teal-700">What Argos is</p>
        </ScrollReveal>

        <ScrollReveal delay={0.08}>
          <p className="text-balance text-2xl leading-snug font-medium text-heading sm:text-3xl">
            A developer tool for running and connecting{" "}
            <span className="text-teal-700">vision-language-action</span>{" "}
            models on real robots.
          </p>
          <p className="mt-5 max-w-2xl text-base text-body sm:text-lg">
            Argos is built for robotics developers working with actual
            hardware, not simulation. Pull an open-source model, connect your
            arm and cameras, and run — one tool, one workflow, from your
            terminal.
          </p>
        </ScrollReveal>
      </div>
    </section>
  );
}
