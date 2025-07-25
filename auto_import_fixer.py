import os
import ast
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(os.getcwd())
LOG_FILE = ROOT_DIR / "autofix_log.txt"

_import_cache = {}

def find_py_files(base_dir="."):
    return [
        Path(root) / file
        for root, _, files in os.walk(base_dir)
        for file in files
        if file.endswith(".py")
        and "venv" not in root
        and "site-packages" not in root
    ]

def backup_file(file_path):
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")
    shutil.copy2(file_path, backup_path)
    _log(f"💾 Backup created: {backup_path}")

def _is_importable(module):
    if module in _import_cache:
        return _import_cache[module]
    result = subprocess.run(
        ["python3", "-c", f"import {module}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _import_cache[module] = (result.returncode == 0)
    return _import_cache[module]

def _fix_relative_import(node, file_path):
    if isinstance(node, ast.ImportFrom) and node.level > 0:
        prefix = "." * node.level
        mod = node.module or ""
        names = ', '.join(n.name for n in node.names)
        return f"from {prefix}{mod} import {names}\n"
    return None

def fix_imports(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except Exception as e:
        _log(f"❌ Skipping broken file {file_path}: {e}")
        return

    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    fixed_lines = []
    seen = set()

    for node in imports:
        try:
            rel = _fix_relative_import(node, file_path)
            if rel:
                fixed_lines.append(rel)
                continue

            if isinstance(node, ast.Import):
                for alias in node.names:
                    mod = alias.name.split('.')[0]
                    if mod not in seen and _is_importable(mod):
                        fixed_lines.append(f"import {alias.name}\n")
                        seen.add(mod)
            elif isinstance(node, ast.ImportFrom):
                mod = node.module.split('.')[0] if node.module else ""
                if mod and mod not in seen and _is_importable(mod):
                    names = ', '.join(n.name for n in node.names)
                    fixed_lines.append(f"from {node.module} import {names}\n")
                    seen.add(mod)
        except Exception as e:
            _log(f"⚠️ Skipped import in {file_path}: {e}")

    non_imports = [line for line in source.splitlines(keepends=True) if not line.strip().startswith(("import ", "from "))]
    updated = fixed_lines + ["\n"] + non_imports

    backup_file(file_path)
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(updated)

    _log(f"✅ Fixed imports: {file_path}")

def _log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def main():
    _log("🔎 Starting import fix scan...")
    py_files = find_py_files()
    for path in py_files:
        fix_imports(path)
    _log("✅ All done.")

if __name__ == "__main__":
    main()
