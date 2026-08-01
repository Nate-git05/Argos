import { Cable, Download, Play } from "lucide-react";
import { ScrollReveal } from "@/components/ui/ScrollReveal";

const steps = [
  {
    icon: Download,
    step: "01",
    title: "Pull",
    description:
      "Download an open-source VLA model with a single command. Argos fetches and caches the weights for you — no manual downloads, no guessing where files should go.",
  },
  {
    icon: Cable,
    step: "02",
    title: "Connect",
    description:
      "Link your robot arm and cameras. Argos verifies each connection is actually working before you rely on it, not just that a port opened.",
  },
  {
    icon: Play,
    step: "03",
    title: "Run",
    description:
      "Give it a plain-language instruction and watch your robot carry it out. Argos handles everything in between.",
  },
] as const;

export function HowItWorks() {
  return (
    <section className="border-y border-border bg-surface-alt px-6 py-28 sm:py-36">
      <div className="mx-auto max-w-5xl">
        <ScrollReveal className="text-center">
          <p className="font-mono text-sm text-teal-700">What it does</p>
          <h2 className="mt-3 text-balance text-2xl font-medium text-heading sm:text-3xl">
            Three commands between you and a working robot.
          </h2>
        </ScrollReveal>

        <div className="mt-16 grid gap-6 sm:grid-cols-3">
          {steps.map(({ icon: Icon, step, title, description }, i) => (
            <ScrollReveal key={title} delay={i * 0.1}>
              <div className="flex h-full flex-col rounded-xl border border-border bg-surface p-6 shadow-sm shadow-heading/[0.02] transition-shadow hover:shadow-md hover:shadow-teal-900/[0.06] sm:p-7">
                <div className="flex items-center justify-between">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-teal-50">
                    <Icon className="h-5 w-5 text-teal-700" strokeWidth={1.75} />
                  </div>
                  <span className="font-mono text-xs text-muted">{step}</span>
                </div>
                <h3 className="mt-5 text-lg font-semibold text-heading">{title}</h3>
                <p className="mt-2 text-sm leading-relaxed text-body">{description}</p>
              </div>
            </ScrollReveal>
          ))}
        </div>
      </div>
    </section>
  );
}
