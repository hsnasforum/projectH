"""Pipeline runtime supervisor package."""

__all__ = ["RuntimeSupervisor"]


def __getattr__(name: str):
    if name == "RuntimeSupervisor":
        from .supervisor import RuntimeSupervisor

        return RuntimeSupervisor
    raise AttributeError(name)
