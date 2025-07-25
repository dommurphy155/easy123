import os
import ast
import subprocess
import shutil
from pathlib import Path
from datetime import datetime


# -------------------- SETTINGS --------------------
REPO_DIR = Path(__file__).resolve().parent
GIT_COMMIT_MSG = f"🧹 Auto-import fixer run on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
FILE_EXTENSIONS = [".py"]
EXCLUDED_FILES = {"__init__.py", "venv", "env"}
# --------------------------------------------------

def log(msg):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    print(f"{timestamp} {msg}")

def is_importable(module_path):
    try:
        subprocess.check_output(['python3', '-c', f'import {module_path}'], stderr=subprocess.STDOUT)
        return True
    except subprocess.CalledProcessError:
        return False

def fix_imports(file_path: Path):
    if file_path.name in EXCLUDED_FILES:
        return False

    with open(file_path, "r") as f:
        original_code = f.read()

    tree = ast.parse(original_code)
    import_lines = []
    for node in tree.body:
        if isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
            line = original_code.splitlines()[node.lineno - 1]
            import_lines.append((node.lineno, line.strip()))

    fixed_lines = original_code.splitlines()
    changed = False
    for lineno, line in import_lines:
        stripped = line.strip()
        test_line = stripped.replace("from ", "").replace("import ", "").split(" ")[0]
        test_line = test_line.split(".")[0]
        if is_importable(test_line):
            log(f"   ✅ Module '{test_line}' is importable")
        else:
            log(f"   ❌ Module '{test_line}' is NOT importable\n   ⛔ Skipping import from: {test_line}")
            fixed_lines[lineno - 1] = f"# {line}  # ⛔ commented out (not importable)"
            changed = True

    if changed:
        backup_path = file_path.with_suffix(file_path.suffix + ".bak")
        shutil.copy(file_path, backup_path)
        with open(file_path, "w") as f:
            f.write("\n".join(fixed_lines))
        log(f"💾 Backup created: {backup_path.name}")
        log(f"✅ Fixed imports: {file_path.name}")
        return True

    return False

def get_all_python_files(root_dir: Path):
    return [
        file for file in root_dir.rglob("*.py")
        if all(excl not in str(file) for excl in EXCLUDED_FILES)
    ]

def git_auto_commit_and_push():
    log("📤 Auto committing and pushing to GitHub...")
    try:
        subprocess.run(["git", "add", "."], check=True, cwd=REPO_DIR)
        subprocess.run(["git", "commit", "-m", GIT_COMMIT_MSG], check=True, cwd=REPO_DIR)
        subprocess.run(["git", "push"], check=True, cwd=REPO_DIR)
        log("✅ Pushed to GitHub successfully.")
    except subprocess.CalledProcessError as e:
        log(f"❌ Git push failed: {e}")

# -------------------- MAIN --------------------
if __name__ == "__main__":
    log("🚀 Starting import fix scan...")
    py_files = get_all_python_files(REPO_DIR)
    log(f"🔍 Found {len(py_files)} Python files to scan.\n")

    files_changed = 0
    for file in py_files:
        log(f"📄 Scanning file: {file.name}")
        if fix_imports(file):
            files_changed += 1
            log(f"✅ Done fixing imports for: {file.name}\n")

    log("🏁 All files processed.")

    if files_changed > 0:
        git_auto_commit_and_push()
    else:
        log("⚠️ No changes detected. Skipping Git push.")
    
