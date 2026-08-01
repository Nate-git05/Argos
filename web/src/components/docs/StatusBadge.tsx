import type { CompatibilityStatus } from "@/lib/models";

const styles: Record<CompatibilityStatus, string> = {
  Supported: "bg-teal-500 text-white",
  Candidate: "bg-teal-50 text-teal-700 border border-teal-200",
  "Not compatible": "bg-surface-alt text-muted border border-border",
};

export function StatusBadge({ status }: { status: CompatibilityStatus }) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 font-mono text-xs font-medium whitespace-nowrap ${styles[status]}`}
    >
      {status}
    </span>
  );
}
