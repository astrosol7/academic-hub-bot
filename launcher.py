import os
import sys
import time
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
root_dir = Path(__file__).resolve().parent
load_dotenv(root_dir / ".env")

_CHILDREN = {}

def spawn(name: str, args: list, cwd: Path = root_dir):
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root_dir) + os.pathsep + str(root_dir / "src")
    env["PYTHONIOENCODING"] = "utf-8"
    
    flags = subprocess.CREATE_NEW_CONSOLE if os.name == 'nt' else 0
    p = subprocess.Popen(args, cwd=str(cwd), env=env, creationflags=flags)
    _CHILDREN[name] = p
    print(f"[{name}] Spawned with PID {p.pid}")

def cleanup():
    for name, p in _CHILDREN.items():
        try:
            if os.name == 'nt':
                subprocess.run(f"taskkill /F /T /PID {p.pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                p.terminate()
        except Exception:
            pass

def main():
    print("🚀 Starting Station Orbit...")
    
    if not os.getenv("TELEGRAM_BOT_TOKEN"):
        print("❌ ABORT: TELEGRAM_BOT_TOKEN missing in .env")
        sys.exit(1)
        
    bot_only = "--bot-only" in sys.argv
    py_exe = sys.executable
    venv_py = root_dir / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        py_exe = str(venv_py)

    if not bot_only:
        spawn("API", [py_exe, "main.py"])
        
    spawn("Bot", [py_exe, "-m", "src.bot.main"])
    
    if not bot_only:
        dash_dir = root_dir / "dashboard"
        if (dash_dir / "package.json").exists():
            spawn("Dashboard", ["npm.cmd", "run", "dev", "--", "--port", "5173"], cwd=dash_dir)
            
        voy_dir = root_dir / "student_app"
        if (voy_dir / "package.json").exists():
            spawn("Voyager", ["npm.cmd", "run", "dev", "--", "--port", "5174"], cwd=voy_dir)

    print("\n✅ Orbit is online. Press Ctrl+C to terminate all processes.\n")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
        cleanup()
        print("Shutdown complete.")

if __name__ == "__main__":
    main()
