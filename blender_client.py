"""TCP client for the Blender MCP addon (localhost:9876 by default)."""

import json
import os
import socket
import tempfile
import threading
from typing import Any


class BlenderConnectionError(Exception):
    pass


class BlenderClient:
    """Talks to the Blender addon using its JSON command protocol."""

    def __init__(
        self,
        host: str | None = None,
        port: int | None = None,
        timeout: float = 180.0,
    ):
        self.host = host or os.getenv("BLENDER_HOST", "localhost")
        self.port = port or int(os.getenv("BLENDER_PORT", "9876"))
        self.timeout = timeout
        self._sock: socket.socket | None = None
        self._lock = threading.Lock()

    def connect(self) -> None:
        if self._sock:
            return
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        try:
            sock.connect((self.host, self.port))
        except OSError as e:
            sock.close()
            raise BlenderConnectionError(
                f"Cannot reach Blender at {self.host}:{self.port}. "
                "Open Blender, enable the MCP addon, and start its server."
            ) from e
        self._sock = sock

    def disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def ping(self) -> dict[str, Any]:
        """Light check that the addon responds."""
        return self.send_command("get_scene_info")

    def send_command(
        self, command_type: str, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        with self._lock:
            if not self._sock:
                self.connect()
            command = {"type": command_type, "params": params or {}}
            try:
                assert self._sock is not None
                self._sock.sendall(json.dumps(command).encode("utf-8"))
                raw = self._receive_full_response(self._sock)
                response = json.loads(raw.decode("utf-8"))
            except (ConnectionError, BrokenPipeError, ConnectionResetError) as e:
                self.disconnect()
                raise BlenderConnectionError(f"Lost connection to Blender: {e}") from e
            except OSError as e:
                self.disconnect()
                raise BlenderConnectionError(f"Blender socket error: {e}") from e
            except json.JSONDecodeError as e:
                self.disconnect()
                raise BlenderConnectionError(f"Invalid JSON from Blender: {e}") from e

            if response.get("status") == "error":
                message = response.get("message", "Unknown Blender error")
                raise BlenderConnectionError(message)

            result = response.get("result", {})
            if isinstance(result, dict) and "error" in result:
                raise BlenderConnectionError(str(result["error"]))
            return result

    def execute_code(self, code: str) -> str:
        result = self.send_command("execute_code", {"code": code})
        output = result.get("result") or result.get("executed")
        if output is True:
            return "Code executed successfully."
        return str(output) if output else "Code executed successfully."

    def get_scene_info(self) -> dict[str, Any]:
        return self.send_command("get_scene_info")

    def get_object_info(self, object_name: str) -> dict[str, Any]:
        return self.send_command("get_object_info", {"object_name": object_name})

    def get_viewport_screenshot_png(self, max_size: int = 800) -> bytes:
        path = os.path.join(
            tempfile.gettempdir(),
            f"blender_tutor_viewport_{os.getpid()}.png",
        )
        try:
            result = self.send_command(
                "get_viewport_screenshot",
                {"max_size": max_size, "filepath": path, "format": "png"},
            )
            if isinstance(result, dict) and "error" in result:
                raise BlenderConnectionError(str(result["error"]))
            if not os.path.isfile(path):
                raise BlenderConnectionError("Viewport screenshot file was not created")
            with open(path, "rb") as f:
                return f.read()
        finally:
            if os.path.isfile(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def _receive_full_response(self, sock: socket.socket, buffer_size: int = 8192) -> bytes:
        chunks: list[bytes] = []
        sock.settimeout(self.timeout)
        while True:
            try:
                chunk = sock.recv(buffer_size)
            except socket.timeout:
                break
            if not chunk:
                if not chunks:
                    raise BlenderConnectionError(
                        "Connection closed before Blender sent a response"
                    )
                break
            chunks.append(chunk)
            try:
                data = b"".join(chunks)
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError:
                continue
        if chunks:
            data = b"".join(chunks)
            try:
                json.loads(data.decode("utf-8"))
                return data
            except json.JSONDecodeError as e:
                raise BlenderConnectionError("Incomplete response from Blender") from e
        raise BlenderConnectionError("No data received from Blender")


_default_client: BlenderClient | None = None
_client_lock = threading.Lock()


def get_blender_client() -> BlenderClient:
    global _default_client
    with _client_lock:
        if _default_client is None:
            _default_client = BlenderClient()
        return _default_client


def check_blender_connection() -> tuple[bool, str]:
    client = get_blender_client()
    try:
        client.disconnect()
        info = client.ping()
        name = info.get("name", "scene")
        count = info.get("object_count", "?")
        return True, f"Blender connected — {name} ({count} objects)"
    except BlenderConnectionError as e:
        return False, str(e)
    except Exception as e:
        return False, f"Blender error: {e}"
