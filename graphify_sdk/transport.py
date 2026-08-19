"""Stdio/JSON-RPC transport for the Graphify MCP protocol.

Manages the lifecycle of a ``graphify`` subprocess and provides
JSON-RPC 2.0 request/response over stdin/stdout pipes.

Zero external dependencies: uses only the Python standard library
(``subprocess``, ``json``, ``threading``).

Lazy initialization: the subprocess spawns on the first request.
"""

from __future__ import annotations

import json
import subprocess
import threading
from typing import Any


class Transport:
    """Manages a graphify subprocess and provides JSON-RPC 2.0 calls.

    Thread-safe: uses a lock for all subprocess I/O.

    Args:
        binary_path: Path to the ``graphify`` binary (default: ``"graphify"``).
        timeout: I/O timeout in seconds (default: 30).
        cwd: Working directory for the subprocess (optional).
    """

    def __init__(
        self,
        binary_path: str = "graphify",
        timeout: float = 30.0,
        cwd: str | None = None,
    ) -> None:
        self._binary_path = binary_path
        self._timeout = timeout
        self._cwd = cwd

        self._lock = threading.Lock()
        self._process: subprocess.Popen | None = None
        self._request_id = 0
        self._started = False

    # ── Lifecycle ───────────────────────────────────────────────────────

    def start(self) -> None:
        """Spawn the graphify subprocess. Idempotent — safe to call multiple times."""
        with self._lock:
            if self._started:
                return

            self._process = subprocess.Popen(
                [self._binary_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self._cwd,
                text=True,
            )
            self._started = True

    def stop(self) -> None:
        """Terminate the graphify subprocess and clean up."""
        with self._lock:
            self._stop_locked()

    def _stop_locked(self) -> None:
        if not self._started:
            return
        proc = self._process
        if proc:
            try:
                proc.stdin.close()  # type: ignore[union-attr]
            except OSError:
                pass
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        self._process = None
        self._started = False

    @property
    def is_running(self) -> bool:
        """Whether the subprocess is currently running."""
        with self._lock:
            return (
                self._started
                and self._process is not None
                and self._process.poll() is None
            )

    # ── JSON-RPC ────────────────────────────────────────────────────────

    def call(self, method: str, args: dict[str, Any] | None = None) -> dict[str, Any]:
        """Send a JSON-RPC 2.0 request and return the decoded result.

        Args:
            method: The MCP tool method name (e.g. ``"graphify_graph_summary"``).
            args: Tool arguments (optional).

        Returns:
            The parsed result content as a dict.

        Raises:
            TransportError: On I/O or process errors.
            ProtocolError: On JSON-RPC protocol errors.
            EngineError: On errors returned by the graphify engine.
        """
        self.start()

        if args is None:
            args = {}

        with self._lock:
            self._request_id += 1
            req_id = self._request_id

            request = json.dumps(
                {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "method": "tools/call",
                    "params": {"name": method, "arguments": args},
                }
            )

            proc = self._process
            if proc is None or proc.stdin is None:
                from .errors import TransportError

                raise TransportError("subprocess not started")

            try:
                proc.stdin.write(request + "\n")
                proc.stdin.flush()
            except OSError as e:
                self._stop_locked()
                from .errors import TransportError

                raise TransportError(
                    f"write stdin: {e}"
                ) from e

            import select

            # Wait for response with timeout
            if proc.stdout is None:
                from .errors import TransportError

                raise TransportError("stdout not available")


            readable, _, _ = select.select([proc.stdout], [], [], self._timeout)
            if not readable:
                self._stop_locked()
                from .errors import TransportError

                raise TransportError(f"timeout after {self._timeout}s")

            line = proc.stdout.readline()
            if not line:
                from .errors import TransportError

                raise TransportError("stdout closed (process exited)")

        return self._parse_response(line)

    def _parse_response(self, line: str) -> dict[str, Any]:
        import json as _json

        from .errors import EngineError, ProtocolError

        try:
            resp = _json.loads(line)
        except _json.JSONDecodeError as e:
            raise ProtocolError(f"parse response: {e}") from e

        if not isinstance(resp, dict):
            raise ProtocolError(f"expected object, got {type(resp).__name__}")

        if "error" in resp and resp["error"] is not None:
            err = resp["error"]
            raise EngineError(
                code=err.get("code", 0),
                message=err.get("message", "unknown error"),
                data=err.get("data"),
            )

        result_raw = resp.get("result")
        if result_raw is None:
            return {}

        # MCP result: content array of text items
        if isinstance(result_raw, dict):
            content = result_raw.get("content")
            if isinstance(content, list) and len(content) > 0:
                combined = "".join(
                    c.get("text", "") for c in content if isinstance(c, dict)
                )
                if combined.strip():
                    try:
                        parsed = _json.loads(combined)
                        if isinstance(parsed, dict):
                            return parsed
                    except _json.JSONDecodeError:
                        pass
                    return {"text": combined}

        return result_raw  # type: ignore[return-value]