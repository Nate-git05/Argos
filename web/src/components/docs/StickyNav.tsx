"use client";

import { useEffect, useState } from "react";

export interface NavSection {
  id: string;
  label: string;
}

/**
 * Shared by every docs page with scroll-based segments (Models detail,
 * CLI reference) -- one implementation of "track which section is in
 * view and highlight it" rather than duplicating an IntersectionObserver
 * per page. Looks sections up by id via the DOM directly instead of
 * requiring the caller to thread ref callbacks through -- callers just
 * need a real element with a matching id somewhere on the page.
 */
export function StickyNav({ sections }: { sections: NavSection[] }) {
  const [active, setActive] = useState(sections[0]?.id);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.filter((e) => e.isIntersecting);
        if (visible.length > 0) setActive(visible[0].target.id);
      },
      { rootMargin: "-15% 0px -70% 0px", threshold: 0 },
    );

    const elements = sections
      .map((s) => document.getElementById(s.id))
      .filter((el): el is HTMLElement => el !== null);
    elements.forEach((el) => observer.observe(el));

    return () => observer.disconnect();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sections.map((s) => s.id).join(",")]);

  return (
    <nav className="sticky top-6 z-10 flex w-fit flex-wrap gap-1 rounded-full border border-border bg-surface/90 p-1 text-sm backdrop-blur">
      {sections.map((s) => (
        <a
          key={s.id}
          href={`#${s.id}`}
          className={`rounded-full px-3 py-1.5 font-mono text-xs transition-colors ${
            active === s.id ? "bg-teal-500 text-white" : "text-muted hover:text-heading"
          }`}
        >
          {s.label}
        </a>
      ))}
    </nav>
  );
}
