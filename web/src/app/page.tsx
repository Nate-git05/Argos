import { FinalCTA } from "@/components/landing/FinalCTA";
import { Hero } from "@/components/landing/Hero";
import { HowItWorks } from "@/components/landing/HowItWorks";
import { ModelCatalogTeaser } from "@/components/landing/ModelCatalogTeaser";
import { Problem } from "@/components/landing/Problem";
import { WhatItIs } from "@/components/landing/WhatItIs";

export default function Home() {
  return (
    <main>
      <Hero />
      <Problem />
      <WhatItIs />
      <HowItWorks />
      <ModelCatalogTeaser />
      <FinalCTA />
    </main>
  );
}
