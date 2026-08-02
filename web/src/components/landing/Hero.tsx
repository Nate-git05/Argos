"use client";

import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { RegistrationModal } from "@/components/RegistrationModal";
import { Terminal } from "@/components/ui/Terminal";

export function Hero() {
  const [showRegistration, setShowRegistration] = useState(false);

  return (
    <section className="relative flex min-h-[92vh] flex-col items-center justify-center overflow-hidden px-6 pt-24 pb-16 text-center">
      <div
        aria-hidden
        className="pointer-events-none absolute inset-0 -z-10 bg-[radial-gradient(ellipse_60%_50%_at_50%_0%,var(--color-teal-50),transparent)]"
      />

      <span className="mb-6 inline-flex items-center rounded-full border border-teal-200 bg-teal-50 px-3.5 py-1 font-mono text-xs font-medium tracking-wide text-teal-700 sm:text-sm">
        Ollama for robot arms
      </span>

      <h1 className="max-w-3xl text-balance text-4xl font-semibold tracking-tight text-heading sm:text-6xl">
        Run VLA models on real robots.
      </h1>

      <p className="mt-5 max-w-xl text-balance text-base text-body sm:text-lg">
        Pull a model, connect your hardware, and run it — without fighting
        mismatched environments, outdated SDKs, or a complicated setup.
      </p>

      <div className="mt-10 flex flex-col items-center gap-4">
        <Terminal command="curl -fsSL https://www.xn--args-ira.com/install | bash" />
        <div className="flex items-center gap-5">
          <Link
            href="/docs"
            className="group inline-flex items-center gap-1 font-mono text-sm text-teal-700 transition-colors hover:text-teal-900"
          >
            Read the docs
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
          <button
            type="button"
            onClick={() => setShowRegistration(true)}
            className="rounded-lg bg-teal-500 px-4 py-2.5 font-mono text-sm font-medium text-white transition-colors hover:bg-teal-700 cursor-pointer"
          >
            Register
          </button>
        </div>
      </div>

      <RegistrationModal open={showRegistration} onClose={() => setShowRegistration(false)} />
    </section>
  );
}
