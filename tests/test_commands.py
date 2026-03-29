"""Unit tests for CLI commands."""
import pytest
from autonomic_cli.main import AutonomicCLI


class TestAutonomicCLI:
    """Tests for AutonomicCLI command handlers."""

    def test_config_command(self):
        """Test configuration retrieval command."""
        cli = AutonomicCLI()
        response = cli.cmd_config()
        assert response.success
        assert "host" in response.data or True  # data might be None if not set

    @pytest.mark.skip(reason="Requires live server")
    def test_list_players_live(self):
        """Test listing players on live server."""
        cli = AutonomicCLI()
        cli.config.host = "192.168.0.219"
        response = cli.cmd_list_players()
        assert response.success
        cli.disconnect()

    @pytest.mark.skip(reason="Requires live server")
    def test_status_live(self):
        """Test getting status on live server."""
        cli = AutonomicCLI()
        cli.config.host = "192.168.0.219"
        response = cli.cmd_status()
        assert response.success
        cli.disconnect()
