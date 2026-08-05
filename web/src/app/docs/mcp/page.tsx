import Link from "next/link";
import { CommandBlock, type CommandSpec } from "@/components/docs/CommandBlock";
import { CliTerminal } from "@/components/docs/CliTerminal";
import { StickyNav, type NavSection } from "@/components/docs/StickyNav";

const sections: NavSection[] = [
  { id: "overview", label: "Overview" },
  { id: "installation", label: "Installation" },
  { id: "tools", label: "Tools" },
  { id: "resources", label: "Resources" },
];

const tools: CommandSpec[] = [
  {
    name: "connect_actuator",
    syntax: "connect_actuator(port?, servo_ids?)",
    description:
      "Connects the robot arm over the Feetech servo protocol. Called with no arguments, it discovers available serial ports instead of connecting to anything. Same underlying daemon call as `argos connect actuator` — the agent doesn't get a separate, looser code path.",
    options: [
      { flag: "port", description: "Serial port, e.g. /dev/ttyUSB0. Omit to list available ports instead." },
      { flag: "servo_ids", description: "Servo IDs to ping. Omit to use the default set for the reference arm." },
    ],
    example: [
      { type: "command", text: "connect_actuator()" },
      { type: "output", text: '{"ports": [{"port": "/dev/ttyUSB0", "description": "USB-Serial Controller"}]}' },
      { type: "command", text: 'connect_actuator(port="/dev/ttyUSB0")' },
      { type: "success", text: '{"port": "/dev/ttyUSB0", "connected": true, "responded": [...], "unresponsive": []}' },
    ],
  },
  {
    name: "connect_sensor",
    syntax: "connect_sensor(index?, view_name?)",
    description:
      "Connects a camera under a named view. Called with no arguments, it discovers available cameras. `view_name` has to match one of the target model's expected camera_views keys — check the model catalog first if you're not sure which.",
    options: [
      { flag: "index", description: "Camera index. Omit to discover available cameras." },
      { flag: "view_name", description: "View name — must match the model's expected camera_views key." },
    ],
    example: [
      { type: "command", text: "connect_sensor()" },
      { type: "output", text: '{"cameras": [{"index": 0, "preview_jpeg_b64": "..."}], "required_views": 2}' },
      { type: "command", text: 'connect_sensor(index=0, view_name="observation.images.image")' },
      { type: "success", text: '{"index": 0, "view_name": "observation.images.image", "connected": true, ...}' },
    ],
  },
  {
    name: "devices",
    syntax: "devices(kind?)",
    description: "Lists whatever's currently connected. Filter to just one kind, or omit it to see both.",
    options: [{ flag: "kind", description: "Optional. Filter to 'actuator' or 'sensor'. Omit to show both." }],
    example: [
      { type: "command", text: "devices()" },
      {
        type: "output",
        text: '{"actuator": {"port": "/dev/ttyUSB0", "servo_ids": [1,2,3,4,5,6]}, "sensors": [...]}',
      },
    ],
  },
  {
    name: "list_models",
    syntax: "list_models()",
    description: "Lists the model catalog and shows which ones are already pulled locally.",
    example: [
      { type: "command", text: "list_models()" },
      { type: "output", text: '{"models": {"smolvla": {"repo_id": "...", "pulled": false}, ...}}' },
    ],
  },
  {
    name: "pull_model",
    syntax: "pull_model(model)",
    description: "Downloads a model's weights from Hugging Face into the daemon's local cache.",
    options: [{ flag: "model", description: "Required. Model name from the catalog, e.g. smolvla." }],
    example: [
      { type: "command", text: 'pull_model("smolvla")' },
      { type: "success", text: '{"model": "smolvla", "path": ".../services/models/smolvla-libero.gguf"}' },
    ],
  },
  {
    name: "status",
    syntax: "status()",
    description:
      "Reports what model is loaded, which devices are connected, and how long the daemon and any active run have been up.",
    example: [
      { type: "command", text: "status()" },
      { type: "output", text: '{"daemon_uptime_s": 142.3, "run": {"active": false, ...}, "engine": {...}}' },
    ],
  },
  {
    name: "logs",
    syntax: "logs(source?, limit?)",
    description: "Shows recent log lines from the inference engine and/or the active run.",
    options: [
      { flag: "source", description: "Optional. Filter to 'engine' or 'run'. Omit to show both." },
      { flag: "limit", description: "Optional. Number of most-recent log lines to show. Defaults to 50." },
    ],
    example: [
      { type: "command", text: 'logs(source="engine", limit=3)' },
      { type: "output", text: '{"engine": ["loaded checkpoint smolvla-libero.gguf", "bound to tcp://127.0.0.1:5555, ready"]}' },
    ],
  },
  {
    name: "stop",
    syntax: "stop()",
    description:
      "Safely ends the active run: stops the control loop, drives the arm back to a home position, and shuts down the inference engine. The one tool here that moves the arm — only ever to a fixed home position as part of shutting a run down, never to start or steer one.",
    example: [
      { type: "command", text: "stop()" },
      { type: "success", text: '{"stopped": true, "home_reached": true}' },
    ],
  },
];

export default function McpDocsPage() {
  return (
    <div className="mx-auto max-w-4xl px-8 py-12 sm:px-12">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold text-heading">MCP</h1>
        <p className="mt-3 text-base text-body">
          Give an AI agent read/setup access to Argos — connecting hardware, browsing the model catalog,
          checking status — without ever handing it control of the arm.
        </p>
      </div>

      <div className="mt-8">
        <StickyNav sections={sections} />
      </div>

      <div className="mt-10 flex flex-col gap-16">
        <section id="overview">
          <h2 className="font-mono text-sm text-teal-700">Overview</h2>
          <div className="mt-3 flex max-w-2xl flex-col gap-4 text-base leading-relaxed text-body">
            <p>
              The Argos MCP server is the same kind of thin client the CLI is — every tool call is just
              an HTTP request to the daemon (<code className="rounded bg-surface-alt px-1.5 py-0.5 font-mono text-sm text-heading">http://127.0.0.1:8000</code>),
              which has to already be running. It exists so an agent like Claude can help a user set up
              and inspect their robot — connecting a serial port, discovering cameras, pulling a
              model — the parts of the workflow that are just setup, not actuation.
            </p>
          </div>

          <div className="mt-5 max-w-2xl rounded-xl border border-border bg-teal-50 p-5">
            <p className="text-sm leading-relaxed text-teal-900">
              <span className="font-semibold">There is no tool here that moves the arm to run a task.</span>{" "}
              <code className="rounded bg-surface px-1 py-0.5 font-mono text-xs">run</code> is deliberately
              not exposed — starting a run means the inference engine begins actively writing goal
              positions to real servos, and that decision is left to the user, run themselves via the
              CLI (<code className="rounded bg-surface px-1 py-0.5 font-mono text-xs">argos run &lt;model&gt; &quot;&lt;instruction&gt;&quot;</code>).
              The one exception is <code className="rounded bg-surface px-1 py-0.5 font-mono text-xs">stop</code>,
              which only ever drives the arm to a fixed home position as part of safely halting a run.
            </p>
          </div>
        </section>

        <section id="installation">
          <h2 className="font-mono text-sm text-teal-700">Installation</h2>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-body">
            The same install that sets up <code className="rounded bg-surface-alt px-1.5 py-0.5 font-mono text-sm text-heading">argos</code>{" "}
            also puts <code className="rounded bg-surface-alt px-1.5 py-0.5 font-mono text-sm text-heading">argos-mcp</code> on your{" "}
            <code className="rounded bg-surface-alt px-1.5 py-0.5 font-mono text-sm text-heading">PATH</code> — nothing extra to build.
          </p>
          <div className="mt-5">
            <CliTerminal lines={[{ type: "command", text: "curl -fsSL https://www.xn--args-ira.com/install | bash" }]} />
          </div>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-body">
            Then register it with your MCP host. For Claude Code:
          </p>
          <div className="mt-5">
            <CliTerminal lines={[{ type: "command", text: "claude mcp add argos -- argos-mcp" }]} />
          </div>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-body">
            For a host that reads a config file directly (e.g. Claude Desktop), add:
          </p>
          <div className="mt-5">
            <CliTerminal
              copyable={false}
              lines={[
                { type: "output", text: "{" },
                { type: "output", text: '  "mcpServers": {' },
                { type: "output", text: '    "argos": { "command": "argos-mcp" }' },
                { type: "output", text: "  }" },
                { type: "output", text: "}" },
              ]}
            />
          </div>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-body">
            The daemon needs to be running before any tool call here will work:
          </p>
          <div className="mt-5">
            <CliTerminal lines={[{ type: "command", text: "sudo systemctl start argos" }]} />
          </div>
        </section>

        <section id="tools">
          <h2 className="font-mono text-sm text-teal-700">Tools</h2>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-body">
            Every tool below maps to one of the daemon&apos;s <code className="rounded bg-surface-alt px-1.5 py-0.5 font-mono text-sm text-heading">/cli/*</code>{" "}
            endpoints — the same ones the CLI uses. Responses are the raw JSON the daemon returns, not
            the CLI&apos;s formatted terminal output.
          </p>

          <div className="mt-8 flex flex-col gap-5">
            {tools.map((tool) => (
              <CommandBlock key={tool.name} command={tool} />
            ))}
          </div>
        </section>

        <section id="resources">
          <h2 className="font-mono text-sm text-teal-700">Resources</h2>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-body">
            Static reference content, not daemon state — these resolve straight from files in the repo
            and don&apos;t need the daemon running.
          </p>

          <div className="mt-8 flex flex-col gap-5">
            <div className="rounded-xl border border-border bg-surface p-6 sm:p-7">
              <code className="font-mono text-base font-semibold text-heading">argos://readme</code>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-body">The project README.</p>
            </div>
            <div className="rounded-xl border border-border bg-surface p-6 sm:p-7">
              <code className="font-mono text-base font-semibold text-heading">argos://guide</code>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-body">
                An agent-facing guide: how the daemon, CLI, and MCP server fit together, which tools are
                available here and why <code className="rounded bg-surface-alt px-1 py-0.5 font-mono text-xs">run</code>{" "}
                isn&apos;t one of them, a suggested setup workflow, and a full{" "}
                <code className="rounded bg-surface-alt px-1 py-0.5 font-mono text-xs">argos --help</code>-equivalent
                CLI command reference — including commands only reachable via the CLI, so the agent can
                still explain them accurately.
              </p>
            </div>
            <div className="rounded-xl border border-border bg-surface p-6 sm:p-7">
              <code className="font-mono text-base font-semibold text-heading">argos://models</code>
              <p className="mt-3 max-w-2xl text-sm leading-relaxed text-body">
                The full model catalog write-up — architecture, benchmarks, hardware fit, and confidence
                notes for every model Argos knows about. The same content as the{" "}
                <Link href="/docs/models" className="text-teal-700 underline underline-offset-2">
                  Models
                </Link>{" "}
                docs, in prose form for an agent to read directly.
              </p>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}
