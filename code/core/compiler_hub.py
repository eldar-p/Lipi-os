"""Lipi OS compiler hub — compile/run snippets in several languages."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

from i18n import get_language_strings, load_config_language
from paths import TEMP_DIR, ensure_runtime_dirs

ensure_runtime_dirs()

SUPPORTED_LANGUAGES = {
    "c": {
        "name": "C",
        "name_ru": "Си",
        "extension": ".c",
        "compiler": "gcc",
        "compile_cmd": ["gcc", "{source}", "-o", "{output}"],
        "run_cmd": ["{output}"],
    },
    "cpp": {
        "name": "C++",
        "name_ru": "C++",
        "extension": ".cpp",
        "compiler": "g++",
        "compile_cmd": ["g++", "{source}", "-o", "{output}"],
        "run_cmd": ["{output}"],
    },
    "cs": {
        "name": "C#",
        "name_ru": "C#",
        "extension": ".cs",
        "compiler": "dotnet",
        "compile_cmd": None,
        "run_cmd": ["dotnet", "script", "{source}"],
    },
    "rust": {
        "name": "Rust",
        "name_ru": "Rust",
        "extension": ".rs",
        "compiler": "rustc",
        "compile_cmd": ["rustc", "{source}", "-o", "{output}"],
        "run_cmd": ["{output}"],
    },
    "asm": {
        "name": "Assembly (NASM)",
        "name_ru": "Ассемблер (NASM)",
        "extension": ".asm",
        "compiler": "nasm",
        "compile_cmd": (
            ["nasm", "-f", "elf64", "{source}", "-o", "{output}.o", "&&", "ld", "{output}.o", "-o", "{output}"]
            if os.name != "nt"
            else ["nasm", "-f", "win64", "{source}", "-o", "{output}.obj"]
        ),
        "run_cmd": ["{output}"],
    },
    "python": {
        "name": "Python",
        "name_ru": "Python",
        "extension": ".py",
        "compiler": "python",
        "compile_cmd": None,
        "run_cmd": [sys.executable, "{source}"],
    },
    "javascript": {
        "name": "JavaScript",
        "name_ru": "JavaScript",
        "extension": ".js",
        "compiler": "node",
        "compile_cmd": None,
        "run_cmd": ["node", "{source}"],
    },
}


def _lang() -> dict:
    return get_language_strings()


def _display_name(lang_id: str) -> str:
    info = SUPPORTED_LANGUAGES[lang_id]
    if load_config_language() == "ru":
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


def compile_and_run(language_id: str, code: str) -> tuple[bool, str]:
    lang_info = SUPPORTED_LANGUAGES.get(language_id)
    if not lang_info:
        return False, "Unsupported language"

    strings = _lang()
    compiler_name = lang_info["compiler"]
    compiler_path = find_compiler(compiler_name)

    # Interpreted languages still need their runtime
    needs_compiler = lang_info["compile_cmd"] is not None
    if needs_compiler and not compiler_path:
        return False, strings["compiler_not_found"].format(compiler_name)
    if not needs_compiler and language_id == "javascript" and not find_compiler("node"):
        return False, strings["compiler_not_found"].format("node")

    source_file = TEMP_DIR / f"temp{lang_info['extension']}"
    with open(source_file, "w", encoding="utf-8") as f:
        f.write(code)

    output_file = TEMP_DIR / "temp_exec"
    if os.name == "nt" and language_id in ("c", "cpp", "rust"):
        output_file = output_file.with_suffix(".exe")

    try:
        if lang_info["compile_cmd"]:
            # Split compile pipeline on '&&' for asm link step
            raw_cmd = lang_info["compile_cmd"]
            stages: list[list[str]] = [[]]
            for part in raw_cmd:
                if part == "&&":
                    stages.append([])
                else:
                    stages[-1].append(part.format(source=str(source_file), output=str(output_file)))

            for stage in stages:
                if not stage:
                    continue
                cmd = list(stage)
                if compiler_path and cmd[0] in (compiler_name, "nasm", "gcc", "g++", "rustc"):
                    cmd[0] = compiler_path
                result = subprocess.run(cmd, capture_output=True, text=True, cwd=str(TEMP_DIR))
                if result.returncode != 0:
                    return False, strings["error_compile"].format(
                        result.stderr or result.stdout or f"exit {result.returncode}"
                    )

        run_cmd = [
            part.format(source=str(source_file), output=str(output_file))
            for part in lang_info["run_cmd"]
        ]
        # Make relative binary runnable
        if run_cmd and run_cmd[0] == str(output_file) and os.name != "nt":
            run_cmd[0] = str(output_file.resolve())

        result = subprocess.run(run_cmd, capture_output=True, text=True, cwd=str(TEMP_DIR), timeout=30)
        output = result.stdout or ""
        if result.stderr:
            output = (output + "\n[STDERR]\n" + result.stderr).strip()
        if result.returncode != 0 and not output:
            output = f"Process exited with code {result.returncode}"
        return True, output
    except subprocess.TimeoutExpired:
        return False, strings.get("error_run", "Runtime error:\n{}").format("Timed out after 30s")
    except Exception as e:
        return False, str(e)
    finally:
        for leftover in TEMP_DIR.glob("temp*"):
            try:
                if leftover.is_file():
                    leftover.unlink(missing_ok=True)
            except OSError:
                pass


def cli_compiler_hub() -> None:
    strings = _lang()
    print(f"\n=== {strings.get('compiler_hub_title', strings.get('title', 'Compiler Hub'))} ===")
    print(strings["select_lang"])

    lang_list = list(SUPPORTED_LANGUAGES.keys())
    for i, lid in enumerate(lang_list, 1):
        print(f"{i}. {_display_name(lid)}")

    try:
        choice = int(input("> ")) - 1
        if choice < 0 or choice >= len(lang_list):
            print(strings.get("invalid_choice", "Invalid choice"))
            return
        lang_id = lang_list[choice]
    except (ValueError, EOFError):
        print(strings.get("invalid_choice", "Invalid choice"))
        return

    print(strings["enter_code"])
    lines = []
    try:
        while True:
            lines.append(input())
    except EOFError:
        pass

    code = "\n".join(lines)
    if not code.strip():
        print(strings.get("empty_code", "Empty code"))
        return

    print(strings["compiling"])
    success, output = compile_and_run(lang_id, code)
    print(strings["running"])
    print(output)
    if success:
        print(strings["success"])


def create_gui_compiler_hub(master=None) -> None:
    try:
        from core.gui_engine import LipiWindow
    except ImportError:
        print("GUI not available. Using CLI.")
        return cli_compiler_hub()

    strings = _lang()
    title = strings.get("compiler_hub_title", "Compiler Hub")
    win = LipiWindow(title, 900, 600, master=master)
    from tkinter import Button, Frame, OptionMenu, Scrollbar, StringVar, Text

    lang_list = list(SUPPORTED_LANGUAGES.keys())
    lang_names = [_display_name(lid) for lid in lang_list]
    name_to_id = {_display_name(lid): lid for lid in lang_list}

    lang_var = StringVar(win.root)
    lang_var.set(lang_names[0])
    OptionMenu(win.content, lang_var, *lang_names).grid(
        row=0, column=0, padx=5, pady=5, sticky="w"
    )

    code_text = Text(win.content, wrap="word", font=("Courier", 10))
    code_scroll = Scrollbar(win.content, command=code_text.yview)
    code_text.config(yscrollcommand=code_scroll.set)
    code_text.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=5)
    code_scroll.grid(row=1, column=2, sticky="ns")

    button_frame = Frame(win.content, bg="white")
    button_frame.grid(row=2, column=0, columnspan=3, pady=5)

    output_holder = {"widget": None}

    def run_code() -> None:
        if output_holder["widget"] is not None:
            output_holder["widget"].destroy()
            output_holder["widget"] = None

        lang_id = name_to_id.get(lang_var.get(), "python")
        code = code_text.get("1.0", "end-1c")
        if not code.strip():
            return

        win.root.config(cursor="watch")
        win.root.update()
        _, output = compile_and_run(lang_id, code)
        win.root.config(cursor="")

        output_frame = Frame(win.content, bg="white")
        output_frame.grid(row=3, column=0, columnspan=3, sticky="nsew", padx=5, pady=5)
        output_holder["widget"] = output_frame

        output_text = Text(
            output_frame, wrap="word", font=("Courier", 10), bg="#f0f0f0", height=10
        )
        out_scroll = Scrollbar(output_frame, command=output_text.yview)
        output_text.config(yscrollcommand=out_scroll.set)
        output_text.pack(side="left", fill="both", expand=True)
        out_scroll.pack(side="right", fill="y")
        output_text.insert("1.0", output)

    Button(
        button_frame, text=strings.get("run", "Run"), command=run_code, width=15
    ).pack(side="left", padx=5)
    Button(button_frame, text=strings["exit"], command=win.close, width=15).pack(
        side="left", padx=5
    )

    win.content.grid_rowconfigure(1, weight=1)
    win.content.grid_columnconfigure(0, weight=1)
    win.content.grid_rowconfigure(3, weight=1)

    win.mainloop()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--gui":
        create_gui_compiler_hub()
    else:
        cli_compiler_hub()
