#!/usr/bin/env bash
set -u
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

HOST="${E2E_HOST:-127.0.0.1}"
PORT="${E2E_PORT:-8879}"
HEALTH_URL="${E2E_HEALTH_URL:-http://${HOST}:${PORT}/healthz}"
WAIT_SECONDS="${E2E_SERVER_WAIT_SECONDS:-60}"

SERVER_PID=""
TMP_DIR=""

healthcheck() {
	python3 - "$HEALTH_URL" <<'PY' >/dev/null 2>&1
import sys
import urllib.request

try:
    with urllib.request.urlopen(sys.argv[1], timeout=1) as response:
        sys.exit(0 if response.status == 200 else 1)
except Exception:
    sys.exit(1)
PY
}

cleanup() {
	if [ -n "$SERVER_PID" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
		kill "$SERVER_PID" 2>/dev/null || true
		wait "$SERVER_PID" 2>/dev/null || true
	fi
	if [ -n "$TMP_DIR" ]; then
		rm -rf "$TMP_DIR"
	fi
}

run_tests() {
	if [ "$#" -gt 0 ]; then
		"$@"
	else
		(
			cd "$REPO_ROOT/e2e" || exit 1
			npm test
		)
	fi
}

if healthcheck; then
	echo "[e2e] Reusing existing app.web server at $HEALTH_URL"
	run_tests "$@"
	exit $?
fi

TMP_DIR="$(mktemp -d)"
trap 'status=$?; cleanup; exit "$status"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

echo "[e2e] Starting app.web server at http://${HOST}:${PORT}"
(
	cd "$REPO_ROOT" || exit 1
	env -u LOCAL_AI_MODEL_PROVIDER -u LOCAL_AI_OLLAMA_MODEL \
		LOCAL_AI_MODEL_PROVIDER=mock \
		LOCAL_AI_OLLAMA_MODEL= \
		LOCAL_AI_MOCK_STREAM_DELAY_MS=10 \
		LOCAL_AI_SQLITE_DB_PATH="$TMP_DIR/test.db" \
		python3 -m app.web --host "$HOST" --port "$PORT"
) &
SERVER_PID=$!

ready=0
for _ in $(seq 1 "$WAIT_SECONDS"); do
	if healthcheck; then
		ready=1
		break
	fi
	if ! kill -0 "$SERVER_PID" 2>/dev/null; then
		server_status=0
		wait "$SERVER_PID" 2>/dev/null || server_status=$?
		echo "[e2e] app.web server exited before becoming healthy (exit ${server_status})" >&2
		exit 1
	fi
	sleep 1
done

if [ "$ready" -ne 1 ]; then
	echo "[e2e] Timed out waiting for $HEALTH_URL" >&2
	exit 1
fi

run_tests "$@"
