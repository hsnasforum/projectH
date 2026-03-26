from __future__ import annotations

import re
from pathlib import Path


_WINDOWS_DRIVE_PATTERN = re.compile(r"^(?P<drive>[A-Za-z]):[\\/](?P<rest>.*)$")
_WSL_UNC_PATTERN = re.compile(r"^[\\/]{2}wsl(?:\.localhost|\$)[\\/][^\\/]+[\\/](?P<rest>.*)$", re.IGNORECASE)


def normalize_local_path_input(raw_path: str) -> Path:
    normalized = raw_path.strip()

    drive_match = _WINDOWS_DRIVE_PATTERN.match(normalized)
    if drive_match:
        drive = drive_match.group("drive").lower()
        rest = drive_match.group("rest").replace("\\", "/").lstrip("/")
        return Path("/mnt") / drive / rest

    wsl_unc_match = _WSL_UNC_PATTERN.match(normalized)
    if wsl_unc_match:
        rest = wsl_unc_match.group("rest").replace("\\", "/").lstrip("/")
        return Path("/") / rest

    return Path(normalized).expanduser()
