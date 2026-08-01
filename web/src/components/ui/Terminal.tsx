"use client";

import { Check, Copy } from "lucide-react";
import { useState } from "react";

export function Terminal({ command }: { command: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  }

  return (
    <div className="flex w-full max-w-xl items-center gap-3 rounded-lg border border-white/10 bg-heading px-4 py-3 shadow-lg shadow-teal-900/10 sm:px-5 sm:py-4">
      <span aria-hidden className="select-none font-mono text-sm text-teal-400 sm:text-base">
        $
      </span>
      <code className="flex-1 overflow-x-auto whitespace-pre font-mono text-sm text-surface-alt sm:text-base">
        {command}
      </code>
      <button
        type="button"
        onClick={handleCopy}
        aria-label="Copy install command"
        className="flex shrink-0 items-center justify-center rounded-md p-1.5 text-muted transition-colors hover:bg-white/10 hover:text-surface-alt cursor-pointer"
      >
        {copied ? (
          <Check className="h-4 w-4 text-teal-400" strokeWidth={2.5} />
        ) : (
          <Copy className="h-4 w-4" strokeWidth={2} />
        )}
      </button>
    </div>
  );
}
