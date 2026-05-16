import os, sys, subprocess, time, signal, webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT, "backend")
FRONTEND = os.path.join(ROOT, "frontend", "app.py")

python = sys.executable
if not python or "WindowsApps" in python:
    for c in ["python", "python3", "C:\\Users\\haris\\AppData\\Local\\Programs\\Python\\Python314\\python.exe"]:
        try:
            subprocess.run([c, "--version"], capture_output=True, timeout=3)
            python = c; break
        except: pass

procs = []
def cleanup():
    for p in procs:
        if p.poll() is None:
            try: p.kill()
            except: pass
signal.signal(signal.SIGINT, lambda *_: (cleanup(), exit(0)))
signal.signal(signal.SIGTERM, lambda *_: (cleanup(), exit(0)))

os.environ.setdefault("PYTHONIOENCODING", "utf-8")

print("Starting AI Paper Summarizer...")
print("Backend on :8001 | Frontend on :8501")
print()

# Start backend
bp = subprocess.Popen(
    [python, "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001", "--log-level", "warning"],
    cwd=BACKEND_DIR
)
procs.append(bp)
time.sleep(2)

if bp.poll() is not None:
    print("Backend FAILED - port 8001 might be in use")
    cleanup()
    sys.exit(1)

# Start frontend
env = os.environ.copy()
env["API_URL"] = "http://localhost:8001"
fp = subprocess.Popen(
    [python, "-m", "streamlit", "run", FRONTEND, "--server.port", "8501"],
    cwd=ROOT, env=env
)
procs.append(fp)
time.sleep(3)

if fp.poll() is not None:
    print("Frontend FAILED")
    cleanup()
    sys.exit(1)

print("Both running! Open http://localhost:8501")
webbrowser.open("http://localhost:8501")

try:
    while True: time.sleep(1)
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    cleanup()