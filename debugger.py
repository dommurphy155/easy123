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

def log(msg):
    print(msg)
    with open(REPORT_FILE, "a") as f:
        f.write(msg + "\n")

def clear_report():
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)

def check_env_vars():
    log("🚨 === Checking Critical Environment Variables ===")
    missing = []
    for var in CRITICAL_ENV_VARS:
        val = os.getenv(var)
        if not val:
            log(f"❌ MISSING: Environment variable '{var}' is NOT set!")
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

def run_subprocess_import(file_path):
    module_name = os.path.splitext(os.path.basename(file_path))[0]
    cmd = [sys.executable, "-c", f"import sys; sys.path.insert(0, '{REPO_DIR}'); import {module_name}"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        if proc.returncode != 0:
            return proc.stderr.strip()
        return None
    except subprocess.TimeoutExpired:
        return f"❌ Timeout importing {module_name} (long import or stuck process)."
    except Exception as e:
        return f"❌ Exception importing {module_name}: {e}"

def scan_py_files():
    log("🚨 === Scanning Python Files for Syntax and Import Errors ===")
    errors = []
    for root, _, files in os.walk(REPO_DIR):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                syntax_err = check_syntax(path)
                if syntax_err:
                    log(syntax_err)
                    errors.append(syntax_err)
                    continue
                import_err = run_subprocess_import(path)
                if import_err:
                    log(f"❌ Import/runtime error in {path}:\n{import_err}\n")
                    errors.append(f"{file}: {import_err}")
    log("")
    return errors

def check_config_file():
    log("🚨 === Checking config.py File ===")
    config_path = os.path.join(REPO_DIR, "config.py")
    if not os.path.isfile(config_path):
        log("❌ config.py is missing! Bot cannot start without it.")
        return ["config.py missing"]

    syntax_err = check_syntax(config_path)
    if syntax_err:
        log(syntax_err)
        return [syntax_err]
    
    log("✅ config.py syntax is OK.")
    return []

def suggest_fixes(missing_env, file_errors, config_errors):
    log("🚨 === Suggested Fixes ===")
    if missing_env:
        for var in missing_env:
            log(f"⚠️ Set the environment variable '{var}' in your .env file or system environment.")
    if file_errors:
        log("⚠️ Fix the above syntax and import/runtime errors in the listed Python files.")
    if config_errors:
        log("⚠️ Fix config.py issues before proceeding.")
    if not missing_env and not file_errors and not config_errors:
        log("🎉 No blockers detected! Your bot should run fine.")
    log("")

def try_git_commit_push():
    log("🚨 === Attempting to Commit and Push debug_report.txt ===")
    try:
        subprocess.run(["git", "add", REPORT_FILE], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "Auto: Add debug report"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push"], cwd=REPO_DIR, check=True)
        log("✅ Git commit and push successful.")
    except subprocess.CalledProcessError as e:
        log(f"❌ Git command failed: {e}")
        log("👉 Make sure git is configured correctly and you have push access.")
    except Exception as e:
        log(f"❌ Unexpected error during git push: {e}")

def main():
    clear_report()
    log(f"🐞 Debug report started for repo: {REPO_DIR}\n")

    missing_env = check_env_vars()
    file_errors = scan_py_files()
    config_errors = check_config_file()

    all_errors = missing_env + file_errors + config_errors

    suggest_fixes(missing_env, file_errors, config_errors)

    if all_errors:
        try_git_commit_push()

if __name__ == "__main__":
    main()
    
