import ast
import unittest
from pathlib import Path
from unittest.mock import patch

from tests import local_socket_guard


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _parse_test_source(relative_path: str) -> ast.Module:
    return ast.parse((PROJECT_ROOT / relative_path).read_text(encoding="utf-8"))


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    return None


def _is_loopback_zero_tuple(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Tuple)
        and len(node.elts) == 2
        and isinstance(node.elts[0], ast.Constant)
        and node.elts[0].value == "127.0.0.1"
        and isinstance(node.elts[1], ast.Constant)
        and node.elts[1].value == 0
    )


def _is_local_only_server_call(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Call)
        and _call_name(node.func) == "LocalOnlyHTTPServer"
        and bool(node.args)
        and _is_loopback_zero_tuple(node.args[0])
    )


def _is_web_app_direct_server_call(node: ast.AST) -> bool:
    return (
        _is_local_only_server_call(node)
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Name)
        and node.args[1].id == "service"
    )


def _is_http_integration_server_call(node: ast.AST) -> bool:
    return (
        _is_local_only_server_call(node)
        and len(node.args) >= 2
        and isinstance(node.args[1], ast.Attribute)
        and node.args[1].attr == "service"
        and isinstance(node.args[1].value, ast.Name)
        and node.args[1].value.id == "self"
    )


def _decorator_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Call):
        return _call_name(node.func)
    return _call_name(node)


def _find_http_integration_set_up(tree: ast.Module) -> ast.FunctionDef:
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "HTTPIntegrationBase":
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == "setUp":
                    return item
    raise AssertionError("HTTPIntegrationBase.setUp was not found")


def _import_aliases_from(tree: ast.Module, module_name: str) -> set[tuple[str, str | None]]:
    aliases: set[tuple[str, str | None]] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module == module_name:
            aliases.update((alias.name, alias.asname) for alias in node.names)
    return aliases


def _assigned_names(tree: ast.Module) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, (ast.AnnAssign, ast.AugAssign)):
            targets = [node.target]
        else:
            continue
        for target in targets:
            for child in ast.walk(target):
                if isinstance(child, ast.Name):
                    names.add(child.id)
    return names


class _FakeSocket:
    def __init__(self, *, bind_error: OSError | None = None) -> None:
        self.bind_error = bind_error
        self.bound_address: tuple[str, int] | None = None
        self.exited = False

    def __enter__(self) -> "_FakeSocket":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.exited = True

    def bind(self, address: tuple[str, int]) -> None:
        self.bound_address = address
        if self.bind_error is not None:
            raise self.bind_error


class _FakeTestCase:
    def __init__(self) -> None:
        self.skip_reason: str | None = None

    def skipTest(self, reason: str) -> None:
        self.skip_reason = reason


class LocalSocketGuardTest(unittest.TestCase):
    def test_local_loopback_socket_available_returns_true_when_bind_succeeds(self) -> None:
        fake_socket = _FakeSocket()

        with patch.object(local_socket_guard.socket, "socket", return_value=fake_socket) as socket_factory:
            self.assertTrue(local_socket_guard.local_loopback_socket_available())

        socket_factory.assert_called_once_with(
            local_socket_guard.socket.AF_INET,
            local_socket_guard.socket.SOCK_STREAM,
        )
        self.assertEqual(fake_socket.bound_address, ("127.0.0.1", 0))
        self.assertTrue(fake_socket.exited)

    def test_local_loopback_socket_available_returns_false_when_socket_creation_fails(self) -> None:
        with patch.object(local_socket_guard.socket, "socket", side_effect=OSError("no sockets")):
            self.assertFalse(local_socket_guard.local_loopback_socket_available())

    def test_local_loopback_socket_available_returns_false_when_bind_fails(self) -> None:
        fake_socket = _FakeSocket(bind_error=OSError("bind unavailable"))

        with patch.object(local_socket_guard.socket, "socket", return_value=fake_socket):
            self.assertFalse(local_socket_guard.local_loopback_socket_available())

        self.assertEqual(fake_socket.bound_address, ("127.0.0.1", 0))
        self.assertTrue(fake_socket.exited)

    def test_skip_unless_local_loopback_socket_skips_with_exact_reason_when_unavailable(self) -> None:
        fake_case = _FakeTestCase()

        with patch.object(local_socket_guard, "local_loopback_socket_available", return_value=False):
            local_socket_guard.skip_unless_local_loopback_socket(fake_case)

        self.assertEqual(
            fake_case.skip_reason,
            local_socket_guard.LOCAL_LOOPBACK_SOCKET_UNAVAILABLE,
        )

    def test_skip_unless_local_loopback_socket_does_not_skip_when_available(self) -> None:
        fake_case = _FakeTestCase()

        with patch.object(local_socket_guard, "local_loopback_socket_available", return_value=True):
            local_socket_guard.skip_unless_local_loopback_socket(fake_case)

        self.assertIsNone(fake_case.skip_reason)


class LocalSocketGuardConsumerPlacementTest(unittest.TestCase):
    def test_web_app_imports_shared_socket_guard_alias(self) -> None:
        tree = _parse_test_source("tests/test_web_app.py")

        self.assertIn(
            ("requires_local_loopback_socket", "_requires_local_loopback_socket"),
            _import_aliases_from(tree, "tests.local_socket_guard"),
        )

    def test_web_app_does_not_recreate_file_local_socket_guard(self) -> None:
        tree = _parse_test_source("tests/test_web_app.py")
        defined_functions = {
            node.name
            for node in ast.walk(tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

        self.assertNotIn("_local_loopback_socket_available", defined_functions)
        self.assertNotIn("_requires_local_loopback_socket", _assigned_names(tree))

    def test_http_integration_imports_shared_skip_helper(self) -> None:
        tree = _parse_test_source("tests/test_http_integration.py")

        self.assertIn(
            ("skip_unless_local_loopback_socket", None),
            _import_aliases_from(tree, "tests.local_socket_guard"),
        )

    def test_web_app_direct_local_server_tests_keep_shared_guard_decorator(self) -> None:
        tree = _parse_test_source("tests/test_web_app.py")
        guarded_methods: list[str] = []
        unguarded_methods: list[str] = []

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            has_direct_server = any(_is_web_app_direct_server_call(child) for child in ast.walk(node))
            if not has_direct_server:
                continue
            decorator_names = {_decorator_name(decorator) for decorator in node.decorator_list}
            if "_requires_local_loopback_socket" in decorator_names:
                guarded_methods.append(node.name)
            else:
                unguarded_methods.append(f"{node.name}:{node.lineno}")

        self.assertGreater(
            len(guarded_methods),
            0,
            "expected at least one guarded direct LocalOnlyHTTPServer web_app test",
        )
        self.assertEqual([], unguarded_methods)

    def test_http_integration_set_up_skips_before_direct_local_server_creation(self) -> None:
        tree = _parse_test_source("tests/test_http_integration.py")
        set_up = _find_http_integration_set_up(tree)

        skip_call_lines = [
            node.lineno
            for node in ast.walk(set_up)
            if (
                isinstance(node, ast.Call)
                and _call_name(node.func) == "skip_unless_local_loopback_socket"
                and len(node.args) == 1
                and isinstance(node.args[0], ast.Name)
                and node.args[0].id == "self"
            )
        ]
        server_call_lines = [
            node.lineno
            for node in ast.walk(set_up)
            if _is_http_integration_server_call(node)
        ]

        self.assertTrue(skip_call_lines, "HTTPIntegrationBase.setUp must call the shared skip helper")
        self.assertTrue(server_call_lines, "HTTPIntegrationBase.setUp must construct the local HTTP server")
        self.assertLess(min(skip_call_lines), min(server_call_lines))


if __name__ == "__main__":
    unittest.main()
