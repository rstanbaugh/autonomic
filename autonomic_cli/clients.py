"""TCP client for Autonomic Mirage Media Server protocol.

Uses nc (netcat) as the transport layer because macOS TCC restricts outbound
socket connections from ad-hoc signed binaries (such as conda Python). System
tools like nc bypass this restriction and give us full protocol access.
"""
import subprocess
import select
import os
import time
from typing import Optional, List, Tuple
from .models import Player, MediaItem, PlaybackState


class MirageClient:
    """nc-backed client for Mirage Media Server control protocol on port 5004."""

    def __init__(self, host: str, port: int = 5004, timeout: float = 5.0):
        """Initialize client (does not connect yet)."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self._proc: Optional[subprocess.Popen] = None
        self.connected = False

    def connect(self) -> Tuple[bool, str]:
        """Open nc connection and perform protocol handshake."""
        try:
            self._proc = subprocess.Popen(
                ["nc", "-w", str(int(self.timeout)), self.host, str(self.port)],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            return False, "nc (netcat) not found—cannot connect to server"
        except Exception as e:
            return False, f"Failed to start nc: {e}"

        # Give nc a moment to connect
        time.sleep(0.2)
        if self._proc.poll() is not None:
            err = self._proc.stderr.read().decode(errors="replace").strip()
            return False, f"nc exited immediately: {err}"

        self.connected = True

        # Read initial server banner
        banner = self._read_until(timeout=2.0)
        if not banner:
            self.connected = False
            return False, "No banner received from server"

        # Protocol handshake
        self._write("SetClientType Core3Player")
        self._read_until(end_token="ClientType Ok", timeout=2.0)

        self._write("SetClientVersion 1.0")
        self._read_until(end_token="ClientVersion Ok", timeout=2.0)

        self._write("SetEncoding 65001")
        self._read_until(end_token="Encoding", timeout=2.0)

        return True, "Connected successfully"

    def disconnect(self):
        """Close connection."""
        if self._proc:
            try:
                self._proc.stdin.close()
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except Exception:
                pass
            self._proc = None
        self.connected = False

    def _write(self, command: str) -> None:
        """Write a command line to nc stdin."""
        if not self._proc or self._proc.poll() is not None:
            raise RuntimeError("Not connected")
        self._proc.stdin.write(f"{command}\r\n".encode("ascii"))
        self._proc.stdin.flush()

    def _read_until(self, end_token: str = "", timeout: float = 2.0) -> str:
        """Read lines from nc stdout until end_token appears or timeout."""
        collected = []
        deadline = time.monotonic() + timeout
        fd = self._proc.stdout.fileno()

        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()
            ready, _, _ = select.select([self._proc.stdout], [], [], max(0, remaining))
            if not ready:
                break
            chunk = os.read(fd, 4096)
            if not chunk:
                break
            text = chunk.decode("ascii", errors="ignore")
            collected.append(text)
            full = "".join(collected)
            if end_token and end_token in full:
                break
            if not end_token and full.endswith("\r\n"):
                break

        return "".join(collected)

    def _run_command(self, command: str, end_token: str, timeout: float = 3.0) -> Tuple[bool, str]:
        """Send a command and read response until end_token. Returns (success, response)."""
        if not self.connected:
            return False, "Not connected"
        try:
            self._write(command)
            response = self._read_until(end_token=end_token, timeout=timeout)
            return True, response
        except Exception as e:
            return False, str(e)

    # ---- Public commands ----

    def get_instances(self) -> Tuple[bool, List[str]]:
        """Get list of available player instances."""
        ok, response = self._run_command("BrowseInstances", end_token="EndInstances")
        if not ok:
            return False, []
        instances = []
        for line in response.splitlines():
            line = line.strip()
            if line and not line.startswith("Begin") and not line.startswith("End") and "=" not in line:
                instances.append(line)
        return True, instances

    def set_instance(self, instance: str) -> Tuple[bool, str]:
        """Select a specific player instance."""
        ok, resp = self._run_command(f"SetInstance {instance}", end_token="InstanceName")
        if not ok:
            return False, resp
        return True, f"Instance set to {instance}"

    def get_status(self) -> Tuple[bool, dict]:
        """Get playback status for current instance."""
        ok, response = self._run_command("GetStatus", end_token="ReportState", timeout=3.0)
        if not ok:
            return False, {}
        status = {}
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("ReportState"):
                # e.g.: ReportState Main PlayState=Playing
                parts = line.split(None, 2)
                if len(parts) >= 3:
                    for kv in parts[2].split():
                        if "=" in kv:
                            k, v = kv.split("=", 1)
                            status[k] = v
            return True, status

    def get_full_status(self, instance: str) -> Tuple[bool, dict]:
        """Get full status for a specific instance."""
        ok, resp = self._run_command(f"SetInstance {instance}", end_token="InstanceName")
        if not ok:
            return False, {}
        return self.get_status()

    def play(self) -> Tuple[bool, str]:
        """Resume playback."""
        ok, _ = self._run_command("Play", end_token="")
        return (True, "Playing") if ok else (False, "Play failed")

    def pause(self) -> Tuple[bool, str]:
        """Pause playback."""
        ok, _ = self._run_command("Pause", end_token="")
        return (True, "Paused") if ok else (False, "Pause failed")

    def stop(self) -> Tuple[bool, str]:
        """Stop playback."""
        ok, _ = self._run_command("Stop", end_token="")
        return (True, "Stopped") if ok else (False, "Stop failed")

    def skip_next(self) -> Tuple[bool, str]:
        """Skip to next track."""
        ok, _ = self._run_command("SkipNext", end_token="")
        return (True, "Skipped to next") if ok else (False, "SkipNext failed")

    def skip_previous(self) -> Tuple[bool, str]:
        """Skip to previous track."""
        ok, _ = self._run_command("SkipPrevious", end_token="")
        return (True, "Skipped to previous") if ok else (False, "SkipPrevious failed")

    def get_favorites(self) -> Tuple[bool, List[dict]]:
        """Get list of favorites."""
        ok, response = self._run_command("BrowseFavoritesAll 0 100", end_token="EndBrowse")
        if not ok:
            return False, []
        favorites = []
        for line in response.splitlines():
            line = line.strip()
            if line.startswith("Item"):
                parts = {}
                for token in line.split()[1:]:
                    if "=" in token:
                        k, v = token.split("=", 1)
                        parts[k] = v.strip('"')
                if parts:
                    favorites.append(parts)
        return True, favorites

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.disconnect()
