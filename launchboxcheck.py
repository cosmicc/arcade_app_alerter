#!/usr/bin/env python3
"""
LaunchBox Version Checker

- Scrapes the LaunchBox changelog page to detect the latest stable release.
- Compares against the locally stored version in data_dir/launchbox.ver.
- On change, updates the version file, records last-check info, and sends a
  Pushover notification.
- Logs all actions to /var/log/arcadecheck.log (or the path defined in config.ini).

Expected version file format (launchbox.ver):
    line 0: version string (e.g. "13.24")
    line 1: date string   (e.g. "03-05-2025" in %m-%d-%Y)

Expected lastcheck file format (shared across all checkers):
    line 0: timestamp string   "%m-%d-%Y %H:%M:%S"
    line 1: app label string   (e.g. "LaunchBox")

This script is intended to be run periodically (cron / scheduler / Docker) and
share config + data_dir + log_path with the arcade web dashboard.
"""

import os
import sys
import re
import configparser
from datetime import datetime
from typing import Optional, Tuple, List

import requests
from bs4 import BeautifulSoup

# ==========================
# CONFIG / GLOBALS
# ==========================

CONFIG_ENV_VAR = "ARCADE_APP_CONFIG"
DEFAULT_CONFIG_PATH = "/config/arcade_app/config.ini"

CONFIG_PATH = os.environ.get(CONFIG_ENV_VAR, DEFAULT_CONFIG_PATH)

# Defaults (overridden by config.ini)
LAUNCHBOX_URL = "https://www.launchbox-app.com/about/changelog"
DATA_DIR = "./data"
VERSION_FILE = "launchbox.ver"
LASTCHECK_FILE = "lastcheck"
LOG_PATH = "/var/log/arcadecheck.log"
LAUNCHBOX_LABEL = "LaunchBox"

PUSHOVER_TOKEN: Optional[str] = None
PUSHOVER_USER: Optional[str] = None
PUSHOVER_DEVICE: Optional[str] = None
PUSHOVER_PRIORITY: int = 0
PUSHOVER_ENABLED: bool = False
NOTIFY_ON_UPDATE: bool = True
NOTIFY_ON_ERROR: bool = True


def load_config(path: str) -> None:
    """
    Load settings from config.ini.

    Relevant sections/keys:

        [web]
        data_dir       = /data/arcade_app
        lastcheck_file = lastcheck
        log_path       = /var/log/arcadecheck.log

        [launchbox]
        url             = https://www.launchbox-app.com/about/changelog
        version_file    = launchbox.ver
        label           = LaunchBox
        notify_on_update = true
        notify_on_error  = true

        [pushover]
        token    = <app token>
        user     = <user key>
        device   =
        priority = 0
        enabled  = true
    """
    global LAUNCHBOX_URL, DATA_DIR, VERSION_FILE, LASTCHECK_FILE, LOG_PATH, LAUNCHBOX_LABEL
    global PUSHOVER_TOKEN, PUSHOVER_USER, PUSHOVER_DEVICE, PUSHOVER_PRIORITY
    global PUSHOVER_ENABLED, NOTIFY_ON_UPDATE, NOTIFY_ON_ERROR

    parser = configparser.ConfigParser()
    read_files = parser.read(path)

    if not read_files:
        print(f"WARNING: config file {path} not found; using built-in defaults.",
              file=sys.stderr)

    # Shared paths with web dashboard
    if parser.has_section("web"):
        web = parser["web"]
        DATA_DIR = web.get("data_dir", DATA_DIR)
        LASTCHECK_FILE = web.get("lastcheck_file", LASTCHECK_FILE)
        LOG_PATH = web.get("log_path", LOG_PATH)

    # LaunchBox-specific settings
    if parser.has_section("launchbox"):
        lb = parser["launchbox"]
        LAUNCHBOX_URL = lb.get("url", LAUNCHBOX_URL)
        VERSION_FILE = lb.get("version_file", VERSION_FILE)
        LAUNCHBOX_LABEL = lb.get("label", LAUNCHBOX_LABEL)
        NOTIFY_ON_UPDATE = lb.getboolean("notify_on_update", NOTIFY_ON_UPDATE)
        NOTIFY_ON_ERROR = lb.getboolean("notify_on_error", NOTIFY_ON_ERROR)

    # Pushover settings
    if parser.has_section("pushover"):
        po = parser["pushover"]
        PUSHOVER_TOKEN = po.get("token", "").strip() or None
        PUSHOVER_USER = po.get("user", "").strip() or None
        PUSHOVER_DEVICE = po.get("device", "").strip() or None
        PUSHOVER_PRIORITY = po.getint("priority", 0)
        PUSHOVER_ENABLED = po.getboolean("enabled", True) and bool(
            PUSHOVER_TOKEN and PUSHOVER_USER
        )
    else:
        PUSHOVER_ENABLED = False

    # Normalize paths
    DATA_DIR = os.path.abspath(DATA_DIR)
    LOG_PATH = os.path.abspath(LOG_PATH)

    print("[launchboxcheck] Loaded config:")
    print(f"  CONFIG_PATH      = {path}")
    print(f"  LAUNCHBOX_URL    = {LAUNCHBOX_URL}")
    print(f"  DATA_DIR         = {DATA_DIR}")
    print(f"  VERSION_FILE     = {VERSION_FILE}")
    print(f"  LASTCHECK_FILE   = {LASTCHECK_FILE}")
    print(f"  LOG_PATH         = {LOG_PATH}")
    print(f"  LAUNCHBOX_LABEL  = {LAUNCHBOX_LABEL}")
    print(f"  PUSHOVER_ENABLED = {PUSHOVER_ENABLED}")


# Load config at import
load_config(CONFIG_PATH)

# ==========================
# LOGGING & PUSHOVER
# ==========================

def logf(ok: bool, message: str) -> None:
    """
    Append a log line to LOG_PATH.

    Format:
        YYYY-MM-DD HH:MM:SS (+) Message...
        YYYY-MM-DD HH:MM:SS (-) Message...
    """
    status = "(+)" if ok else "(-)"
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{ts} {status} {message}\n"

    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(line)
    except OSError as e:
        print(f"ERROR: unable to write log file '{LOG_PATH}': {e}",
              file=sys.stderr)


def send_pushover(title: str, message: str, priority: Optional[int] = None) -> None:
    """
    Send a Pushover notification, if enabled.

    Uses HTTP API directly via requests. Errors are logged but do not raise.
    """
    if not PUSHOVER_ENABLED:
        return

    prio = PUSHOVER_PRIORITY if priority is None else priority

    payload = {
        "token": PUSHOVER_TOKEN,
        "user": PUSHOVER_USER,
        "title": title,
        "message": message,
        "priority": str(prio),
    }
    if PUSHOVER_DEVICE:
        payload["device"] = PUSHOVER_DEVICE

    try:
        resp = requests.post("https://api.pushover.net/1/messages.json",
                             data=payload, timeout=10)
        if resp.status_code != 200:
            logf(False, f"Pushover API error {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        logf(False, f"Failed to send Pushover notification: {e}")


# ==========================
# FILE HELPERS
# ==========================

def read_local_version() -> Optional[str]:
    """
    Read the currently stored LaunchBox version from VERSION_FILE in DATA_DIR.

    Returns the version string, or None if the file doesn't exist or is invalid.
    """
    path = os.path.join(DATA_DIR, VERSION_FILE)
    if not os.path.exists(path):
        logf(False, f"LaunchBox: local version file not found at {path}")
        return None

    try:
        with open(path, "r", encoding="utf-8") as f:
            first_line = f.readline().strip()
            return first_line or None
    except OSError as e:
        logf(False, f"LaunchBox: error reading local version file '{path}': {e}")
        return None


def write_local_version(version: str, date_str: str) -> None:
    """
    Write the updated version and date to VERSION_FILE in DATA_DIR.

    Format:
        line 0: version
        line 1: date (%m-%d-%Y)
    """
    path = os.path.join(DATA_DIR, VERSION_FILE)
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{version}\n")
            f.write(f"{date_str}\n")
    except OSError as e:
        logf(False, f"LaunchBox: error writing local version file '{path}': {e}")


def update_lastcheck(timestamp_str: str, label: str) -> None:
    """
    Update the shared "lastcheck" file with the latest run.

    Format:
        line 0: timestamp (%m-%d-%Y %H:%M:%S)
        line 1: app label (e.g. "LaunchBox")
    """
    path = os.path.join(DATA_DIR, LASTCHECK_FILE)
    os.makedirs(DATA_DIR, exist_ok=True)
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"{timestamp_str}\n")
            f.write(f"{label}\n")
    except OSError as e:
        logf(False, f"LaunchBox: error writing lastcheck file '{path}': {e}")


# ==========================
# HTML FETCH + PARSING
# ==========================

def fetch_launchbox_page(url: str) -> str:
    """
    Retrieve the HTML content of the LaunchBox changelog page.

    Raises RuntimeError on HTTP/network issues.
    """
    try:
        resp = requests.get(url, timeout=20)
    except Exception as e:
        raise RuntimeError(f"HTTP request failed: {e}") from e

    if resp.status_code != 200:
        raise RuntimeError(f"Unexpected HTTP status {resp.status_code}")

    return resp.text


def parse_launchbox_versions(html: str) -> Tuple[str, bool]:
    """
    Parse the LaunchBox changelog HTML and extract the latest release version.

    Strategy:
      - Find all <h4> elements.
      - For each, look for "Version X.YY" via regex.
      - Mark entries as "beta" if the heading contains '?' or 'beta'.
      - Prefer the first NON-beta version; if all are beta, use the first one.

    Returns:
        (version_str, is_beta)

    Raises:
        ValueError if no version headings can be found.
    """
    soup = BeautifulSoup(html, "html.parser")
    h4s = soup.find_all("h4")

    candidates: List[Tuple[str, bool]] = []

    for h in h4s:
        text = " ".join(h.get_text(strip=True).split())
        m = re.search(r"\bVersion\s+([0-9.]+)\b", text, flags=re.IGNORECASE)
        if not m:
            continue

        ver = m.group(1)
        lower = text.lower()
        is_beta = ("beta" in lower) or ("?" in text)
        candidates.append((ver, is_beta))

    if not candidates:
        snippet = soup.get_text(" ", strip=True)[:200]
        raise ValueError(
            "Could not find any 'Version X.Y' headings on LaunchBox changelog page. "
            f"First 200 chars: {snippet!r}"
        )

    # Prefer first non-beta, fall back to first candidate
    for ver, is_beta in candidates:
        if not is_beta:
            return ver, False

    return candidates[0]


# ==========================
# MAIN
# ==========================

def main() -> int:
    """
    Main entry point.

    - Fetch LaunchBox changelog
    - Parse latest version
    - Compare with local version
    - Update files, log, and notify as needed
    """
    now = datetime.now()
    now_date = now.strftime("%m-%d-%Y")
    now_ts = now.strftime("%m-%d-%Y %H:%M:%S")

    # Record this check in the lastcheck file regardless of outcome
    update_lastcheck(now_ts, LAUNCHBOX_LABEL)

    try:
        html = fetch_launchbox_page(LAUNCHBOX_URL)
    except Exception as e:
        msg = f"LaunchBox ERROR: failed to fetch changelog page: {e}"
        logf(False, msg)
        if NOTIFY_ON_ERROR:
            send_pushover("LaunchBox Check Error", msg)
        return 1

    try:
        new_version, is_beta = parse_launchbox_versions(html)
    except Exception as e:
        msg = f"LaunchBox ERROR: failed to parse version from changelog: {e}"
        logf(False, msg)
        if NOTIFY_ON_ERROR:
            send_pushover("LaunchBox Check Error", msg)
        return 1

    local_version = read_local_version()

    if local_version is None:
        logf(False, f"LaunchBox: no local version found; treating {new_version} as new.")
    else:
        logf(
            True,
            f"LaunchBox: local version {local_version}, changelog reports {new_version}"
            + (" (beta)" if is_beta else ""),
        )

    if local_version == new_version:
        logf(True, f"LaunchBox: version {local_version} is current.")
        return 0

    # New version detected
    logf(
        True,
        f"LaunchBox: new version detected. Local={local_version or 'none'}, "
        f"Changelog={new_version}{' (beta)' if is_beta else ''}",
    )
    write_local_version(new_version, now_date)

    if NOTIFY_ON_UPDATE:
        suffix = " (beta)" if is_beta else ""
        send_pushover(
            "New LaunchBox Version",
            f"New LaunchBox version {new_version}{suffix} is available.",
        )

    return 0


if __name__ == "__main__":
    rc = main()
    sys.exit(rc)
