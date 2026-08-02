# Installing Argos

```
bash install/install.sh
```

This detects your GPU (Jetson first, then desktop NVIDIA via `nvidia-smi`,
then falls back to a much slower CPU build), installs system + Python
dependencies, builds the `vla-server` binary from the vendored `vla.cpp`
engine, and installs the daemon as a systemd service (`argos.service`) —
enabled, but not started yet.

## Before starting the daemon

Set your Hugging Face token so model pulls work:

```
echo "HUGGING_FACE_TOKEN=<your token>" > application/server/local/.env
```

## Running the daemon

The daemon is `application/server/local/app.py`, served by `uvicorn` at
`http://127.0.0.1:8000`.

```
sudo systemctl start argos      # start it
sudo systemctl status argos     # check it's up
journalctl -u argos -f          # follow its logs
sudo systemctl stop argos       # stop it
```

## Using the CLI

`install.sh` also installs `argos` itself as a command on your `PATH`, talking to
the daemon over HTTP:

```
argos list                                     # show the model catalog
argos pull smolvla                             # download a model's weights
argos connect actuator                         # list serial ports
argos connect actuator --port /dev/ttyUSB0     # connect to one
argos connect sensor                           # discover cameras
argos connect sensor --index 0 --view <name>   # connect one under a view
argos devices                                  # list what's connected
argos run smolvla "pick up the red block"      # start a run
```
