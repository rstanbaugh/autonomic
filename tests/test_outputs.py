"""Integration tests for output formatting."""
import pytest
from autonomic_cli.models import Player, MediaItem, PlaybackState
from autonomic_cli.utils import format_players_table, format_status_table


class TestOutputFormatting:
    """Tests for output formatting functions."""

    def test_format_players_table(self):
        """Test player list table formatting."""
        players = [
            Player(
                name="Main",
                status=PlaybackState.PLAYING,
                media=MediaItem(track="Test Song", artist="Test Artist", service="Spotify"),
            ),
            Player(
                name="Player_A",
                status=PlaybackState.PAUSED,
            ),
        ]
        output = format_players_table(players)
        assert "Main" in output
        assert "Player_A" in output
        assert "Test Song" in output or "Music" in output or "-" in output

    def test_format_status_table(self):
        """Test now-playing status table formatting."""
        player = Player(
            name="Main",
            status=PlaybackState.PLAYING,
            media=MediaItem(
                track="Hello",
                artist="Adele",
                album="25",
                service="Spotify",
            ),
        )
        output = format_status_table(player)
        assert "Main" in output
        assert "Hello" in output
        assert "Adele" in output
