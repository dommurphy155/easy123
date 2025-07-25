import os
import ast
import subprocess
from pathlib import Path
from datetime import datetime
import re

ROOT_DIR = Path(os.getcwd())
LOG_FILE = ROOT_DIR / "autofix_log.txt"
_import_cache = {}

MAX_LINE_LENGTH = 79
INDENT_SIZE = 4
INDENT_STR = " " * INDENT_SIZE
MAX_FILE_SIZE = 1_000_000  # 1MB max size to process (skip bigger)

def _log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def find_py_files(base_dir="."):
    files = []
    for root, _, filenames in os.walk(base_dir):
        # skip hidden dirs
        if any(part.startswith('.') for part in Path(root).parts):
            continue
        for file in filenames:
            if file.startswith('.'):
                continue  # skip hidden files
            if not file.endswith(".py"):
                continue
            full_path = Path(root) / file
            files.append(full_path)
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

def _fix_relative_import(node):
    if isinstance(node, ast.ImportFrom) and node.level > 0:
        prefix = "." * node.level
        mod = node.module or ""
        names = ', '.join(n.name for n in node.names)
        print(f"   🔄 Found relative import: from {prefix}{mod} import {names}")
        return f"from {prefix}{mod} import {names}\n"
    return None

def normalize_indentation(lines):
    normalized = []
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            normalized.append("\n")
            continue
        leading = line[:len(line) - len(stripped)]
        # Replace tabs with spaces (4 spaces per tab)
        leading_spaces = leading.replace("\t", INDENT_STR)
        space_count = len(leading_spaces.expandtabs(INDENT_SIZE))
        indent_levels = space_count // INDENT_SIZE
        new_indent = INDENT_STR * indent_levels
        normalized.append(new_indent + stripped)
    return normalized

def split_long_line(line, max_length=MAX_LINE_LENGTH):
    if len(line) <= max_length:
        return [line]
    parts = re.split(r'(, |\s)', line)
    if len(parts) == 1:
        # No spaces or commas to split, split hard
        return [line[i:i+max_length] for i in range(0, len(line), max_length)]
    split_lines = []
    current_line = ""
    for part in parts:
        if len(current_line) + len(part) <= max_length:
            current_line += part
        else:
            split_lines.append(current_line.rstrip())
            current_line = part
    if current_line:
        split_lines.append(current_line.rstrip())
    return split_lines

def read_file_with_fallback(path):
    # Try utf-8 first, then fallback to latin1 (windows-1252 is close)
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except UnicodeDecodeError:
        _log(f"⚠️ UTF-8 decode failed on {path}, trying latin1 fallback")
        with open(path, "r", encoding="latin1") as f:
            return f.read()

def fix_imports_and_formatting(file_path):
    print(f"\n📄 Processing {file_path}")

    # Skip files too large
    if file_path.stat().st_size > MAX_FILE_SIZE:
        _log(f"⚠️ Skipping large file (>1MB): {file_path}")
        print(f"⚠️ Skipping large file (>1MB): {file_path}")
        return False

    source = read_file_with_fallback(file_path)

    try:
        tree = ast.parse(source, filename=str(file_path))
    except SyntaxError as e:
        _log(f"❌ Syntax error in {file_path} line {e.lineno}:{e.offset} {e.msg}")
        print(f"❌ Syntax error line {e.lineno}:{e.offset} - {e.msg}")
        return False
    except Exception as e:
        _log(f"❌ Failed to parse AST {file_path}: {e}")
        print(f"❌ Failed to parse AST: {e}")
        return False

    imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
    fixed_imports = []
    seen = set()

    for node in imports:
        rel = _fix_relative_import(node)
        if rel:
            fixed_imports.append(rel)
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                mod = alias.name.split('.')[0]
                if mod not in seen:
                    if _is_importable(mod):
                        fixed_imports.append(f"import {alias.name}\n")
                        seen.add(mod)
        elif isinstance(node, ast.ImportFrom):
            mod = node.module.split('.')[0] if node.module else ""
            if mod and mod not in seen:
                names = ', '.join(n.name for n in node.names)
                if _is_importable(mod):
                    fixed_imports.append(f"from {node.module} import {names}\n")
                    seen.add(mod)

    # Strip trailing whitespace and normalize line endings to LF
    lines = source.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True)
    non_import_lines = [line.rstrip() + "\n" for line in lines if not line.lstrip().startswith(("import ", "from "))]

    non_import_lines = normalize_indentation(non_import_lines)

    # Sort imports alphabetically and remove duplicates if any
    fixed_imports = sorted(set(fixed_imports))

    final_lines = []
    # imports first
    for line in fixed_imports:
        split_lines = split_long_line(line.rstrip('\n'))
        for l in split_lines:
            final_lines.append(l.rstrip() + "\n")
    final_lines.append("\n")  # one blank line after imports

    # then rest of the code
    for line in non_import_lines:
        split_lines = split_long_line(line.rstrip('\n'))
        for l in split_lines:
            final_lines.append(l.rstrip() + "\n")

    original_content = "".join(lines)
    new_content = "".join(final_lines)
    if original_content != new_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(final_lines)
        _log(f"✅ Fixed {file_path}")
        print(f"✅ Fixed {file_path}")
        return True
    else:
        print(f"   No changes needed for {file_path}")
        return False

def git_commit_push():
    print("\n🚀 Running git add, commit, and push...")

    # Check if there is anything to commit
    status = subprocess.run(["git", "diff-index", "--quiet", "HEAD", "--"])
    if status.returncode == 0:
        print("No changes to commit.")
        _log("No changes to commit.")
        return

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
    _log("🚀 Starting autofix run...")
    py_files = find_py_files()
    fixed_any = False
    for file in py_files:
        if fix_imports_and_formatting(file):
            fixed_any = True

    if fixed_any:
        git_commit_push()
    else:
        _log("No files needed fixing.")
        print("No files needed fixing.")

    _log("🏁 Autofix run complete.")

if __name__ == "__main__":
    main()
