# commands/run.py
import sys
import subprocess
import os
from pathlib import Path

def run(args):
    if not args:
        return "run: missing file operand"
    
    script_path = Path(args[0])
    
    if not script_path.exists():
        return f"run: file not found: {script_path}"
    
    ext = script_path.suffix.lower()
    cmd = []
    
    if ext == ".py":
        cmd = [sys.executable, str(script_path)]
    elif ext == ".js":
        node = "node.exe" if os.name == "nt" else "node"
        cmd = [node, str(script_path)]
    elif ext == ".sh" and os.name != "nt":
        cmd = ["sh", str(script_path)]
    elif ext == ".bat" and os.name == "nt":
        cmd = ["cmd", "/c", str(script_path)]
    else:
        # Попытка запустить как исполняемый файл (Linux/macOS)
        if os.name != "nt" and os.access(script_path, os.X_OK):
            cmd = [str(script_path)]
        else:
            return f"run: unsupported file type or missing interpreter: {script_path}"
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        output = result.stdout
        if result.stderr:
            output += "\n[STDERR]\n" + result.stderr
        if result.returncode != 0 and not output:
            output = f"Process exited with code {result.returncode}"
        return output
    except FileNotFoundError as e:
        return f"run: interpreter not found ({e})"
    except Exception as e:
        return f"run: error: {e}"
