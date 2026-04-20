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
import atexit
from pathlib import Path
from typing import List, Dict, Optional

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
R   = "\033[0m"     # Reset
B   = "\033[1m"     # Bold
DIM = "\033[2m"     # Dim
CY  = "\033[96m"    # Bright Cyan
GR  = "\033[92m"    # Bright Green
RD  = "\033[91m"    # Bright Red
YL  = "\033[93m"    # Yellow
MG  = "\033[95m"    # Magenta
WH  = "\033[97m"    # White
GY  = "\033[90m"    # Gray
BLU = "\033[94m"    # Bright Blue

# ── ASCII LOGO ──────────────────────────────────────────────────
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
    """Print a phase header."""
    print(f"\n  {CY}{B}[ORBIT]{R} {WH}{label}{R}")

def _status(label: str, ok: bool, detail: str = ""):
    tag = f"{GR}ONLINE{R}" if ok else f"{RD}FAILED{R}"
    pad = 32 - len(label)
    extra = f"  {GY}{detail}{R}" if detail else ""
    print(f"    {DIM}>{R} {label}{'.' * max(pad, 2)} {tag}{extra}")

def _scan(label: str, steps: int = 30, duration: float = 0.6):
    """Animated progress scanner."""
    for i in range(steps + 1):
        pct = int(i / steps * 100)
        filled = "█" * i + "░" * (steps - i)
        print(f"\r    {GY}>{R} {label}  [{CY}{filled}{R}] {pct}%", end="", flush=True)
        time.sleep(duration / steps)
    print()


# ── ORCHESTRATOR ────────────────────────────────────────────────
class Orchestrator:
    def __init__(self, root: Path):
        self.root = root
        self.venv_py = root / ".venv" / "Scripts" / "python.exe"
        if not self.venv_py.exists():
            self.venv_py = Path(sys.executable)

        self.env = os.environ.copy()
        self.env["PYTHONPATH"] = str(root) + os.pathsep + str(root / "src")
        self.env["PYTHONIOENCODING"] = "utf-8"
        self.processes: Dict[str, subprocess.Popen] = {}
        atexit.register(self._cleanup)

    # ── Port utilities ──
    def _port_open(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.3)
                return s.connect_ex(("127.0.0.1", port)) == 0
        except Exception:
            return False

    def _purge_ports(self, ports: List[int]):
        if os.name != 'nt':
            return
        for port in ports:
            try:
                out = subprocess.check_output(
                    f"netstat -ano | findstr :{port}", shell=True
                ).decode()
                for line in out.splitlines():
                    if "LISTENING" in line:
                        pid = line.strip().split()[-1]
                        subprocess.run(
                            f"taskkill /F /PID {pid}", shell=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                        )
            except Exception:
                pass

    # ── Process lifecycle ──
    def spawn(self, name: str, cmd: List[str], cwd: Optional[Path] = None):
        p = subprocess.Popen(
            cmd, cwd=str(cwd or self.root), env=self.env,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            shell=(os.name == 'nt'), text=True,
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0,
        )
        self.processes[name] = p
        return p

    def wait_for_port(self, port: int, timeout: int = 20) -> bool:
        for _ in range(timeout * 2):
            if self._port_open(port):
                return True
            time.sleep(0.5)
        return False

    def alive(self, name: str) -> bool:
        p = self.processes.get(name)
        return p is not None and p.poll() is None

    def _cleanup(self):
        for name, p in self.processes.items():
            try:
                if os.name == 'nt':
                    subprocess.run(
                        f"taskkill /F /T /PID {p.pid}", shell=True,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                else:
                    p.terminate()
            except Exception:
                pass


# ── LAUNCH SEQUENCES ────────────────────────────────────────────

def _launch_api(orc: Orchestrator) -> bool:
    _phase("Igniting FastAPI Engine")
    orc.spawn("API", [str(orc.venv_py), "-m", "backend.api.main"])
    ok = orc.wait_for_port(8000, timeout=20)
    _status("FastAPI Engine", ok, "http://localhost:8000/docs")
    return ok


def _launch_bot(orc: Orchestrator) -> bool:
    _phase("Deploying Telegram Bot")
    token = os.getenv("TELEGRAM_BOT_TOKEN", "")
    if not token:
        _status("Telegram Bot", False, "TELEGRAM_BOT_TOKEN missing")
        return False
    orc.spawn("Bot", [str(orc.venv_py), "-m", "src.bot.main"])
    time.sleep(3)
    ok = orc.alive("Bot")
    _status("Telegram Bot", ok, "@academic_hub_bot")
    return ok


def _launch_dashboard(orc: Orchestrator) -> bool:
    _phase("Starting Orbit Dashboard")
    dash_dir = orc.root / "dashboard"
    if not (dash_dir / "package.json").exists():
        _status("Dashboard", False, "package.json not found")
        return False
    orc.spawn("Dashboard", ["npm.cmd", "run", "dev", "--", "--port", "5173"], cwd=dash_dir)
    ok = orc.wait_for_port(5173, timeout=30)
    _status("Dashboard", ok, "http://localhost:5173")
    return ok


def _launch_voyager(orc: Orchestrator) -> bool:
    _phase("Launching Voyager Mini App")
    voy_dir = orc.root / "student_app"
    if not (voy_dir / "package.json").exists():
        _status("Voyager", False, "package.json not found")
        return False
    orc.spawn("Voyager", ["npm.cmd", "run", "dev", "--", "--port", "5174"], cwd=voy_dir)
    ok = orc.wait_for_port(5174, timeout=30)
    _status("Voyager", ok, "http://localhost:5174")
    return ok


def _final_report(orc: Orchestrator, bot_only: bool):
    print(f"\n  {CY}{B}{'=' * 60}{R}")
    if bot_only:
        print(f"  {CY}{B}[ORBIT]{R} {GR}{B}STANDALONE BOT ORBIT ACTIVE{R}")
        print(f"  {CY}{B}{'=' * 60}{R}\n")
        bot_ok = orc.alive("Bot")
        _status("Telegram Bot", bot_ok, "@academic_hub_bot")
    else:
        print(f"  {CY}{B}[ORBIT]{R} {GR}{B}FULL STATION ORBIT ACHIEVED{R}")
        print(f"  {CY}{B}{'=' * 60}{R}\n")
        _status("FastAPI Engine", orc._port_open(8000), "http://localhost:8000/docs")
        _status("Telegram Bot", orc.alive("Bot"), "@academic_hub_bot")
        _status("Dashboard", orc._port_open(5173), "http://localhost:5173")
        _status("Voyager", orc._port_open(5174), "http://localhost:5174")

        online = sum([
            orc._port_open(8000), orc.alive("Bot"),
            orc._port_open(5173), orc._port_open(5174)
        ])
        print(f"\n    {WH}{B}{online}/4 components online{R}")

    print(f"\n  {GY}Press Ctrl+C to terminate orbit.{R}\n")


# ── MAIN ────────────────────────────────────────────────────────

def main():
    root = Path(__file__).resolve().parent
    orc = Orchestrator(root)
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

    # Port cleanup
    if not bot_only:
        _scan("Clearing sub-orbital ports", steps=20, duration=0.4)
        orc._purge_ports([8000, 5173, 5174])

    # Launch
    if not bot_only:
        _launch_api(orc)
    _launch_bot(orc)
    if not bot_only:
        _launch_dashboard(orc)
        _launch_voyager(orc)

    # Report
    _final_report(orc, bot_only)

    # Hold
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n  {CY}{B}[ORBIT]{R} {YL}Retracting solar arrays... Shutdown complete.{R}\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
