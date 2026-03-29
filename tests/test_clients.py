"""Unit tests for protocol client."""
import subprocess
import pytest
from autonomic_cli.clients import MirageClient
from autonomic_cli.config import Config


class TestMirageClient:
    """Tests for MirageClient."""

    def test_init(self):
        """Test client initialization."""
        client = MirageClient("192.168.0.219", 5004)
        assert client.host == "192.168.0.219"
        assert client.port == 5004
        assert not client.connected

    @pytest.mark.skip(reason="Requires live server")
    def test_connect_live(self):
        """Test connection to live server (requires AUTONOMIC_HOST env var)."""
        client = MirageClient("192.168.0.219", 5004, timeout=2.0)
        success, msg = client.connect()
        assert success, msg
        assert client.connected
        client.disconnect()

    @pytest.mark.skip(reason="Requires live server")
    def test_get_instances_live(self):
        """Test getting instance list from live server."""
        client = MirageClient("192.168.0.219", 5004, timeout=2.0)
        success, msg = client.connect()
        if success:
            success, instances = client.get_instances()
            assert success
            assert len(instances) > 0
            assert "Main" in instances
            client.disconnect()


class TestSmokeNetwork:
    """Smoke tests for network reachability of the Mirage server."""

    def _host(self):
        cfg = Config()
        return cfg.host or "192.168.0.219"

    def test_http_reachable(self):
        """Smoke test: Mirage HTTP interface responds (nginx 302)."""
        host = self._host()
        result = subprocess.run(
            ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}", "--connect-timeout", "3", f"http://{host}/"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"curl failed: {result.stderr}"
        assert result.stdout.strip() in ("200", "301", "302"), f"Unexpected HTTP status: {result.stdout.strip()}"

    def test_tcp_5004_reachable(self):
        """Smoke test: Mirage control port 5004 accepts TCP connections (via nc)."""
        host = self._host()
        result = subprocess.run(
            ["nc", "-z", "-w", "3", host, "5004"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        assert result.returncode == 0, f"nc failed to connect to {host}:5004"
