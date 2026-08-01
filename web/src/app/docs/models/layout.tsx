"use client";

import { LayoutGroup } from "motion/react";

export default function ModelsLayout({ children }: { children: React.ReactNode }) {
  return <LayoutGroup>{children}</LayoutGroup>;
}
