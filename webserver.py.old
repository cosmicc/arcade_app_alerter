#!/usr/bin/env python3
"""
Arcade App Version Web Dashboard

- Shows current versions and last-checked times for configured apps.
- Reads app status from simple text files (version + date) in a data directory.
- Shows recent log tail from a log file.
- Restricts access by client IP(s) from config.ini.
- All settings (port, allowed hosts, paths, etc.) driven by config.ini.

Intended to be run under Docker or directly on the host.
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

from flask import Flask, request, render_template, abort
import configparser
import re

# ====================================
# CONFIG LOADING
# ====================================

# Environment variable to override config path (for Docker)
CONFIG_ENV_VAR = "ARCADE_APP_CONFIG"
DEFAULT_CONFIG_PATH = "/config/arcade_app/config.ini"

CONFIG_PATH = os.environ.get(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH)

# Defaults (overridden by config.ini)
ALLOWED_HOSTS: List[str] = []       # If empty, no IP restriction
FLASK_PORT: int = 5000
DATA_DIR: str = "./data"
LASTCHECK_FILE: str = "lastcheck"
LOG_PATH: str = "/var/log/arcadecheck.log"
LOG_LINES: int = 20
PAGE_TITLE: str = "Arcade App Version Monitor"

# App config structure:
# apps = mame, launchbox, retroarch, ledblinky
# [app.mame]
# label = MAME
# file = mame.ver
APPS: List[Dict[str, Any]] = []


def load_config(path: str) -> None:
    """
    Load configuration from INI file.

    Sections used:

        [web]
        allowed_hosts = 192.168.199.5, 192.168.199.10
        port = 5000
        data_dir = /data/arcade
        lastcheck_file = lastcheck
        log_path = /var/log/arcadecheck.log
        log_lines = 20
        title = Arcade App Version Monitor

        [apps]
        apps = mame, launchbox, retroarch, ledblinky

        [app.mame]
        label = MAME
        file = mame.ver

        [app.launchbox]
        label = LaunchBox
        file = launchbox.ver

        ... etc ...
    """
    global ALLOWED_HOSTS, FLASK_PORT, DATA_DIR, LASTCHECK_FILE
    global LOG_PATH, LOG_LINES, PAGE_TITLE, APPS

    parser = configparser.ConfigParser()
    read_files = parser.read(path)

    if not read_files:
        print(f"WARNING: config file {path} not found; "
              f"using built-in defaults for web server.",
              file=sys.stderr)
    else:
        # [web]
        if parser.has_section("web"):
            web = parser["web"]

            # allowed_hosts: comma/space separated list
            raw_hosts = web.get("allowed_hosts", "").strip()
            if raw_hosts:
                tokens = re.split(r"[,\s]+", raw_hosts)
                ALLOWED_HOSTS = [t for t in tokens if t]
            else:
                ALLOWED_HOSTS = []

            FLASK_PORT = web.getint("port", FLASK_PORT)
            DATA_DIR = web.get("data_dir", DATA_DIR)
            LASTCHECK_FILE = web.get("lastcheck_file", LASTCHECK_FILE)
            LOG_PATH = web.get("log_path", LOG_PATH)
            LOG_LINES = web.getint("log_lines", LOG_LINES)
            PAGE_TITLE = web.get("title", PAGE_TITLE)
        else:
            print("WARNING: [web] section missing in config; using defaults.",
                  file=sys.stderr)

    # Normalize paths
    DATA_DIR = os.path.abspath(DATA_DIR)
    LASTCHECK_FILE_PATH = os.path.join(DATA_DIR, LASTCHECK_FILE)
    # Keep LASTCHECK_FILE as basename, we use helper to join paths later
    # But we may want the absolute path for sanity
    # (we'll re-construct full path with DATA_DIR in code)

    # Apps
    APPS = []
    if parser.has_section("apps"):
        apps_raw = parser["apps"].get("apps", "").strip()
        if apps_raw:
            app_names = [a.strip() for a in apps_raw.split(",") if a.strip()]
        else:
            app_names = []
    else:
        app_names = []

    for app_name in app_names:
        section = f"app.{app_name}"
        if not parser.has_section(section):
            print(f"WARNING: missing section [{section}] for app '{app_name}'",
                  file=sys.stderr)
            continue

        sec = parser[section]
        label = sec.get("label", app_name)
        file_name = sec.get("file", f"{app_name}.ver")

        APPS.append(
            {
                "name": app_name,
                "label": label,
                "file": file_name,
            }
        )

    if not APPS:
        print("WARNING: no apps configured under [apps]; dashboard will be empty.",
              file=sys.stderr)

    # Log some summary
    print("[webserver] Loaded config:")
    print(f"  CONFIG_PATH   = {path}")
    print(f"  DATA_DIR      = {DATA_DIR}")
    print(f"  LASTCHECK     = {LASTCHECK_FILE}")
    print(f"  LOG_PATH      = {LOG_PATH}")
    print(f"  LOG_LINES     = {LOG_LINES}")
    print(f"  FLASK_PORT    = {FLASK_PORT}")
    print(f"  ALLOWED_HOSTS = {ALLOWED_HOSTS}")
    print(f"  APPS          = {[a['name'] for a in APPS]}")


# Load configuration at import time
load_config(CONFIG_PATH)

# ====================================
# HELPERS
# ====================================

def elapsed_time(start_time: str, withsecs: bool, append: Optional[str] = None) -> str:
    """
    Convert string representation of datetime to elapsed time string.

    Args:
        start_time (str): Start time in the format 'MM-DD-YYYY HH:MM:SS' if withsecs,
                          otherwise 'MM-DD-YYYY'.
        withsecs (bool): Whether the input contains seconds.
        append (str, optional): String appended at the end, e.g. "ago".

    Returns:
        str: A human-readable elapsed time like '1 Hour, 45 Minutes' or
             'Today' / 'Yesterday' if withsecs=False and dates match.
    """
    if not start_time:
        return "Unknown"

    try:
        if withsecs:
            datetime_format = "%m-%d-%Y %H:%M:%S"
        else:
            datetime_format = "%m-%d-%Y"

        start_dt = datetime.strptime(start_time, datetime_format)
    except ValueError:
        return "Invalid date"

    now = datetime.now()

    if not withsecs:
        # Special cases for dates only
        if start_dt.date() == now.date():
            return "Today"
        elif start_dt.date() == (now.date() - timedelta(days=1)):
            return "Yesterday"

    seconds = int((now - start_dt).total_seconds())
    if seconds < 0:
        seconds = 0

    intervals = (
        ("Years",   31536000),
        ("Months",  2592000),
        ("Weeks",   604800),
        ("Days",    86400),
        ("Hours",   3600),
        ("Minutes", 60),
        ("Seconds", 1),
    )

    result = []
    for name, count in intervals:
        value = seconds // count
        if value:
            seconds -= value * count
            if value == 1:
                name = name.rstrip("s")
            result.append(f"{int(value)} {name}")
            if len(result) == 2:
                break

    if not result:
        result = ["0 Seconds"]

    if append:
        return ", ".join(result) + f" {append}"
    return ", ".join(result)


def read_text_lines(path: str) -> List[str]:
    """
    Read all lines from a text file, stripping trailing newlines.
    Returns [] if the file does not exist or cannot be read.
    """
    if not os.path.exists(path):
        return []

    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            return [line.rstrip("\n") for line in f]
    except OSError as e:
        print(f"ERROR: unable to read file '{path}': {e}", file=sys.stderr)
        return []


def tail_file(path: str, max_lines: int) -> str:
    """
    Read the last max_lines lines from a text file.
    Returns an empty string if file is missing or unreadable.
    """
    lines = read_text_lines(path)
    if not lines:
        return ""
    if max_lines <= 0:
        return "\n".join(lines)
    return "\n".join(lines[-max_lines:])


def load_lastcheck() -> Dict[str, Any]:
    """
    Load last-check information from LASTCHECK_FILE in DATA_DIR.

    Expected format:
        line 0: MM-DD-YYYY HH:MM:SS
        line 1: last checked app name or description
    """
    path = os.path.join(DATA_DIR, LASTCHECK_FILE)
    lines = read_text_lines(path)
    if len(lines) < 2:
        return {
            "date_raw": "",
            "date_display": "Unknown",
            "app": "Unknown",
            "elapsed": "Unknown",
        }

    date_raw = lines[0].strip()
    app = lines[1].strip()
    elapsed = elapsed_time(date_raw, withsecs=True, append="ago")

    return {
        "date_raw": date_raw,
        "date_display": date_raw,
        "app": app,
        "elapsed": elapsed,
    }


def load_app_status(app: Dict[str, Any]) -> Dict[str, Any]:
    """
    Load version & date info for a single app from its .ver file.

    Expected file contents:
        line 0: version string
        line 1: date string in format 'MM-DD-YYYY'
    """
    file_name = app.get("file")
    label = app.get("label", app.get("name", "Unknown"))
    path = os.path.join(DATA_DIR, file_name)

    lines = read_text_lines(path)
    if len(lines) < 2:
        return {
            "name": app.get("name"),
            "label": label,
            "version": "Unknown",
            "date_raw": "",
            "date_display": "Unknown",
            "elapsed": "Unknown",
        }

    version = lines[0].strip()
    date_raw = lines[1].strip()
    elapsed = elapsed_time(date_raw, withsecs=False, append="ago")

    return {
        "name": app.get("name"),
        "label": label,
        "version": version,
        "date_raw": date_raw,
        "date_display": date_raw,
        "elapsed": elapsed,
    }


# ====================================
# FLASK APP
# ====================================

app = Flask(__name__)


@app.before_request
def limit_remote_addr():
    """
    Restrict access based on client IP address.

    - If ALLOWED_HOSTS is empty, no restriction is applied.
    - Otherwise, request.remote_addr must be in ALLOWED_HOSTS.
    """
    if not ALLOWED_HOSTS:
        return

    client_ip = request.remote_addr
    if client_ip not in ALLOWED_HOSTS:
        return "You're not allowed to access this resource", 403


@app.route("/")
def index():
    # Last check info
    lastcheck = load_lastcheck()

    # Per-app status
    app_statuses = [load_app_status(a) for a in APPS]

    # Log tail
    log_tail = tail_file(LOG_PATH, LOG_LINES)

    return render_template(
        "index.html",
        page_title=PAGE_TITLE,
        lastcheck=lastcheck,
        apps=app_statuses,
        log_tail=log_tail,
        log_path=LOG_PATH,
        log_lines=LOG_LINES,
    )


@app.route("/health")
def health():
    """
    Simple health endpoint for Docker healthcheck:
    - Returns 200 if the app can load config and render a basic response.
    """
    return "OK", 200


if __name__ == "__main__":
    # When running directly, use config-defined port
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=False)
