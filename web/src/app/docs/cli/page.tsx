import { CommandBlock, type CommandSpec } from "@/components/docs/CommandBlock";
import { CliTerminal } from "@/components/docs/CliTerminal";
import { StickyNav, type NavSection } from "@/components/docs/StickyNav";

const sections: NavSection[] = [
  { id: "overview", label: "Overview" },
  { id: "installation", label: "Installation" },
  { id: "commands", label: "Commands" },
];

const commands: CommandSpec[] = [
  {
    name: "list",
    syntax: "argos list",
    description:
      "Shows the full model catalog and flags which ones are already pulled onto this machine. This is usually the first command you run — it's how you find out what's available before committing to a multi-gigabyte download.",
    example: [
      { type: "command", text: "argos list" },
      { type: "output", text: "No models have been pulled yet." },
      { type: "output", text: "smolvla         [not pulled]" },
      { type: "output", text: "pi0             [not pulled]" },
      { type: "output", text: "bitvla          [not pulled]" },
    ],
  },
  {
    name: "pull",
    syntax: "argos pull <model>",
    description:
      "Downloads a model's weights from Hugging Face into the daemon's local cache. The model name must match one from `argos list`. This can take a while for larger models — the daemon shows a live progress spinner while it downloads.",
    options: [{ flag: "model", description: "Required. Model name from the catalog, e.g. smolvla." }],
    example: [
      { type: "command", text: "argos pull smolvla" },
      { type: "success", text: "Pulled smolvla -> .../services/models/smolvla-libero.gguf" },
    ],
  },
  {
    name: "connect actuator",
    syntax: "argos connect actuator [--port PORT] [--servo-id ID]",
    description:
      "Connects the robot arm over the Feetech servo protocol. Run it with no arguments first — it scans and lists every serial port it can see, so you can figure out which one is actually your arm before connecting to it. Once you know the port, connecting does a real handshake: it pings each servo ID and only counts the connection as live if servos actually respond, not just because the port opened.",
    options: [
      { flag: "--port", description: "Serial port, e.g. /dev/ttyUSB0. Omit to list available ports instead." },
      {
        flag: "--servo-id",
        description: "A servo ID to ping. Repeatable. Omit to use the default set for the reference arm.",
      },
    ],
    example: [
      { type: "command", text: "argos connect actuator" },
      { type: "output", text: "/dev/ttyUSB0         USB-Serial Controller" },
      { type: "command", text: "argos connect actuator --port /dev/ttyUSB0" },
      { type: "success", text: "Connected /dev/ttyUSB0: responded=[1, 2, 3, 4, 5, 6] unresponsive=[]" },
    ],
  },
  {
    name: "connect sensor",
    syntax: "argos connect sensor [--index N] [--view NAME]",
    description:
      "Connects a camera under a named view. Just like connect actuator, running it with no arguments discovers what's available first. The --view name isn't just a label — it has to match one of the view names the model you're about to run actually expects, so the right camera feed ends up in the right slot instead of being guessed from connection order.",
    options: [
      { flag: "--index", description: "Camera index. Omit to discover available cameras." },
      { flag: "--view", description: "View name — must match the model's expected camera view key exactly." },
    ],
    example: [
      { type: "command", text: "argos connect sensor" },
      { type: "output", text: "index 0" },
      { type: "output", text: "index 1" },
      { type: "command", text: "argos connect sensor --index 0 --view observation.images.image" },
      { type: "success", text: "Connected camera 0 as 'observation.images.image'" },
    ],
  },
  {
    name: "run",
    syntax: "argos run <model> <instruction>",
    description:
      "Starts the model running. This is the command that actually moves the arm: it checks that the model is pulled and that both the actuator and required cameras are connected, spawns the inference engine, and kicks off the control loop. The instruction is a plain-language description of what you want the robot to do — it gets fed straight to the model alongside the camera feed.",
    options: [
      { flag: "model", description: "Required. Model name to run, e.g. smolvla." },
      { flag: "instruction", description: "Required. Natural-language task instruction for the robot." },
    ],
    example: [
      { type: "command", text: 'argos run smolvla "pick up the red block"' },
      { type: "success", text: "Running smolvla (pid=48213, bind=tcp://127.0.0.1:5555)" },
    ],
  },
  {
    name: "devices",
    syntax: "argos devices [--kind actuator|sensor]",
    description:
      "Lists whatever's currently connected — useful as a sanity check before running, or any time you've lost track of what's plugged in. Filter to just one kind if you don't need the full picture.",
    options: [{ flag: "--kind", description: "Optional. Filter to 'actuator' or 'sensor'. Omit to show both." }],
    example: [
      { type: "command", text: "argos devices" },
      { type: "output", text: "{'actuator': {'port': '/dev/ttyUSB0', 'servo_ids': [1, 2, 3, 4, 5, 6]}," },
      { type: "output", text: " 'sensors': [{'index': 0, 'view_name': 'observation.images.image'}]}" },
    ],
  },
];

const inSessionCommands: CommandSpec[] = [
  {
    name: "logs",
    syntax: "GET /cli/logs",
    description:
      "Returns both the inference engine's raw output and Argos's own pipeline log (frame captured, request sent, response received, correction applied) — everything that's happened since the run started. Today this lives on the daemon's API; a native `argos logs` command that talks to it while a run is active is coming.",
    planned: true,
    example: [{ type: "output", text: "$ curl http://127.0.0.1:8000/cli/logs" }],
  },
  {
    name: "status",
    syntax: "GET /cli/status",
    description:
      "Reports what model is loaded, which devices are connected, and how long the daemon and the current run have each been up. Same story as logs — available on the daemon today, landing as a CLI command next.",
    planned: true,
    example: [{ type: "output", text: "$ curl http://127.0.0.1:8000/cli/status" }],
  },
  {
    name: "stop",
    syntax: "POST /cli/stop",
    description:
      "Safely ends the active run: stops the control loop, drives the arm back to a home position, and shuts down the inference engine — the daemon itself keeps running throughout, ready for the next run.",
    planned: true,
    example: [{ type: "output", text: "$ curl -X POST http://127.0.0.1:8000/cli/stop" }],
  },
];

export default function CliDocsPage() {
  return (
    <div className="mx-auto max-w-4xl px-8 py-12 sm:px-12">
      <div className="max-w-2xl">
        <h1 className="text-2xl font-semibold text-heading">CLI</h1>
        <p className="mt-3 text-base text-body">
          Reference for every Argos CLI command — what it does, what it takes, and how to use it.
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
              The Argos CLI is how you talk to the daemon running on your robot&apos;s machine — it
              doesn&apos;t do any of the real work itself. Pulling model weights, opening a serial
              connection to a servo, spawning the inference engine, running the control loop: all of
              that happens inside a long-running background process, started once and left running.
              Every CLI command is really just an HTTP request to that daemon, wrapped in a clean
              terminal interface with readable errors and correct exit codes.
            </p>
            <p>
              That split matters in practice. Starting a run doesn&apos;t tie up your terminal — you
              can close it, come back later, and the robot is still doing whatever you told it to do.
              And if a command fails because the daemon isn&apos;t running, you get a clear message
              telling you how to fix that, not a stack trace.
            </p>
          </div>
        </section>

        <section id="installation">
          <h2 className="font-mono text-sm text-teal-700">Installation</h2>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-body">
            One command installs everything: system dependencies, a Python virtual environment, the
            inference engine built from source with GPU detection (Jetson, desktop GPU, or a CPU-only
            fallback), and the daemon itself as a systemd service.
          </p>
          <div className="mt-5">
            <CliTerminal lines={[{ type: "command", text: "curl -fsSL https://argos.sh/install | bash" }]} />
          </div>
          <p className="mt-5 max-w-2xl text-base leading-relaxed text-body">
            The daemon is enabled but not started automatically — add your Hugging Face token to{" "}
            <code className="rounded bg-surface-alt px-1.5 py-0.5 font-mono text-sm text-heading">
              local/.env
            </code>{" "}
            first, then start it:
          </p>
          <div className="mt-5">
            <CliTerminal lines={[{ type: "command", text: "sudo systemctl start argos" }]} />
          </div>
        </section>

        <section id="commands">
          <h2 className="font-mono text-sm text-teal-700">Commands</h2>
          <p className="mt-3 max-w-2xl text-base leading-relaxed text-body">
            Every command below follows the same shape: a verb, sometimes a model or device argument,
            and options for anything optional. The two connect commands share a pattern worth calling
            out — run them with no arguments to discover what&apos;s available, then run them again
            with the specific one you want.
          </p>

          <div className="mt-8 flex flex-col gap-5">
            {commands.map((command) => (
              <CommandBlock key={command.name} command={command} />
            ))}
          </div>

          <div className="mt-10 max-w-2xl">
            <h3 className="font-mono text-sm font-medium text-heading">In-session commands</h3>
            <p className="mt-2 text-sm leading-relaxed text-body">
              While a run is active, three more operations are available: checking logs, checking
              status, and safely stopping. These exist today as routes on the daemon&apos;s own API —
              wiring them into the CLI as interactive commands you can type while a run is in progress
              is next.
            </p>
          </div>

          <div className="mt-5 flex flex-col gap-5">
            {inSessionCommands.map((command) => (
              <CommandBlock key={command.name} command={command} />
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
