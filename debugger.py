#!/usr/bin/env python3

import ast
import os
import re
import sys
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(os.getcwd())
LOG_FILE = ROOT_DIR / "safe_fix_log.txt"
REPORT_FILE = ROOT_DIR / "safe_fix_report.txt"

def _log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] {msg}\n")
    print(f"[{timestamp}] {msg}")

def find_py_files(base_dir="."):
    for root, _, files in os.walk(base_dir):
        parts = Path(root).parts
        if any(p.startswith('.') for p in parts):
            continue
        for file in files:
            if file.endswith(".py"):
                yield Path(root) / file

def read_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(path, "r", encoding="latin1") as f:
            return f.read()

def fix_trailing_commas_in_imports(source):
    lines = source.splitlines()
    fixed = False
    new_lines = []
    for line in lines:
        stripped = line.strip()
        if (stripped.startswith("import ") or stripped.startswith("from ")) and stripped.endswith(","):
            fixed = True
            line = line.rstrip(", \t")
        new_lines.append(line)
    return "\n".join(new_lines), fixed

def fix_tabs_to_spaces(source):
    if "\t" not in source:
        return source, False
    fixed_source = source.replace("\t", "    ")
    return fixed_source, True

def check_syntax(source, filename):
    try:
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, e

def check_imports(source, filename, issues):
    try:
        tree = ast.parse(source)
    except Exception:
        # Already checked syntax, so should not fail here
        return

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split(".")[0]
                if not is_importable(mod):
                    issues.append(f"{filename}:{node.lineno} Missing import: {mod}")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if node.level > 0:
                issues.append(f"{filename}:{node.lineno} Relative import: {'.'*node.level}{mod} — verify manually")
            else:
                base_mod = mod.split(".")[0]
                if base_mod and not is_importable(base_mod):
                    issues.append(f"{filename}:{node.lineno} Missing import: {base_mod}")

_import_cache = {}

def is_importable(module):
    if module in _import_cache:
        return _import_cache[module]
    try:
        __import__(module)
        _import_cache[module] = True
    except ImportError:
        _import_cache[module] = False
    return _import_cache[module]

def main():
    _log("Starting safe autofix run...")

    issues = []
    files_fixed = 0

    for pyfile in find_py_files():
        source = read_file(pyfile)

        syntax_ok, err = check_syntax(source, pyfile)
        if not syntax_ok:
            _log(f"Syntax error in {pyfile} at line {err.lineno}: {err.msg} - skipping fixes.")
            continue

        orig_source = source

        # Fix tabs to spaces only
        source, tabs_fixed = fix_tabs_to_spaces(source)

        # Fix trailing commas in imports only
        source, commas_fixed = fix_trailing_commas_in_imports(source)

        if tabs_fixed or commas_fixed:
            with open(pyfile, "w", encoding="utf-8") as f:
                f.write(source)
            _log(f"Fixed {'tabs' if tabs_fixed else ''}{' and ' if tabs_fixed and commas_fixed else ''}{'trailing commas' if commas_fixed else ''} in {pyfile}")
            files_fixed += 1

        # Check imports and relative imports
        check_imports(source, str(pyfile), issues)

    # Log issues
    if issues:
        with open(REPORT_FILE, "w") as f:
            f.write("# Import and Syntax Issues Report\n\n")
            for issue in issues:
                f.write(issue + "\n")
        _log(f"Import issues found and reported in {REPORT_FILE}")
    else:
        _log("No import issues found.")

    _log(f"Safe autofix run complete. Files fixed: {files_fixed}")

if __name__ == "__main__":
    main()
