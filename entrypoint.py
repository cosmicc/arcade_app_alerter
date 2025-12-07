#!/usr/bin/env python3
"""
Container entrypoint for Arcade App Alerter.

Responsibilities:
- Start the Flask webserver (webserver.app) on the configured port.
- Run each checker (MAME, LaunchBox, RetroArch, LEDBlinky, ScummVM) on its own
  interval, as defined in config.ini under [scheduler].
- Handle SIGTERM/SIGINT cleanly so Docker stop works as expected.
"""

import os
import sys
import threading
import time
import signal
import configparser
from typing import Callable, Dict

import webserver
import mamecheck
import launchboxcheck
import retroarchcheck
import ledblinkycheck
import scummvmcheck

CONFIG_ENV_VAR = "ARCADE_APP_CONFIG"
DEFAULT_CONFIG_PATH = "/config/arcade_app/config.ini"
CONFIG_PATH = os.environ.get(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH)


def load_scheduler_config(path: str) -> Dict[str, int]:
    """
    Load per-checker intervals (in seconds) from config.ini.

    [scheduler]
    mame_interval       = 21600   ; 6h
    launchbox_interval  = 21600
    retroarch_interval  = 21600
    ledblinky_interval  = 21600
    scummvm_interval    = 21600

    Returns a dict with defaults if section/keys are missing.
    """

    # Reasonable defaults if config missing
    intervals = {
        "mame_interval": 21600,        # 6h
        "launchbox_interval": 21600,   # 6h
        "retroarch_interval": 21600,   # 6h
        "ledblinky_interval": 21600,   # 6h
        "scummvm_interval": 21600,     # 6h
    }

    parser = configparser.ConfigParser()
    read_files = parser.read(path)

    if not read_files:
        print(f"[entrypoint] WARNING: config file {path} not found; using default scheduler intervals.",
              file=sys.stderr)
        return intervals

    if parser.has_section("scheduler"):
        sec = parser["scheduler"]
        for key in list(intervals.keys()):
            try:
                intervals[key] = sec.getint(key, intervals[key])
            except ValueError:
                print(f"[entrypoint] WARNING: invalid integer for [scheduler].{key}, using default {intervals[key]}",
                      file=sys.stderr)
    else:
        print("[entrypoint] WARNING: [scheduler] section missing; using default intervals.",
              file=sys.stderr)

    print("[entrypoint] Scheduler intervals (seconds):", intervals)
    return intervals


def run_checker_loop(name: str, func: Callable[[], int], interval: int, stop_event: threading.Event) -> None:
    """
    Run a checker function periodically until stop_event is set.

    - func() is expected to return an int (0/1), but return value is ignored.
    - interval <= 0 disables the loop (function returns immediately).
    """
    if interval <= 0:
        print(f"[entrypoint] {name}: interval <= 0, checker disabled.")
        return

    print(f"[entrypoint] {name}: starting checker loop with interval {interval}s.")
    while not stop_event.is_set():
        try:
            rc = func()
            print(f"[entrypoint] {name}: checker run completed with exit code {rc}.")
        except Exception as e:
            # Checkers already log internally; this is a last-resort guard.
            print(f"[entrypoint] {name}: unhandled exception in checker: {e}", file=sys.stderr)

        # Sleep in 1-second chunks so we can respond quickly to stop_event
        for _ in range(interval):
            if stop_event.is_set():
                break
            time.sleep(1)


def run_webserver(stop_event: threading.Event) -> None:
    """
    Run the Flask webserver.

    We rely on webserver.FLASK_PORT which is loaded from the same config.ini
    during webserver import.
    """
    port = getattr(webserver, "FLASK_PORT", 5000)
    print(f"[entrypoint] Starting Flask webserver on port {port}.")

    webserver.app.run(host="0.0.0.0", port=port, debug=False, use_reloader=False)


def main() -> int:
    # Load scheduler intervals
    intervals = load_scheduler_config(CONFIG_PATH)

    stop_event = threading.Event()

    # Prepare threads
    threads = []

    # Webserver thread
    t_web = threading.Thread(target=run_webserver, args=(stop_event,), name="webserver", daemon=True)
    threads.append(t_web)

    # Checker threads
    t_mame = threading.Thread(
        target=run_checker_loop,
        args=("MAME", mamecheck.main, intervals["mame_interval"], stop_event),
        name="mamechecker",
        daemon=True,
    )
    t_launchbox = threading.Thread(
        target=run_checker_loop,
        args=("LaunchBox", launchboxcheck.main, intervals["launchbox_interval"], stop_event),
        name="launchboxchecker",
        daemon=True,
    )
    t_retroarch = threading.Thread(
        target=run_checker_loop,
        args=("RetroArch", retroarchcheck.main, intervals["retroarch_interval"], stop_event),
        name="retroarchchecker",
        daemon=True,
    )
    t_ledblinky = threading.Thread(
        target=run_checker_loop,
        args=("LEDBlinky", ledblinkycheck.main, intervals["ledblinky_interval"], stop_event),
        name="ledblinkychecker",
        daemon=True,
    )
    t_scummvm = threading.Thread(
        target=run_checker_loop,
        args=("ScummVM", scummvmcheck.main, intervals["scummvm_interval"], stop_event),
        name="scummvmchecker",
        daemon=True,
    )

    threads.extend([t_mame, t_launchbox, t_retroarch, t_ledblinky, t_scummvm])

    # Signal handlers for clean shutdown
    def handle_signal(signum, frame):
        print(f"[entrypoint] Received signal {signum}, shutting down...")
        stop_event.set()

    signal.signal(signal.SIGTERM, handle_signal)
    signal.signal(signal.SIGINT, handle_signal)

    # Start all threads
    for t in threads:
        t.start()

    print("[entrypoint] All threads started. Service is up.")

    # Keep main thread alive until stop_event is set
    try:
        while not stop_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        handle_signal(signal.SIGINT, None)

    print("[entrypoint] Waiting for threads to finish...")
    for t in threads:
        if t.is_alive():
            t.join(timeout=2.0)

    print("[entrypoint] Exit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
