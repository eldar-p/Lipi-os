"""Install / show compilers for Lipi OS Compiler Hub.

Usage:
  compilers              status (same as langs)
  compilers install      try apt install (needs sudo/root)
  compilers install --minimal
  compilers list         package list
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path


def _code_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _script() -> Path:
    return _code_root() / "scripts" / "install-compilers.sh"


def run(args):
    from core.compiler_hub import language_status

    if not args or args[0] in ("status", "langs", "--status"):
        lines = [f"{'ID':12} {'NAME':24} {'OK':4} NOTE"]
        for r in language_status():
            lines.append(
                f"{r['id']:12} {r['name'][:24]:24} {('yes' if r['ready'] else 'no'):4} {r['note']}"
            )
        lines.append("")
        lines.append("Install toolchains:  compilers install")
        lines.append("Minimal set:         compilers install --minimal")
        return "\n".join(lines)

    if args[0] == "list":
        script = _script()
        if not script.exists():
            return f"Missing {script}"
        try:
            flag = "--minimal" if "--minimal" in args or "-m" in args else "--full"
            out = subprocess.check_output(
                ["bash", str(script), flag, "--list"],
                text=True,
            )
            return out.strip()
        except Exception as e:
            return f"compilers list: {e}"

    if args[0] in ("install", "setup", "add"):
        script = _script()
        if not script.exists():
            return f"Missing installer script: {script}"
        minimal = "--minimal" in args or "-m" in args
        cmd = ["bash", str(script)]
        if minimal:
            cmd.append("--minimal")
        if os.geteuid() != 0:
            cmd = ["sudo", "-E", *cmd]
        print(f"Running: {' '.join(cmd)}")
        try:
            proc = subprocess.run(cmd)
            ready = sum(1 for r in language_status() if r["ready"])
            total = len(language_status())
            return f"Installer exit={proc.returncode}. Languages ready: {ready}/{total} (langs)"
        except FileNotFoundError:
            return "compilers install: sudo/bash not available"
        except Exception as e:
            return f"compilers install: {e}"

    return (
        "Usage:\n"
        "  compilers                 # status\n"
        "  compilers install         # full toolchains (sudo)\n"
        "  compilers install --minimal\n"
        "  compilers list"
    )
