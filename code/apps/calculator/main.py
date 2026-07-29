"""Simple calculator app for Lipi OS."""
from __future__ import annotations

import ast
import operator
import sys


OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.USub: operator.neg,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
}


def safe_eval(expr: str) -> float:
    """Evaluate a basic arithmetic expression safely."""
    node = ast.parse(expr, mode="eval")

    def _eval(n):
        if isinstance(n, ast.Expression):
            return _eval(n.body)
        if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
            return n.value
        if isinstance(n, ast.BinOp) and type(n.op) in OPS:
            return OPS[type(n.op)](_eval(n.left), _eval(n.right))
        if isinstance(n, ast.UnaryOp) and type(n.op) in OPS:
            return OPS[type(n.op)](_eval(n.operand))
        raise ValueError("Unsupported expression")

    return float(_eval(node))


def run_gui() -> None:
    import tkinter as tk

    root = tk.Tk()
    root.title("Lipi Calculator")
    root.geometry("280x360")
    root.resizable(False, False)

    display = tk.StringVar(value="0")
    entry = tk.Entry(
        root,
        textvariable=display,
        font=("Courier", 18),
        justify="right",
        bd=8,
        relief="sunken",
    )
    entry.pack(fill="x", padx=8, pady=8)

    def press(char: str) -> None:
        current = display.get()
        if current == "0" and char not in (".", "+", "-", "*", "/"):
            display.set(char)
        elif current in ("Error",):
            display.set(char)
        else:
            display.set(current + char)

    def clear() -> None:
        display.set("0")

    def equals() -> None:
        try:
            result = safe_eval(display.get())
            display.set(str(result))
        except Exception:
            display.set("Error")

    buttons = [
        ["7", "8", "9", "/"],
        ["4", "5", "6", "*"],
        ["1", "2", "3", "-"],
        ["0", ".", "=", "+"],
    ]

    grid = tk.Frame(root)
    grid.pack(expand=True, fill="both", padx=8, pady=8)

    for r, row in enumerate(buttons):
        for c, label in enumerate(row):
            cmd = equals if label == "=" else (lambda ch=label: press(ch))
            tk.Button(grid, text=label, font=("Arial", 14), command=cmd).grid(
                row=r, column=c, sticky="nsew", padx=2, pady=2
            )

    tk.Button(root, text="Clear", command=clear).pack(fill="x", padx=8, pady=(0, 8))

    for i in range(4):
        grid.grid_columnconfigure(i, weight=1)
        grid.grid_rowconfigure(i, weight=1)

    root.mainloop()


def run_cli() -> None:
    print("Lipi Calculator (type 'q' to quit)")
    while True:
        try:
            expr = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if expr.lower() in ("q", "quit", "exit"):
            break
        if not expr:
            continue
        try:
            print(safe_eval(expr))
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    if "--cli" in sys.argv:
        run_cli()
    else:
        try:
            run_gui()
        except Exception:
            run_cli()
