"""Lipi OS compiler hub — compile/run snippets in many languages."""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
import webbrowser
from pathlib import Path

from i18n import get_language_strings, load_config_language
from paths import TEMP_DIR, ensure_runtime_dirs

ensure_runtime_dirs()

SUPPORTED_LANGUAGES: dict[str, dict] = {
    "python": {
        "name": "Python", "name_ru": "Python", "extension": ".py", "category": "script",
        "compiler": "python", "tools": ["python3", "python"],
        "compile_cmd": None, "run_cmd": [sys.executable, "{source}"],
    },
    "javascript": {
        "name": "JavaScript (Node)", "name_ru": "JavaScript (Node)", "extension": ".js",
        "category": "script", "compiler": "node", "tools": ["node"],
        "compile_cmd": None, "run_cmd": ["node", "{source}"],
    },
    "typescript": {
        "name": "TypeScript", "name_ru": "TypeScript", "extension": ".ts",
        "category": "script", "compiler": "tsc", "tools": ["tsc", "ts-node", "node"],
        "compile_cmd": None, "run_cmd": ["node", "{output}"],
    },
    "html": {
        "name": "HTML", "name_ru": "HTML", "extension": ".html", "category": "web",
        "compiler": "browser", "tools": [], "compile_cmd": None, "run_cmd": None,
    },
    "css": {
        "name": "CSS", "name_ru": "CSS", "extension": ".css", "category": "web",
        "compiler": "css", "tools": [], "compile_cmd": None, "run_cmd": None,
    },
    "c": {
        "name": "C", "name_ru": "Си", "extension": ".c", "category": "compiled",
        "compiler": "gcc", "tools": ["gcc", "clang"],
        "compile_cmd": ["gcc", "{source}", "-O2", "-Wall", "-o", "{output}"],
        "run_cmd": ["{output}"],
    },
    "cpp": {
        "name": "C++", "name_ru": "C++", "extension": ".cpp", "category": "compiled",
        "compiler": "g++", "tools": ["g++", "clang++"],
        "compile_cmd": ["g++", "{source}", "-O2", "-Wall", "-std=c++17", "-o", "{output}"],
        "run_cmd": ["{output}"],
    },
    "java": {
        "name": "Java", "name_ru": "Java", "extension": ".java", "category": "compiled",
        "compiler": "javac", "tools": ["javac", "java"],
        "compile_cmd": ["javac", "{source}"],
        "run_cmd": ["java", "-cp", "{dir}", "{classname}"],
    },
    "rust": {
        "name": "Rust", "name_ru": "Rust", "extension": ".rs", "category": "compiled",
        "compiler": "rustc", "tools": ["rustc", "cargo"],
        "compile_cmd": ["rustc", "{source}", "-O", "-o", "{output}"],
        "run_cmd": ["{output}"],
    },
    "go": {
        "name": "Go", "name_ru": "Go", "extension": ".go", "category": "compiled",
        "compiler": "go", "tools": ["go"],
        "compile_cmd": None, "run_cmd": ["go", "run", "{source}"],
    },
    "csharp": {
        "name": "C#", "name_ru": "C#", "extension": ".cs", "category": "compiled",
        "compiler": "dotnet", "tools": ["dotnet", "csc"],
        "compile_cmd": None, "run_cmd": ["dotnet", "script", "{source}"],
    },
    "asm": {
        "name": "Assembly (NASM)", "name_ru": "Ассемблер (NASM)", "extension": ".asm",
        "category": "compiled", "compiler": "nasm", "tools": ["nasm", "ld"],
        "compile_cmd": None, "run_cmd": ["{output}"],
    },
    "kotlin": {
        "name": "Kotlin", "name_ru": "Kotlin", "extension": ".kt", "category": "compiled",
        "compiler": "kotlinc", "tools": ["kotlinc", "kotlin"],
        "compile_cmd": ["kotlinc", "{source}", "-include-runtime", "-d", "{output}.jar"],
        "run_cmd": ["java", "-jar", "{output}.jar"],
    },
    "lua": {
        "name": "Lua", "name_ru": "Lua", "extension": ".lua", "category": "script",
        "compiler": "lua", "tools": ["lua", "luajit"],
        "compile_cmd": None, "run_cmd": ["lua", "{source}"],
    },
    "ruby": {
        "name": "Ruby", "name_ru": "Ruby", "extension": ".rb", "category": "script",
        "compiler": "ruby", "tools": ["ruby"],
        "compile_cmd": None, "run_cmd": ["ruby", "{source}"],
    },
    "php": {
        "name": "PHP", "name_ru": "PHP", "extension": ".php", "category": "script",
        "compiler": "php", "tools": ["php"],
        "compile_cmd": None, "run_cmd": ["php", "{source}"],
    },
    "bash": {
        "name": "Bash / Shell", "name_ru": "Bash / Shell", "extension": ".sh",
        "category": "script", "compiler": "bash", "tools": ["bash", "sh"],
        "compile_cmd": None, "run_cmd": ["bash", "{source}"],
    },
    "perl": {
        "name": "Perl", "name_ru": "Perl", "extension": ".pl", "category": "script",
        "compiler": "perl", "tools": ["perl"],
        "compile_cmd": None, "run_cmd": ["perl", "{source}"],
    },
    "fortran": {
        "name": "Fortran", "name_ru": "Fortran", "extension": ".f90", "category": "compiled",
        "compiler": "gfortran", "tools": ["gfortran"],
        "compile_cmd": ["gfortran", "{source}", "-O2", "-o", "{output}"],
        "run_cmd": ["{output}"],
    },
    "zig": {
        "name": "Zig", "name_ru": "Zig", "extension": ".zig", "category": "compiled",
        "compiler": "zig", "tools": ["zig"],
        "compile_cmd": None, "run_cmd": ["zig", "run", "{source}"],
    },
}

ALIASES = {
    "js": "javascript", "ts": "typescript", "c++": "cpp", "cxx": "cpp",
    "c#": "csharp", "cs": "csharp", "py": "python", "rs": "rust",
    "assembly": "asm", "nasm": "asm", "kt": "kotlin", "sh": "bash", "shell": "bash", "f90": "fortran", "fortran90": "fortran",
}


def resolve_language(language_id: str) -> str | None:
    lid = (language_id or "").strip().lower()
    if lid in SUPPORTED_LANGUAGES:
        return lid
    return ALIASES.get(lid)


def _lang() -> dict:
    return get_language_strings()


def _display_name(lang_id: str) -> str:
    info = SUPPORTED_LANGUAGES[lang_id]
    if load_config_language().startswith("ru"):
        return info.get("name_ru", info["name"])
    return info["name"]


def load_compiler_paths() -> dict:
    try:
        from core.settings_manager import load_config
        return dict(load_config().get("compiler_paths") or {})
    except Exception:
        return {}


def find_compiler(name: str) -> str | None:
    compiler_paths = load_compiler_paths()
    custom_path = compiler_paths.get(name)
    if custom_path and Path(custom_path).exists():
        return custom_path
    return shutil.which(name)


def find_any_tool(names: list[str]) -> str | None:
    for n in names:
        p = find_compiler(n)
        if p:
            return p
    return None


def language_status() -> list[dict]:
    rows = []
    for lid, info in SUPPORTED_LANGUAGES.items():
        tools = info.get("tools") or ([info["compiler"]] if info.get("compiler") else [])
        present, missing = [], []
        for t in tools:
            if t in ("browser", "css"):
                continue
            (present if find_compiler(t) else missing).append(t)
        if lid in ("html", "css"):
            ready, note = True, "built-in"
        elif lid == "python":
            ready, note = True, sys.executable
        elif lid == "typescript":
            ready = bool(find_any_tool(["ts-node", "tsc"]))
            note = "ts-node or tsc+node" if ready else "need ts-node or tsc"
        elif lid == "csharp":
            ready = bool(find_any_tool(["dotnet", "csc"]))
            note = "dotnet/csc" if ready else "need dotnet"
        elif lid == "asm":
            ready = bool(find_compiler("nasm") and (os.name == "nt" or find_compiler("ld")))
            note = "nasm+ld" if ready else "need nasm (+ ld)"
        else:
            primary = info.get("compiler")
            ready = bool(find_compiler(primary)) if primary else bool(present)
            if not ready and info.get("run_cmd"):
                ready = bool(find_compiler(info["run_cmd"][0]))
            note = ", ".join(present) if present else ("missing: " + ", ".join(missing[:3]))
        rows.append({"id": lid, "name": _display_name(lid), "category": info.get("category", ""),
                     "ready": ready, "note": note})
    return rows


def _extract_java_classname(code: str, source_file: Path) -> str:
    m = re.search(r"\bpublic\s+class\s+(\w+)", code)
    if m:
        return m.group(1)
    m = re.search(r"\bclass\s+(\w+)", code)
    if m:
        return m.group(1)
    return source_file.stem


def _run_typescript(source_file: Path, output_file: Path) -> tuple[bool, str]:
    strings = _lang()
    tsc, node = find_compiler("tsc"), find_compiler("node")
    if tsc and node:
        # TypeScript 5+/7: `tsc file.ts` emits sibling .js (outFile removed in TS 7)
        result = subprocess.run(
            [tsc, str(source_file)],
            capture_output=True, text=True, cwd=str(source_file.parent), timeout=60,
        )
        js_out = source_file.with_suffix(".js")
        if result.returncode == 0 and js_out.exists():
            run = subprocess.run(
                [node, str(js_out)], capture_output=True, text=True, cwd=str(source_file.parent), timeout=30,
            )
            out = (run.stdout or "") + (("\n" + run.stderr) if run.stderr else "")
            try:
                js_out.unlink(missing_ok=True)
            except OSError:
                pass
            return run.returncode == 0, out.strip() or f"exit {run.returncode}"
        tsc_err = (result.stderr or result.stdout or "").strip()
    else:
        tsc_err = ""

    ts_node = find_compiler("ts-node")
    if ts_node:
        result = subprocess.run(
            [ts_node, "--transpileOnly", str(source_file)],
            capture_output=True, text=True, cwd=str(source_file.parent), timeout=30,
        )
        out = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
        if result.returncode == 0:
            return True, out.strip()
        return False, out.strip() or tsc_err or f"exit {result.returncode}"

    if not tsc or not node:
        return False, strings["compiler_not_found"].format("tsc+node or ts-node")
    return False, strings["error_compile"].format(tsc_err or "tsc failed")


def _run_asm(source_file: Path, output_file: Path) -> tuple[bool, str]:
    strings = _lang()
    nasm = find_compiler("nasm")
    if not nasm:
        return False, strings["compiler_not_found"].format("nasm")
    if os.name == "nt":
        obj = output_file.with_suffix(".obj")
        result = subprocess.run([nasm, "-f", "win64", str(source_file), "-o", str(obj)],
                                capture_output=True, text=True, cwd=str(TEMP_DIR))
        if result.returncode != 0:
            return False, strings["error_compile"].format(result.stderr or result.stdout)
        return False, f"NASM object built ({obj}); link with MSVC/GoLink on Windows."
    ld = find_compiler("ld")
    if not ld:
        return False, strings["compiler_not_found"].format("ld")
    obj = Path(str(output_file) + ".o")
    result = subprocess.run([nasm, "-f", "elf64", str(source_file), "-o", str(obj)],
                            capture_output=True, text=True, cwd=str(TEMP_DIR))
    if result.returncode != 0:
        return False, strings["error_compile"].format(result.stderr or result.stdout)
    result = subprocess.run([ld, str(obj), "-o", str(output_file)], capture_output=True, text=True, cwd=str(TEMP_DIR))
    if result.returncode != 0:
        return False, strings["error_compile"].format(result.stderr or result.stdout)
    result = subprocess.run([str(output_file.resolve())], capture_output=True, text=True, cwd=str(TEMP_DIR), timeout=30)
    out = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
    return True, out.strip() or f"exit {result.returncode}"


def _run_html(code: str) -> tuple[bool, str]:
    path = TEMP_DIR / "lipi_preview.html"
    path.write_text(code, encoding="utf-8")
    url = path.resolve().as_uri()
    try:
        webbrowser.open(url)
        return True, f"Opened in browser:\n{url}"
    except Exception as e:
        return True, f"Saved HTML preview:\n{path}\n({e})"


def _run_css(code: str) -> tuple[bool, str]:
    path = TEMP_DIR / "lipi_preview.css"
    path.write_text(code, encoding="utf-8")
    braces = code.count("{") - code.count("}")
    notes = []
    if braces:
        notes.append(f"warning: unmatched braces ({braces:+d})")
    notes.append(f"saved: {path}")
    notes.append(f"bytes: {len(code.encode('utf-8'))}")
    return True, "\n".join(notes)


def compile_and_run(language_id: str, code: str) -> tuple[bool, str]:
    lid = resolve_language(language_id)
    if not lid:
        return False, f"Unsupported language: {language_id}"
    lang_info = SUPPORTED_LANGUAGES[lid]
    strings = _lang()
    if lid == "html":
        return _run_html(code)
    if lid == "css":
        return _run_css(code)

    work = Path(tempfile.mkdtemp(prefix="lipi_", dir=str(TEMP_DIR)))
    try:
        if lid == "java":
            classname = _extract_java_classname(code, Path("Main.java"))
            source_file = work / f"{classname}.java"
        else:
            classname = "Main"
            source_file = work / f"main{lang_info['extension']}"
        source_file.write_text(code, encoding="utf-8")
        output_file = work / ("out.exe" if os.name == "nt" and lid in ("c", "cpp", "rust") else "out")

        if lid == "typescript":
            return _run_typescript(source_file, output_file)
        if lid == "asm":
            return _run_asm(source_file, output_file)
        if lid == "csharp":
            dotnet = find_compiler("dotnet")
            if not dotnet:
                return False, strings["compiler_not_found"].format("dotnet")
            result = subprocess.run([dotnet, "script", str(source_file)], capture_output=True, text=True, cwd=str(work), timeout=60)
            out = (result.stdout or "") + (("\n" + result.stderr) if result.stderr else "")
            return result.returncode == 0, out.strip() or f"exit {result.returncode}"

        fmt = dict(source=str(source_file), output=str(output_file), dir=str(work), classname=classname)

        if lang_info.get("compile_cmd"):
            stages: list[list[str]] = [[]]
            for part in lang_info["compile_cmd"]:
                if part == "&&":
                    stages.append([])
                else:
                    stages[-1].append(part.format(**fmt))
            for stage in stages:
                if not stage:
                    continue
                cmd = list(stage)
                tool = find_compiler(cmd[0]) or find_any_tool(lang_info.get("tools") or [])
                if tool:
                    cmd[0] = tool
                elif not shutil.which(cmd[0]):
                    return False, strings["compiler_not_found"].format(cmd[0])
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(work), timeout=120)
                if result.returncode != 0:
                    return False, strings["error_compile"].format(result.stderr or result.stdout or f"exit {result.returncode}")

        if not lang_info.get("run_cmd"):
            return True, "Compiled."

        run_cmd = [part.format(**fmt) for part in lang_info["run_cmd"]]
        if run_cmd[0] == sys.executable:
            pass
        elif Path(run_cmd[0]).exists() or run_cmd[0].endswith("out") or run_cmd[0].endswith(".exe"):
            run_cmd[0] = str(Path(run_cmd[0]).resolve())
        else:
            resolved = find_compiler(run_cmd[0])
            if resolved:
                run_cmd[0] = resolved
            elif not shutil.which(run_cmd[0]):
                return False, strings["compiler_not_found"].format(run_cmd[0])

        result = subprocess.run(run_cmd, capture_output=True, text=True, cwd=str(work), timeout=30)
        output = result.stdout or ""
        if result.stderr:
            output = (output + "\n[STDERR]\n" + result.stderr).strip()
        if result.returncode != 0 and not output:
            output = f"Process exited with code {result.returncode}"
        return True, output
    except subprocess.TimeoutExpired:
        return False, strings.get("error_run", "Runtime error:\n{}").format("Timed out")
    except Exception as e:
        return False, str(e)
    finally:
        try:
            for p in sorted(work.rglob("*"), reverse=True):
                try:
                    p.unlink() if p.is_file() else p.rmdir()
                except OSError:
                    pass
            work.rmdir()
        except OSError:
            pass


def cli_compiler_hub(argv: list[str] | None = None) -> None:
    strings = _lang()
    argv = list(argv or [])
    if argv and argv[0] in ("langs", "list", "--list", "status"):
        print(f"{'ID':12} {'NAME':24} {'OK':4} NOTE")
        for row in language_status():
            print(f"{row['id']:12} {row['name'][:24]:24} {('yes' if row['ready'] else 'no'):4} {row['note']}")
        return
    if argv and argv[0] == "run" and len(argv) >= 3:
        ok, out = compile_and_run(argv[1], " ".join(argv[2:]).replace("\\n", "\n"))
        print(out)
        return
    if argv and argv[0] == "file" and len(argv) >= 3:
        path = Path(argv[2])
        if not path.exists():
            print(f"File not found: {path}")
            return
        ok, out = compile_and_run(argv[1], path.read_text(encoding="utf-8", errors="replace"))
        print(out)
        return

    print(f"\n=== {strings.get('compiler_hub_title', 'Compiler Hub')} ===")
    print(strings["select_lang"])
    print("Tip: compile langs | compile run python 'print(1)' | compile file c main.c\n")
    status = {r["id"]: r for r in language_status()}
    lang_list = list(SUPPORTED_LANGUAGES.keys())
    for i, lid in enumerate(lang_list, 1):
        st = "Y" if status[lid]["ready"] else "."
        print(f"{i:2}. [{st}] {_display_name(lid)} ({lid})")
    try:
        choice = int(input("> ")) - 1
        if choice < 0 or choice >= len(lang_list):
            print(strings.get("invalid_choice", "Invalid choice")); return
        lang_id = lang_list[choice]
    except (ValueError, EOFError):
        print(strings.get("invalid_choice", "Invalid choice")); return
    print(strings["enter_code"])
    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass
    code = "\n".join(lines)
    if not code.strip():
        print(strings.get("empty_code", "Empty code")); return
    print(strings["compiling"])
    success, output = compile_and_run(lang_id, code)
    print(strings["running"]); print(output)
    if success:
        print(strings["success"])


def create_gui_compiler_hub(master=None) -> None:
    try:
        from core.gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Using CLI.")
        return cli_compiler_hub()
    strings = _lang()
    win = LipiWindow(strings.get("compiler_hub_title", "Compiler Hub"), 960, 640, master=master)
    from tkinter import Button, Frame, OptionMenu, Scrollbar, StringVar, Text
    status = {r["id"]: r for r in language_status()}
    lang_list = list(SUPPORTED_LANGUAGES.keys())
    lang_names = [f"{_display_name(lid)} ({lid})" + ("" if status[lid]["ready"] else " [!]") for lid in lang_list]
    name_to_id = {lang_names[i]: lang_list[i] for i in range(len(lang_list))}
    lang_var = StringVar(win.root); lang_var.set(lang_names[0])
    OptionMenu(win.content, lang_var, *lang_names).grid(row=0, column=0, padx=5, pady=5, sticky="w")
    code_text = Text(win.content, wrap="word", font=("Courier", 10))
    code_scroll = Scrollbar(win.content, command=code_text.yview)
    code_text.config(yscrollcommand=code_scroll.set)
    code_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5)
    code_scroll.grid(row=1, column=2, sticky="ns")
    button_frame = Frame(win.content, bg="white"); button_frame.grid(row=2, column=0, columnspan=3, pady=5)
    output_holder = {"widget": None}
    def run_code() -> None:
        if output_holder["widget"] is not None:
            output_holder["widget"].destroy(); output_holder["widget"] = None
        lang_id = name_to_id.get(lang_var.get(), "python")
        code = code_text.get("1.0", "end-1c")
        if not code.strip():
            return
        win.root.config(cursor="watch"); win.root.update()
        _, output = compile_and_run(lang_id, code)
        win.root.config(cursor="")
        output_frame = Frame(win.content, bg="white")
        output_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        output_holder["widget"] = output_frame
        output_text = Text(output_frame, wrap="word", font=("Courier", 10), bg="#f0f0f0", height=10)
        out_scroll = Scrollbar(output_frame, command=output_text.yview)
        output_text.config(yscrollcommand=out_scroll.set)
        output_text.pack(side="left", fill="both", expand=True); out_scroll.pack(side="right", fill="y")
        output_text.insert("1.0", output)
    Button(button_frame, text=strings.get("run", "Run"), command=run_code, width=15).pack(side="left", padx=5)
    Button(button_frame, text=strings["exit"], command=win.close, width=15).pack(side="left", padx=5)
    win.content.grid_rowconfigure(1, weight=1); win.content.grid_columnconfigure(0, weight=1)
    win.content.grid_rowconfigure(3, weight=1); win.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_compiler_hub()
    else:
        cli_compiler_hub(sys.argv[1:])
