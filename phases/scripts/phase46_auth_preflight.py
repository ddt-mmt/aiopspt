#!/usr/bin/env python3
"""Offline-only auth/config inventory. No network, API, DB, or config changes."""
from pathlib import Path
import re
import os

ROOTS = [
    Path("/root/grafan_aiops"),
    Path("/etc/zabbix"),
]
MAX_FILE_SIZE = 1_000_000
MAX_FILES = 2500

CONFIG_NAMES = {
    "docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml",
    ".env", "zabbix_server.conf", "zabbix_agentd.conf",
    "zabbix_proxy.conf", "script_aiops.py",
}
TEXT_SUFFIXES = {".py", ".ini", ".conf", ".yaml", ".yml", ".env",
                 ".md", ".txt", ".json", ".sh"}

SECRET_KEY = re.compile(
    r"(password|passwd|secret|token|api[_-]?key|authorization|credential)",
    re.I,
)
AUTH_KEY = re.compile(
    r"(zabbix_url|zabbix_server|api[_-]?token|user(name)?|auth|login|"
    r"access[_-]?token|tls|certificate|verify_ssl)",
    re.I,
)
PERMISSION_TERMS = re.compile(
    r"(read.only|read_only|user.?role|api.?access|permission|"
    r"role.?id|user.?group|api.?token|history\.get|item\.get)",
    re.I,
)

def safe_key_lines(path):
    """Print key names and line numbers only, never values."""
    try:
        lines = path.read_text(errors="ignore").splitlines()
    except (OSError, UnicodeError):
        return [], []
    auth, perms = [], []
    for n, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ";")):
            continue
        # YAML/env/INI/Python assignments: expose key only, not the value.
        match = re.match(r'^\s*["\']?([A-Za-z_][A-Za-z0-9_.-]*)["\']?\s*[:=]', stripped)
        key = match.group(1) if match else ""
        if key and AUTH_KEY.search(key):
            auth.append((n, key, bool(SECRET_KEY.search(key))))
        if PERMISSION_TERMS.search(stripped):
            # Report only line number and classification, never source text.
            perms.append((n, "permission/role-related reference"))
    return auth, perms

print("PHASE 46 — OFFLINE AUTH/PERMISSION PREFLIGHT")
print("Network/API/DB calls: NONE")
print("Configuration changes: NONE")
print("Secret values: NEVER PRINTED")
print()

count = 0
auth_count = 0
permission_count = 0
credential_files = 0

for root in ROOTS:
    if not root.exists():
        print(f"[INFO] Root absent: {root}")
        continue

    for base, dirs, files in os.walk(root, followlinks=False):
        dirs[:] = [d for d in dirs if d not in {
            ".git", "__pycache__", "node_modules", ".venv", "venv"
        }]
        for name in files:
            p = Path(base) / name
            if p.is_symlink():
                continue
            if name not in CONFIG_NAMES and p.suffix.lower() not in TEXT_SUFFIXES:
                continue
            count += 1
            if count > MAX_FILES:
                print("[LIMIT] File scan capped; results are partial.")
                break
            try:
                if p.stat().st_size > MAX_FILE_SIZE:
                    continue
            except OSError:
                continue

            auth, perms = safe_key_lines(p)
            if auth:
                auth_count += len(auth)
                print(f"[CONFIG] {p}")
                for line_no, key, is_secret in auth[:30]:
                    if is_secret:
                        print(f"  line {line_no}: {key}=<REDACTED>")
                    else:
                        print(f"  line {line_no}: key={key}; value=<not shown>")
            if perms:
                permission_count += len(perms)
                print(f"[PERMISSION REFERENCE] {p}")
                for line_no, desc in perms[:20]:
                    print(f"  line {line_no}: {desc}")

            # Identify possible credential files by filename only.
            low = name.lower()
            if any(x in low for x in ("secret", "credential", "token", "passwd")):
                credential_files += 1
                print(f"[SENSITIVE-FILE-PATH] {p} (contents not read or printed)")

        if count > MAX_FILES:
            break

print()
print(f"Files scanned: {min(count, MAX_FILES)}")
print(f"Auth-related key references: {auth_count}")
print(f"Permission-related references: {permission_count}")
print(f"Potential sensitive filenames found: {credential_files}")
print()
print("EFFECTIVE ZABBIX API PERMISSIONS: NOT VERIFIED")
print("Reason: local config references do not prove server-side effective rights.")
print("No login, token test, API request, history retrieval, or DB query was made.")
print("NEXT: review findings and identify a documented, authoritative permission source.")
