"""Storage layer error hierarchy."""


class SessionStoreError(RuntimeError):
    """Base error for session store operations."""


class SaveConflictError(SessionStoreError):
    """Raised when a save conflicts with a concurrent modification."""

    def __init__(self, session_id: str, expected_version: int, actual_version: int) -> None:
        self.session_id = session_id
        self.expected_version = expected_version
        self.actual_version = actual_version
        super().__init__(
            f"Save conflict for session {session_id}: "
            f"expected version {expected_version}, found {actual_version}"
        )


class SessionCorruptError(SessionStoreError):
    """Raised when a session file is corrupt and was quarantined."""

    def __init__(self, session_id: str, quarantine_path: str | None = None) -> None:
        self.session_id = session_id
        self.quarantine_path = quarantine_path
        super().__init__(
            f"Session {session_id} was corrupt and quarantined"
            + (f" at {quarantine_path}" if quarantine_path else "")
        )
