import os
import ast
import subprocess
from pathlib import Path
from datetime import datetime


ROOT_DIR = Path(os.getcwd())
LOG_FILE = ROOT_DIR / "autofix_log.txt"
_import_cache = {}

def find_py_files(base_dir="."):
    files = [
        Path(root) / file
        for root, _, files in os.walk(base_dir)
        for file in files
        if file.endswith(".py")
        and "venv" not in root
        and "site-packages" not in root
    ]
    _log(f"🔍 Found {len(files)} Python files to scan.")
    return files

def _is_importable(module):
    if module in _import_cache:
        return _import_cache[module]
    result = subprocess.run(
        ["python3", "-c", f"import {module}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _import_cache[module] = (result.returncode == 0)
    if _import_cache[module]:
        print(f"   ✅ Module '{module}' is importable")
    else:
        print(f"   ❌ Module '{module}' is NOT importable")
    return _import_cache[module]

def _fix_relative_import(node, file_path):
    if isinstance(node, ast.ImportFrom) and node.level > 0:
        prefix = "." * node.level
        mod = node.module or ""
        names = ', '.join(n.name for n in node.names)
        print(f"   🔄 Found relative import: from {prefix}{mod} import {names}")
        return f"from {prefix}{mod} import {names}\n"
    return None

def fix_imports(file_path):
    print(f"\n📄 Scanning file: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source, filename=str(file_path))
    except Exception as e:
        _log(f"❌ Skipping broken file {file_path}: {e}")
        print(f"❌ Could not parse AST: {e}")
        return False

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
                    if mod not in seen:
                        print(f"→ Trying: import {alias.name}")
                        if _is_importable(mod):
                            fixed_lines.append(f"import {alias.name}\n")
                            seen.add(mod)
                        else:
                            print(f"   ⛔ Skipping import: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                mod = node.module.split('.')[0] if node.module else ""
                if mod and mod not in seen:
                    names = ', '.join(n.name for n in node.names)
                    print(f"→ Trying: from {node.module} import {names}")
                    if _is_importable(mod):
                        fixed_lines.append(f"from {node.module} import {names}\n")
                        seen.add(mod)
                    else:
                        print(f"   ⛔ Skipping import from: {node.module}")
        except Exception as e:
            _log(f"⚠️ Skipped import in {file_path}: {e}")
            print(f"⚠️ Error processing import: {e}")

    non_imports = [line for line in source.splitlines(keepends=True) if not line.strip().startswith(("import ", "from "))]
    updated = fixed_lines + ["\n"] + non_imports

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(updated)

    _log(f"✅ Fixed imports: {file_path}")
    print(f"✅ Done fixing imports for: {file_path}")
    return True

def _log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def git_commit_push():
    print("\n🚀 Running git add, commit, and push...")
    commit_message = f"🔁 Auto import fix on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Git commit and push successful.")
        _log("✅ Git commit and push successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        _log(f"❌ Git operation failed: {e}")

def main():
    _log("🚀 Starting import fix scan...")
    py_files = find_py_files()
    fixed_any = False
    for path in py_files:
        fixed = fix_imports(path)
        if fixed:
            fixed_any = True

    if fixed_any:
        git_commit_push()
    else:
        print("No files fixed, skipping git commit/push.")
        _log("No files fixed, skipping git commit/push.")

    _log("🏁 All files processed.")

if __name__ == "__main__":
    main()
