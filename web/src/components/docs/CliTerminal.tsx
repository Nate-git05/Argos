"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

export type CliLine =
  | { type: "command"; text: string }
  | { type: "output"; text: string }
  | { type: "success"; text: string };

/**
 * Deliberately its own color scheme (cli-bg/cli-amber/cli-muted/cli-fg,
 * defined in globals.css) -- not the site's teal palette. A terminal
 * example should look like an actual terminal, not a page section
 * wearing the brand colors.
 */
export function CliTerminal({ lines, copyable = true }: { lines: CliLine[]; copyable?: boolean }) {
  const [copied, setCopied] = useState(false);

  const commandText = lines
    .filter((l) => l.type === "command")
    .map((l) => l.text)
    .join("\n");

  async function handleCopy() {
    await navigator.clipboard.writeText(commandText);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <div className="relative w-full max-w-2xl overflow-x-auto rounded-lg border border-white/10 bg-cli-bg px-4 py-3.5 font-mono text-[13px] leading-relaxed shadow-lg shadow-black/20 sm:px-5 sm:py-4 sm:text-sm">
      {copyable && commandText && (
        <button
          type="button"
          onClick={handleCopy}
          aria-label="Copy command"
          className="absolute top-3 right-3 flex items-center justify-center rounded-md p-1.5 text-cli-muted transition-colors hover:bg-white/10 hover:text-cli-fg cursor-pointer"
        >
          {copied ? (
            <Check className="h-3.5 w-3.5 text-cli-amber" strokeWidth={2.5} />
          ) : (
            <Copy className="h-3.5 w-3.5" strokeWidth={2} />
          )}
        </button>
      )}
      <div className="flex flex-col gap-1 pr-8">
        {lines.map((line, i) => (
          <div key={i} className="whitespace-pre-wrap break-all">
            {line.type === "command" && (
              <span>
                <span className="text-cli-amber">$ </span>
                <span className="text-cli-fg">{line.text}</span>
              </span>
            )}
            {line.type === "output" && <span className="text-cli-muted">{line.text}</span>}
            {line.type === "success" && <span className="text-cli-amber">{line.text}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
