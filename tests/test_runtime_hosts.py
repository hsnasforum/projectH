from __future__ import annotations

import unittest
from unittest import mock

import config.runtime_hosts as runtime_hosts


class RuntimeHostTests(unittest.TestCase):
    def test_resolve_bind_host_defaults_to_localhost_outside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=False):
            self.assertEqual(runtime_hosts.resolve_bind_host(), "127.0.0.1")

    def test_resolve_bind_host_defaults_to_all_interfaces_inside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            self.assertEqual(runtime_hosts.resolve_bind_host(), "0.0.0.0")

    def test_resolve_bind_host_respects_explicit_host(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            self.assertEqual(
                runtime_hosts.resolve_bind_host(explicit_host="127.0.0.1"),
                "127.0.0.1",
            )

    def test_browser_host_for_bind_maps_all_interfaces_to_loopback(self) -> None:
        self.assertEqual(runtime_hosts.browser_host_for_bind("0.0.0.0"), "127.0.0.1")
        self.assertEqual(runtime_hosts.browser_host_for_bind("127.0.0.1"), "127.0.0.1")

    def test_windows_fallback_host_returns_none_outside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=False):
            self.assertIsNone(runtime_hosts.windows_fallback_host())

    def test_windows_fallback_host_uses_first_ipv4_inside_wsl(self) -> None:
        with mock.patch.object(runtime_hosts, "running_in_wsl", return_value=True):
            with mock.patch.object(
                runtime_hosts.subprocess,
                "check_output",
                return_value="172.20.128.246 fe80::1\n",
            ):
                self.assertEqual(
                    runtime_hosts.windows_fallback_host(),
                    "172.20.128.246",
                )
