import { CliTerminal, type CliLine } from "@/components/docs/CliTerminal";

export interface CommandOption {
  flag: string;
  description: string;
}

export interface CommandSpec {
  name: string;
  syntax: string;
  description: string;
  options?: CommandOption[];
  example: CliLine[];
  planned?: boolean;
}

export function CommandBlock({ command }: { command: CommandSpec }) {
  return (
    <div className="rounded-xl border border-border bg-surface p-6 sm:p-7">
      <div className="flex flex-wrap items-center gap-2.5">
        <h3 className="font-mono text-base font-semibold text-heading">{command.name}</h3>
        {command.planned && (
          <span className="inline-flex items-center rounded-full border border-border bg-surface-alt px-2 py-0.5 font-mono text-[10px] tracking-wide text-muted uppercase">
            Coming soon
          </span>
        )}
      </div>

      <code className="mt-2 block font-mono text-sm text-teal-700">{command.syntax}</code>

      <p className="mt-3 max-w-2xl text-sm leading-relaxed text-body">{command.description}</p>

      {command.options && command.options.length > 0 && (
        <dl className="mt-4 flex flex-col gap-2 border-t border-border pt-4">
          {command.options.map((opt) => (
            <div key={opt.flag} className="flex flex-col gap-0.5 sm:flex-row sm:gap-3">
              <dt className="shrink-0 font-mono text-xs text-muted sm:w-40">{opt.flag}</dt>
              <dd className="text-sm text-body">{opt.description}</dd>
            </div>
          ))}
        </dl>
      )}

      <div className="mt-5">
        <CliTerminal lines={command.example} />
      </div>
    </div>
  );
}
