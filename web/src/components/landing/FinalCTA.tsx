import { ArrowRight } from "lucide-react";
import Link from "next/link";
import { ScrollReveal } from "@/components/ui/ScrollReveal";
import { Terminal } from "@/components/ui/Terminal";

export function FinalCTA() {
  return (
    <section className="bg-teal-900 px-6 py-28 text-center sm:py-36">
      <ScrollReveal className="mx-auto flex max-w-2xl flex-col items-center">
        <h2 className="text-balance text-3xl font-semibold tracking-tight text-white sm:text-4xl">
          Get your robot running in minutes.
        </h2>
        <p className="mt-4 text-balance text-base text-teal-200 sm:text-lg">
          One install command. No environment wrangling.
        </p>

        <div className="mt-10 flex flex-col items-center gap-4">
          <Terminal command="curl -fsSL https://www.xn--args-ira.com/install | bash" />
          <Link
            href="/docs"
            className="group inline-flex items-center gap-1 font-mono text-sm text-teal-200 transition-colors hover:text-white"
          >
            Read the docs
            <ArrowRight className="h-3.5 w-3.5 transition-transform group-hover:translate-x-0.5" />
          </Link>
        </div>
      </ScrollReveal>
    </section>
  );
}
