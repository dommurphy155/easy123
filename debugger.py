import os
import sys
import subprocess
import traceback

REPO_DIR = os.path.abspath(os.path.dirname(__file__))
REPORT_FILE = os.path.join(REPO_DIR, "debug_report.txt")
CRITICAL_ENV_VARS = [
    "TELEGRAM_TOKEN",
    "TELEGRAM_CHAT_ID",
    "HF_API_KEY",
    "INDEED_COOKIES_PATH"
]
EXCLUDED_DIRS = {"venv", "__pycache__", ".git", "site-packages"}

def log(msg):
    print(msg)
    with open(REPORT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def clear_report():
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)

def check_env_vars():
    log("🚨 === Checking Critical Environment Variables ===")
    missing = []
    for var in CRITICAL_ENV_VARS:
        if not os.getenv(var):
            log(f"❌ MISSING: '{var}' is NOT set!")
            missing.append(var)
        else:
            log(f"✅ OK: '{var}' is set")
    log("")
    return missing

def check_syntax(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        compile(source, file_path, "exec")
        return None
    except Exception as e:
        return f"❌ Syntax error in {file_path}: {e}"

def run_import_check(file_path):
    rel_path = os.path.relpath(file_path, REPO_DIR)
    module_name = rel_path[:-3].replace(os.sep, ".")  # strip .py, convert to module format
    cmd = [
        sys.executable, "-c",
        f"import sys; sys.path.insert(0, '{REPO_DIR}'); import {module_name}"
    ]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode != 0:
            return f"{file_path}: {proc.stderr.strip()}"
    except subprocess.TimeoutExpired:
        return f"{file_path}: ❌ Import timeout."
    except Exception as e:
        return f"{file_path}: ❌ Import failed - {e}"
    return None

def scan_py_and_txt_files():
    log("🚨 === Scanning .py and .txt Files ===")
    errors = []
    for root, dirs, files in os.walk(REPO_DIR):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for file in files:
            if not file.endswith((".py", ".txt")):
                continue
            full_path = os.path.join(root, file)
            if file.endswith(".py"):
                syntax_err = check_syntax(full_path)
                if syntax_err:
                    log(syntax_err)
                    errors.append(syntax_err)
                    continue
                import_err = run_import_check(full_path)
                if import_err:
                    log(f"❌ Import error: {import_err}")
                    errors.append(import_err)
    log("")
    return errors

def check_config_integrity():
    log("🚨 === Checking config.py File ===")
    config_path = os.path.join(REPO_DIR, "config.py")
    if not os.path.isfile(config_path):
        msg = "❌ config.py is missing!"
        log(msg)
        return [msg]
    err = check_syntax(config_path)
    if err:
        log(err)
        return [err]
    log("✅ config.py looks OK.")
    return []

def suggest_fixes(missing_env, file_errors, config_errors):
    log("🚨 === Suggested Fixes ===")
    if missing_env:
        for var in missing_env:
            log(f"⚠️ Set env var '{var}' in .env or system env.")
    if file_errors:
        log("⚠️ Fix all syntax/import errors above.")
    if config_errors:
        log("⚠️ config.py is invalid or missing.")
    if not (missing_env or file_errors or config_errors):
        log("🎉 No critical issues found. Bot is ready to run.")
    log("")

def try_git_commit_push():
    log("🚨 === Attempting Git Commit & Push ===")
    try:
        subprocess.run(["git", "add", REPORT_FILE], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "Auto: Add debug report"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        log("✅ Git push successful.")
    except subprocess.CalledProcessError as e:
        log(f"❌ Git command failed: {e}")
    except Exception as e:
        log(f"❌ Git push error: {e}")

def main():
    clear_report()
    log(f"🐞 Debugging project at: {REPO_DIR}\n")

    missing_env = check_env_vars()
    file_errors = scan_py_and_txt_files()
    config_errors = check_config_integrity()

    suggest_fixes(missing_env, file_errors, config_errors)

    if missing_env or file_errors or config_errors:
        try_git_commit_push()

if __name__ == "__main__":
    main()
