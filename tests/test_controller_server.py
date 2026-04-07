from __future__ import annotations

import os
import unittest
from unittest import mock

import config.runtime_hosts as runtime_hosts
import controller.server as controller_server


class ControllerServerHostTests(unittest.TestCase):
    def test_bind_host_defaults_to_localhost_outside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=False):
            with mock.patch.dict(os.environ, {}, clear=False):
                self.assertEqual(controller_server._controller_bind_host(), "127.0.0.1")

    def test_bind_host_defaults_to_all_interfaces_inside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            with mock.patch.dict(os.environ, {}, clear=False):
                self.assertEqual(controller_server._controller_bind_host(), "0.0.0.0")

    def test_bind_host_respects_explicit_override(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            with mock.patch.dict(os.environ, {"CONTROLLER_HOST": "127.0.0.1"}, clear=False):
                self.assertEqual(controller_server._controller_bind_host(), "127.0.0.1")

    def test_browser_host_uses_localhost_for_all_interfaces_bind(self) -> None:
        self.assertEqual(controller_server._controller_browser_host("0.0.0.0"), "127.0.0.1")
        self.assertEqual(controller_server._controller_browser_host("127.0.0.1"), "127.0.0.1")

    def test_windows_fallback_host_returns_none_outside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=False):
            self.assertIsNone(controller_server._controller_windows_fallback_host())

    def test_windows_fallback_host_uses_first_ipv4(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            with mock.patch.object(
                runtime_hosts.subprocess,
                "check_output",
                return_value="172.20.128.246 fe80::1\n",
            ):
                self.assertEqual(
                    controller_server._controller_windows_fallback_host(),
                    "172.20.128.246",
                )


if __name__ == "__main__":
    unittest.main()
