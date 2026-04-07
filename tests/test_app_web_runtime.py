from __future__ import annotations

import unittest
from unittest import mock

from app.web import _effective_web_host
from config.settings import AppSettings


class AppWebRuntimeTests(unittest.TestCase):
    def test_effective_web_host_defaults_to_all_interfaces_inside_wsl(self) -> None:
        settings = AppSettings()
        with mock.patch("app.web.resolve_bind_host", return_value="0.0.0.0") as resolve_mock:
            host = _effective_web_host(args_host=None, settings=settings)
        self.assertEqual(host, "0.0.0.0")
        resolve_mock.assert_called_once_with(explicit_host="")

    def test_effective_web_host_prefers_cli_override(self) -> None:
        settings = AppSettings()
        with mock.patch("app.web.resolve_bind_host", return_value="127.0.0.1") as resolve_mock:
            host = _effective_web_host(args_host="127.0.0.1", settings=settings)
        self.assertEqual(host, "127.0.0.1")
        resolve_mock.assert_called_once_with(explicit_host="127.0.0.1")

    def test_effective_web_host_uses_non_default_settings_host_as_explicit(self) -> None:
        settings = AppSettings(web_host="0.0.0.0")
        with mock.patch("app.web.resolve_bind_host", return_value="0.0.0.0") as resolve_mock:
            host = _effective_web_host(args_host=None, settings=settings)
        self.assertEqual(host, "0.0.0.0")
        resolve_mock.assert_called_once_with(explicit_host="0.0.0.0")
