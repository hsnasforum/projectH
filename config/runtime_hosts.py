from __future__ import annotations

import os
from pathlib import Path
import re
import subprocess

_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


def running_in_wsl() -> bool:
    if os.environ.get("WSL_INTEROP") or os.environ.get("WSL_DISTRO_NAME"):
        return True
    try:
        return "microsoft" in Path("/proc/version").read_text(encoding="utf-8").lower()
    except OSError:
        return False


def resolve_bind_host(
    *,
    explicit_host: str | None = None,
    prefer_all_interfaces_in_wsl: bool = True,
) -> str:
    normalized = (explicit_host or "").strip()
    if normalized:
        return normalized
    if prefer_all_interfaces_in_wsl and running_in_wsl():
        return "0.0.0.0"
    return "127.0.0.1"


def browser_host_for_bind(bind_host: str) -> str:
    return "127.0.0.1" if bind_host == "0.0.0.0" else bind_host


def windows_fallback_host() -> str | None:
    if not running_in_wsl():
        return None
    try:
        output = subprocess.check_output(["hostname", "-I"], text=True, timeout=2.0).strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError, OSError):
        return None
    for candidate in output.split():
        if _IPV4_RE.match(candidate):
            return candidate
    return None
