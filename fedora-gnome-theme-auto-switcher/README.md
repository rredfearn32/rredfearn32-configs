# Setup

From the directory containing this README file, run:

```
# Create the necessary directories
mkdir -p ~/.local/bin ~/.config/systemd/user

# Create symlinks
ln -sf "$(pwd)/theme-auto.service" ~/.config/systemd/user/theme-auto.service
ln -sf "$(pwd)/theme-auto.timer" ~/.config/systemd/user/theme-auto.timer
ln -sf "$(pwd)/theme_auto.py" ~/.local/bin/theme_auto.py

# Enable and start the service and timer
systemctl --user daemon-reload
systemctl --user enable --now theme-auto.timer
```

You can then use the following commands to verify the results:

```
# Show the next run time
systemctl --user list-timers theme-auto.timer
```
```
# Show the scripts output from each run
journalctl --user -u theme-auto.service -n 20
```

# Running tests

The tests use pytest, installed into a local virtual environment in this directory (nothing is installed system-wide). The script itself still runs on the system Python.

One-time setup, from the directory containing this README file:

```
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
```

Then run the tests with:

```
.venv/bin/pytest -v
```

# Known limitations

The script doesn't handle places within the Arctic or Antarctic circles (above roughly 66.5° latitude, north or south), which get polar night or midnight sun. During midnight sun, there is a gap of a few minutes near solar midnight on some days, when the script wrongly treats it as night and briefly switches to dark mode. Polar night (always dark) works as expected. This isn't tested, because the script is not expected to be used at those latitudes.
