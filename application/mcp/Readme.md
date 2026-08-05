# Argos -- agent guide

Reference material for an AI agent (e.g. Claude) talking to a user through
this MCP server. Exposed as the `argos://guide` resource -- read it to
understand what Argos is, how its pieces fit together, and what every
`argos` CLI command does, including the ones this MCP server does **not**
expose, so you can still explain them accurately to the user.

## What Argos is

Argos connects and runs VLA (vision-language-action) models on real robot
hardware -- pairing a robot arm (Feetech servos over serial) and one or more
USB cameras with a local vision-language-action model, so a natural-language
instruction like "pick up the red block" turns into actual joint commands.
See the `argos://models` resource for the full model catalog (architectures,
benchmarks, hardware fit).

## How the pieces fit together

- **The daemon** (`application/server/local`) is the only thing that ever
  touches hardware. A FastAPI process, normally running as a systemd service
  on the robot, that owns the actuator connection, camera connections, the
  `vla-server` inference engine subprocess, and the PID control loop that
  drives the arm. Everything else is a client of it over HTTP
  (`http://127.0.0.1:8000`).
- **The CLI** (`application/cli`, the `argos` command) is a thin Typer
  wrapper the *user* runs directly -- every command just calls the daemon's
  HTTP API and prints the result.
- **This MCP server** (`application/mcp`) is the same kind of thin HTTP
  client of the daemon, but for you (the agent) instead of a terminal. It is
  intentionally a **subset** of the CLI -- see below.

## What this MCP server can and can't do

Available to you as tools: `connect_actuator`, `connect_sensor`, `devices`,
`list_models`, `pull_model`, `status`, `logs`, `stop`.

**`run` is deliberately not available to you.** Starting a run spawns the
inference engine and begins actively writing goal positions to the arm's
servos -- real, physical actuation. That decision is left to the user, who
runs it themselves via the CLI. You can help them get everything in place
(hardware connected, model pulled, cameras on the right views) and explain
exactly what command they need, but you should never represent yourself as
able to start or steer the arm, and there is no tool call available to you
that does so. `stop` is the one exception -- it's a safety/halt action, not
task execution: it only ever drives the arm to a fixed home position as part
of shutting an active run down.

## Typical workflow to walk a user through

1. `status` -- see what's already connected/running.
2. `connect_actuator` with no args to list serial ports, then again with
   `port` set to actually connect.
3. `connect_sensor` with no args to discover cameras, then again with
   `index` + `view_name` for each camera view the target model needs (see
   `camera_views` in the model catalog).
4. `list_models` / `pull_model` to get the model's weights onto the machine.
5. Hand off: tell the user to run `argos run <model> "<instruction>"`
   themselves in a terminal -- that's the one step you don't do for them.

## Full CLI command reference (`argos --help`)

```
argos list
    List the model catalog and show which ones are already pulled locally.

argos pull MODEL
    Download a model's weights from Hugging Face into the local cache.
    MODEL -- name from the catalog, e.g. "smolvla".

argos run MODEL INSTRUCTION
    Start running a model: spawns the inference engine and begins the
    control loop. Not available via MCP -- see above.
    MODEL       -- model name to run, e.g. "smolvla".
    INSTRUCTION -- natural-language task instruction for the robot.

argos connect actuator [--port PORT] [--servo-id ID ...]
    Connect the actuator over the Feetech protocol, or list available
    ports if --port is omitted.
    --port      -- serial port, e.g. /dev/ttyUSB0. Omit to list ports.
    --servo-id  -- servo ID to ping. Repeatable. Omit for the default set.

argos connect sensor [--index INDEX] [--view VIEW]
    Connect a camera under a named view, or discover available cameras
    if --index is omitted.
    --index -- camera index. Omit to discover available cameras.
    --view  -- view name -- must match the model's expected
               camera_views key.

argos devices [--kind KIND]
    List connected actuator and sensor devices.
    --kind -- filter: "actuator" or "sensor".

argos status
    Show what's loaded, what's connected, and how long the
    daemon/run have been up.

argos logs [--source SOURCE] [--limit LIMIT]
    Show recent log lines from the inference engine and/or the
    active run.
    --source -- filter: "engine" or "run". Omit to show both.
    --limit  -- number of most-recent log lines to show (default 50).

argos stop
    Safely stop the active run: halts control, drives the arm home,
    tears down the engine.
```

The daemon must be running for any of the above (CLI or MCP) to work:
`sudo systemctl start argos`, or `uvicorn application.server.local.app:app`
directly during development.
