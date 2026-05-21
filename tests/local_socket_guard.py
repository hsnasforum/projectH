import socket
import unittest


LOCAL_LOOPBACK_SOCKET_UNAVAILABLE = "local loopback socket unavailable in this environment"


def local_loopback_socket_available() -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
        return True
    except OSError:
        return False


requires_local_loopback_socket = unittest.skipUnless(
    local_loopback_socket_available(),
    LOCAL_LOOPBACK_SOCKET_UNAVAILABLE,
)


def skip_unless_local_loopback_socket(test_case: unittest.TestCase) -> None:
    if not local_loopback_socket_available():
        test_case.skipTest(LOCAL_LOOPBACK_SOCKET_UNAVAILABLE)
