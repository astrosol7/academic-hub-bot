"""
 ██████  ██████  ██████  ██ ████████
██    ██ ██   ██ ██   ██ ██    ██
██    ██ ██████  ██████  ██    ██
██    ██ ██   ██ ██   ██ ██    ██
 ██████  ██   ██ ██████  ██    ██

Station Orbit Launcher — V1.0 Stable
Academic Hub | SIT
"""

import os
import sys
import subprocess
import time
import socket
import webbrowser
from pathlib import Path
from typing import Dict, Optional

# Force UTF-8 output on Windows terminals
if sys.platform == 'win32':
    os.system('')  # Enable ANSI escape codes on Windows 10+
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# ── ENV LOADER ──────────────────────────────────────────────────
def _load_env():
    env_file = Path(__file__).parent / ".env"
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip("'\"")
                    os.environ[key] = value

_load_env()

# ── ANSI CODES ──────────────────────────────────────────────────
R   = "\033[0m"
B   = "\033[1m"
DIM = "\033[2m"
CY  = "\033[96m"
GR  = "\033[92m"
RD  = "\033[91m"
YL  = "\033[93m"
MG  = "\033[95m"
WH  = "\033[97m"
GY  = "\033[90m"

ORBIT_LOGO = f"""
{CY}{B}    ================================================================={R}
{CY}{B}    ||                                                             ||{R}
{CY}{B}    ||{MG}   ██████  ██████  ██████  ██ ████████                       {CY}||{R}
{CY}{B}    ||{MG}  ██    ██ ██   ██ ██   ██ ██    ██                          {CY}||{R}
{CY}{B}    ||{MG}  ██    ██ ██████  ██████  ██    ██                          {CY}||{R}
{CY}{B}    ||{MG}  ██    ██ ██   ██ ██   ██ ██    ██                          {CY}||{R}
{CY}{B}    ||{MG}   ██████  ██   ██ ██████  ██    ██                          {CY}||{R}
{CY}{B}    ||                                                             ||{R}
{CY}{B}    ||{WH}       S T A T I O N   O R B I T   |   V 1 . 0{R}{CY}{B}              ||{R}
{CY}{B}    ||{GY}           Academic Hub  ·  SIT  ·  Stable Release{R}{CY}{B}           ||{R}
{CY}{B}    ||                                                             ||{R}
{CY}{B}    ================================================================={R}
"""

# ── UI HELPERS ──────────────────────────────────────────────────
def _clear():
    os.system('cls' if os.name == 'nt' else 'clear')

def _phase(label: str):
    print(f"\n  {CY}{B}[ORBIT]{R} {WH}{label}{R}", flush=True)

def _status(label: str, ok: bool, detail: str = ""):
    tag = f"{GR}ONLINE{R}" if ok else f"{RD}FAILED{R}"
    pad = 32 - len(label)
    extra = f"  {GY}{detail}{R}" if detail else ""
    print(f"    {DIM}>{R} {label}{'.' * max(pad, 2)} {tag}{extra}", flush=True)

def _scan(label: str, steps: int = 20, duration: float = 0.4):
    for i in range(steps + 1):
        filled = "█" * i + "░" * (steps - i)
        print(f"\r    {GY}>{R} {label}  [{CY}{filled}{R}] {int(i / steps * 100)}%", end="", flush=True)
        time.sleep(duration / steps)
    print(flush=True)


# ── PORT UTILITIES ──────────────────────────────────────────────
def _port_open(port: int) -> bool:
    # Try both IPv4 and IPv6 (Vite binds to ::1 on modern Windows)
    for family, addr in [
        (socket.AF_INET, ("127.0.0.1", port)),
        (socket.AF_INET6, ("::1", port, 0, 0)),
    ]:
        try:
            with socket.socket(family, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(addr) == 0:
                    return True
        except Exception:
            pass
    return False

def _wait_for_port(port: int, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_open(port):
            return True
        time.sleep(0.5)
    return False

def _kill_port(port: int):
    """Kill whatever is holding a port on Windows."""
    if os.name != 'nt':
        return
    try:
        # Run netstat alone (no pipe to findstr — that can hang)
        result = subprocess.run(
            ["netstat", "-ano"],
            capture_output=True, text=True, timeout=5,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        pids = set()
        needle = f":{port}"
        for line in result.stdout.splitlines():
            if needle in line and "LISTENING" in line:
                parts = line.strip().split()
                if parts:
                    pids.add(parts[-1])
        for pid in pids:
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", pid],
                timeout=5, capture_output=True,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
    except Exception:
        pass


# ── PROCESS SPAWNER ─────────────────────────────────────────────
# Each component gets its own console window (CREATE_NEW_CONSOLE)
# so there are zero pipe/buffer issues.

_CHILDREN: Dict[str, subprocess.Popen] = {}

def _make_env() -> dict:
    env = os.environ.copy()
    root = str(Path(__file__).resolve().parent)
    env["PYTHONPATH"] = root + os.pathsep + os.path.join(root, "src")
    env["PYTHONIOENCODING"] = "utf-8"
    return env

def _spawn_in_new_window(name: str, args: list, cwd: Optional[Path] = None):
    """Spawn a process in its own visible console window."""
    work_dir = str(cwd) if cwd else str(Path(__file__).resolve().parent)
    env = _make_env()

    flags = 0
    if os.name == 'nt':
        flags = subprocess.CREATE_NEW_CONSOLE

    p = subprocess.Popen(
        args,
        cwd=work_dir,
        env=env,
        creationflags=flags,
    )
    _CHILDREN[name] = p
    return p


def _cleanup_all():
    """Kill all child processes on exit."""
    for name, p in _CHILDREN.items():
        try:
            if os.name == 'nt':
                subprocess.run(
                    f"taskkill /F /T /PID {p.pid}", shell=True, timeout=5,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                )
            else:
                p.terminate()
        except Exception:
            pass


# ── LAUNCH SEQUENCES ────────────────────────────────────────────

def _get_python() -> str:
    root = Path(__file__).resolve().parent
    venv_py = root / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def _launch_api() -> bool:
    _phase("Igniting FastAPI Engine")
    py = _get_python()
    _spawn_in_new_window("API", [py, "-m", "backend.api.main"])
    ok = _wait_for_port(8000, timeout=20)
    _status("FastAPI Engine", ok, "http://localhost:8000/docs")
    return ok


def _launch_bot() -> bool:
    _phase("Deploying Telegram Bot")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        _status("Telegram Bot", False, "TELEGRAM_BOT_TOKEN missing")
        return False
    py = _get_python()
    _spawn_in_new_window("Bot", [py, "-m", "src.bot.main"])
    time.sleep(3)
    # Bot doesn't bind a port — check process is alive
    p = _CHILDREN.get("Bot")
    ok = p is not None and p.poll() is None
    _status("Telegram Bot", ok, "@academic_hub_bot")
    return ok


def _launch_dashboard() -> bool:
    _phase("Starting Orbit Dashboard")
    root = Path(__file__).resolve().parent
    dash_dir = root / "dashboard"
    if not (dash_dir / "package.json").exists():
        _status("Dashboard", False, "package.json not found")
        return False
    _spawn_in_new_window("Dashboard", ["npm.cmd", "run", "dev", "--", "--port", "5173"], cwd=dash_dir)
    ok = _wait_for_port(5173, timeout=45)
    _status("Dashboard", ok, "http://localhost:5173")
    return ok


def _launch_voyager() -> bool:
    _phase("Launching Voyager Mini App")
    root = Path(__file__).resolve().parent
    voy_dir = root / "student_app"
    if not (voy_dir / "package.json").exists():
        _status("Voyager", False, "package.json not found")
        return False
    _spawn_in_new_window("Voyager", ["npm.cmd", "run", "dev", "--", "--port", "5174"], cwd=voy_dir)
    ok = _wait_for_port(5174, timeout=45)
    _status("Voyager", ok, "http://localhost:5174")
    return ok


# ── MAIN ────────────────────────────────────────────────────────

def main():
    bot_only = "--bot-only" in sys.argv

    _clear()
    print(ORBIT_LOGO)

    # Pre-flight
    _phase("Pre-Flight Checks")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    _status(f"Python {py_ver}", True)

    token = os.getenv("TELEGRAM_BOT_TOKEN")
    _status("Bot Token", bool(token), "loaded from .env" if token else "MISSING")
    if not token:
        print(f"\n  {RD}{B}ABORT:{R} TELEGRAM_BOT_TOKEN not found in .env")
        sys.exit(1)

    db_host = os.getenv("POSTGRES_HOST", "localhost")
    db_port = os.getenv("POSTGRES_PORT", "5432")
    _status("Database Config", True, f"{db_host}:{db_port}")

    # Port cleanup (only for full launch)
    if not bot_only:
        _scan("Clearing sub-orbital ports")
        _kill_port(8000)
        _kill_port(5173)
        _kill_port(5174)
        time.sleep(1)

    # Launch
    if not bot_only:
        _launch_api()
    _launch_bot()
    if not bot_only:
        _launch_dashboard()
        _launch_voyager()

    # Final Report
    print(f"\n  {CY}{B}{'=' * 60}{R}")
    if bot_only:
        print(f"  {CY}{B}[ORBIT]{R} {GR}{B}STANDALONE BOT ORBIT ACTIVE{R}")
        print(f"  {CY}{B}{'=' * 60}{R}\n")
        _status("Telegram Bot", True, "@academic_hub_bot")
    else:
        print(f"  {CY}{B}[ORBIT]{R} {GR}{B}FULL STATION ORBIT ACHIEVED{R}")
        print(f"  {CY}{B}{'=' * 60}{R}\n")
        _status("FastAPI Engine", _port_open(8000), "http://localhost:8000/docs")
        bot_p = _CHILDREN.get("Bot")
        bot_ok = bot_p is not None and bot_p.poll() is None
        _status("Telegram Bot", bot_ok, "@academic_hub_bot")
        _status("Dashboard", _port_open(5173), "http://localhost:5173")
        _status("Voyager", _port_open(5174), "http://localhost:5174")

        online = sum([_port_open(8000), bot_ok, _port_open(5173), _port_open(5174)])
        print(f"\n    {WH}{B}{online}/4 components online{R}")

        # Auto-open browser tabs for running web apps
        _phase("Opening Web Apps in Browser")
        if _port_open(5173):
            webbrowser.open("http://localhost:5173")
            _status("Dashboard", True, "opened in browser")
        if _port_open(5174):
            webbrowser.open("http://localhost:5174")
            _status("Student App", True, "opened in browser")
        if _port_open(8000):
            webbrowser.open("http://localhost:8000/docs")
            _status("API Docs", True, "opened in browser")

    print(f"\n  {GY}Press Ctrl+C to terminate orbit.{R}\n", flush=True)

    # Hold alive — when user presses Ctrl+C, clean up everything
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n  {CY}{B}[ORBIT]{R} {YL}Retracting solar arrays...{R}")
        _cleanup_all()
        print(f"  {GR}{B}Shutdown complete.{R}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
