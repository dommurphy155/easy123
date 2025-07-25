from datetime import datetime
from pathlib import Path
import ast
import os
import re
import subprocess
import sys
import importlib.util
import traceback

#!/usr/bin/env python3

ROOT_DIR = Path(os.getcwd())
LOG_FILE = ROOT_DIR / "autofix_log.txt"
_import_cache = {}

MAX_LINE_LENGTH = 79
INDENT_SIZE = 4
INDENT_STR = " " * INDENT_SIZE
MAX_FILE_SIZE = 1_000_000  # 1MB max size to process (skip bigger)

# Metrics counters for rating
_metrics = {
    "files_processed": 0,
    "imports_fixed": 0,
    "indentation_fixed": 0,
    "line_length_fixed": 0,
    "syntax_errors_fixed": 0,
    "files_skipped_big": 0,
    "runtime_issues": 0,
}

_issue_report = {}

def _log(message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"[{timestamp}] {message}")

def find_py_files(base_dir="."):
    files = []
    for root, _, filenames in os.walk(base_dir):
        parts = Path(root).parts
        # Skip hidden dirs, venvs, site-packages, __pycache__, env folders
        if any(part.startswith('.') for part in parts):
            continue
        if any(part in ('venv', 'env', '__pycache__', 'site-packages') for part in parts):
            continue
        for file in filenames:
            if file.startswith('.'):
                continue
            if not (file.endswith(".py") or file.endswith(".txt")):
                continue
            full_path = Path(root) / file
            files.append(full_path)
    _log(f"🔍 Found {len(files)} Python/text files to scan.")
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
    fixed = False
    for line in lines:
        stripped = line.lstrip()
        if not stripped:
            normalized.append("\n")
            continue
        leading = line[:len(line) - len(stripped)]
        leading_spaces = leading.replace("\t", INDENT_STR)
        space_count = len(leading_spaces.expandtabs(INDENT_SIZE))
        indent_levels = space_count // INDENT_SIZE
        new_indent = INDENT_STR * indent_levels
        if new_indent != leading:
            fixed = True
        normalized.append(new_indent + stripped)
    if fixed:
        _metrics["indentation_fixed"] += 1
    return normalized

def split_long_line(line, max_length=MAX_LINE_LENGTH):
    if len(line) <= max_length:
        return [line]
    parts = re.split(r'(, |\s)', line)
    if len(parts) == 1:
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
    if len(split_lines) > 1:
        _metrics["line_length_fixed"] += 1
    return split_lines

def read_file_with_fallback(path):
    try:
        with open(path, "r", encoding="utf-8-sig") as f:
            return f.read()
    except UnicodeDecodeError:
        _log(f"⚠️ UTF-8 decode failed on {path}, trying latin1 fallback")
        with open(path, "r", encoding="latin1") as f:
            return f.read()

def fix_indentation_errors(source):
    lines = source.splitlines()
    fixed_lines = []
    for line in lines:
        line = line.replace("\t", INDENT_STR)
        stripped = line.lstrip()
        leading_spaces = len(line) - len(stripped)
        corrected_indent = (leading_spaces // INDENT_SIZE) * INDENT_SIZE
        fixed_lines.append(INDENT_STR * (corrected_indent // INDENT_SIZE) + stripped)
    _metrics["indentation_fixed"] += 1
    return "\n".join(fixed_lines) + "\n"

def fix_imports_and_formatting(file_path):
    print(f"\n📄 Processing {file_path}")

    if file_path.stat().st_size > MAX_FILE_SIZE:
        _log(f"⚠️ Skipping large file (>1MB): {file_path}")
        print(f"⚠️ Skipping large file (>1MB): {file_path}")
        _metrics["files_skipped_big"] += 1
        return False

    source = read_file_with_fallback(file_path)

    if file_path.suffix == ".py":
        try:
            tree = ast.parse(source, filename=str(file_path))
        except SyntaxError as e:
            if "indent" in e.msg.lower():
                _log(f"⚠️ Indentation error in {file_path} line {e.lineno}: trying auto-fix")
                print(f"⚠️ Indentation error detected, trying fix...")

                fixed_source = fix_indentation_errors(source)
                try:
                    tree = ast.parse(fixed_source, filename=str(file_path))
                    source = fixed_source
                    _log(f"✅ Indentation error fixed in {file_path}")
                    print(f"✅ Indentation error fixed.")
                    _metrics["syntax_errors_fixed"] += 1
                except Exception as e2:
                    _log(f"❌ Failed to fix indentation in {file_path}: {e2}")
                    print(f"❌ Could not fix indentation: {e2}")
                    return False
            else:
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
        imports_fixed_this_file = 0

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
                            imports_fixed_this_file += 1
            elif isinstance(node, ast.ImportFrom):
                mod = node.module.split('.')[0] if node.module else ""
                if mod and mod not in seen:
                    names = ', '.join(n.name for n in node.names)
                    if _is_importable(mod):
                        fixed_imports.append(f"from {node.module} import {names}\n")
                        seen.add(mod)
                        imports_fixed_this_file += 1

        _metrics["imports_fixed"] += imports_fixed_this_file

        lines = source.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True)
        non_import_lines = [line.rstrip() + "\n" for line in lines if not line.lstrip().startswith(("import ", "from "))]

        non_import_lines = normalize_indentation(non_import_lines)

        fixed_imports = sorted(set(fixed_imports))

        final_lines = []
        for line in fixed_imports:
            split_lines = split_long_line(line.rstrip('\n'))
            for l in split_lines:
                final_lines.append(l.rstrip() + "\n")
        final_lines.append("\n")

        for line in non_import_lines:
            split_lines = split_long_line(line.rstrip('\n'))
            for l in split_lines:
                final_lines.append(l.rstrip() + "\n")

        original_content = "".join(lines)
        new_content = "".join(final_lines)

    else:
        # For non-python (.txt) just do indentation normalization
        lines = source.replace("\r\n", "\n").replace("\r", "\n").splitlines(keepends=True)
        normalized = normalize_indentation(lines)
        original_content = "".join(lines)
        new_content = "".join(normalized)

    _metrics["files_processed"] += 1

    if original_content != new_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(new_content)
        _log(f"✅ Fixed {file_path}")
        print(f"✅ Fixed {file_path}")
        return True
    else:
        print(f"   No changes needed for {file_path}")
        return False

def check_runtime_issues():
    """Checks for runtime issues such as cookie loading and Telegram bot instantiation."""

    # 1. Check if 'cookies' file or environment variable is present and readable
    cookies_paths = [ROOT_DIR / "cookies.json", ROOT_DIR / "cookies.txt"]
    cookie_found = False
    for cpath in cookies_paths:
        if cpath.exists() and cpath.is_file():
            try:
                with open(cpath, 'r') as f:
                    _ = f.read()
                cookie_found = True
                print(f"✅ Cookies file found and readable: {cpath}")
                break
            except Exception as e:
                _log(f"❌ Cookies file found but not readable: {cpath} - {e}")
                _metrics["runtime_issues"] += 1
                _issue_report.setdefault("cookies", []).append(f"Unreadable cookie file {cpath}")
    if not cookie_found:
        # Also check env vars for cookies
        if "COOKIES" in os.environ and os.environ["COOKIES"].strip():
            print("✅ Cookies found in environment variable COOKIES")
        else:
            _log("❌ No cookies file or environment variable 'COOKIES' found")
            _metrics["runtime_issues"] += 1
            _issue_report.setdefault("cookies", []).append("No cookies found (file or env)")

    # 2. Check if Telegram token env var is set and looks valid (non-empty)
    telegram_token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    if telegram_token:
        print("✅ TELEGRAM_TOKEN environment variable is set")
    else:
        _log("❌ TELEGRAM_TOKEN environment variable is not set or empty")
        _metrics["runtime_issues"] += 1
        _issue_report.setdefault("telegram", []).append("Missing TELEGRAM_TOKEN env variable")

    # 3. Check if telegram python library is importable
    if _is_importable("telegram"):
        print("✅ Telegram python package is importable")
    else:
        _log("❌ Telegram python package is NOT importable")
        _metrics["runtime_issues"] += 1
        _issue_report.setdefault("telegram", []).append("telegram python package missing")

    # 4. Try to import and instantiate a Telegram Bot object to catch basic issues
    try:
        import telegram
        bot = telegram.Bot(token=telegram_token)
        # Optional: get_me to check token validity (timeout 5s)
        bot.get_me()
        print("✅ Telegram bot instantiated and token validated")
    except Exception as e:
        _log(f"❌ Failed to instantiate Telegram bot or validate token: {e}")
        _metrics["runtime_issues"] += 1
        _issue_report.setdefault("telegram", []).append(f"Bot instantiation or token validation failed: {e}")

def print_runtime_issues_report():
    if not _issue_report:
        print("\n✅ No runtime issues detected.")
        _log("✅ No runtime issues detected.")
        return
    print("\n❌ Runtime Issues Detected:")
    for category, issues in _issue_report.items():
        print(f"\n - {category.upper()} issues:")
        for issue in issues:
            print(f"   * {issue}")
    _log(f"❌ Runtime issues found: {_issue_report}")

def git_commit_push():
    print("\n🚀 Running git add, commit, and push...")

    status = subprocess.run(["git", "diff-index", "--quiet", "HEAD", "--"])
    if status.returncode == 0:
        print("No changes to commit.")
        _log("No changes to commit.")
        return

    commit_message = f"🔁 Auto import fix on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    try:
        subprocess.run(["git", "add", "."], check=True)
        subprocess.run(["git", "commit", "-m", commit_message], check=True)
        subprocess.run(["git", "pull", "--rebase"], check=True)
        subprocess.run(["git", "push"], check=True)
        print("✅ Git commit and push successful.")
        _log("✅ Git commit and push successful.")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git operation failed: {e}")
        _log(f"❌ Git operation failed: {e}")

def print_code_rating():
    if _metrics["files_processed"] == 0:
        print("\n⚠️ No Python/text files processed, no rating available.")
        return

    imp_fix = _metrics["imports_fixed"]
    imp_score = max(10 - imp_fix, 1)

    indent_fix = _metrics["indentation_fixed"]
    indent_score = max(10 - indent_fix, 1)

    line_len_fix = _metrics["line_length_fixed"]
    line_len_score = max(10 - line_len_fix, 1)

    syntax_fix = _metrics["syntax_errors_fixed"]
    syntax_score = max(10 - syntax_fix, 1)

    big_files = _metrics["files_skipped_big"]
    big_file_score = 10 if big_files == 0 else max(10 - big_files, 1)

    runtime_issues = _metrics["runtime_issues"]
    runtime_score = max(10 - runtime_issues, 1)

    avg_score = (imp_score + indent_score + line_len_score + syntax_score + big_file_score + runtime_score) / 6

    print("\n📊 Code Quality Rating Summary:")
    print(f" - Files processed: {_metrics['files_processed']}")
    print(f" - Imports fixed: {_metrics['imports_fixed']} (Import hygiene score: {imp_score}/10)")
    print(f" - Indentation fixes: {_metrics['indentation_fixed']} (Indentation consistency score: {indent_score}/10)")
    print(f" - Line length fixes: {_metrics['line_length_fixed']} (Line length adherence score: {line_len_score}/10)")
    print(f" - Syntax errors fixed: {_metrics['syntax_errors_fixed']} (Syntax correctness score: {syntax_score}/10)")
    print(f" - Large files skipped: {_metrics['files_skipped_big']} (File size safety score: {big_file_score}/10)")
    print(f" - Runtime issues: {_metrics['runtime_issues']} (Runtime environment score: {runtime_score}/10)")
    print(f"\n=> Average code quality score: {avg_score:.2f}/10")

    if avg_score >= 9:
        print("Overall: Excellent code hygiene and formatting.")
    elif avg_score >= 7:
        print("Overall: Good, with minor improvements needed.")
    elif avg_score >= 5:
        print("Overall: Fair, needs attention in some areas.")
    else:
        print("Overall: Poor, requires significant fixes.")

    _log(f"📊 Code Quality Rating: {avg_score:.2f}/10")

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

    print_code_rating()

    _log("🔍 Starting runtime environment checks...")
    check_runtime_issues()
    print_runtime_issues_report()

    _log("🏁 Autofix and environment check run complete.")

if __name__ == "__main__":
    main()
