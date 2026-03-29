"""Output formatting utilities for tables, JSON, YAML."""
from typing import List, Dict, Any
from io import StringIO
from rich.console import Console
from rich.table import Table
from .models import CLIResponse, Player


def format_players_table(players: List[Player]) -> str:
    """Format list of players as a table."""
    table = Table(title="Mirage Players")
    table.add_column("Player", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Current", style="magenta")
    table.add_column("Service", style="yellow")

    for player in players:
        current_track = f"{player.media.track}" if player.media.track else "-"
        service = player.media.service or "-"
        table.add_row(player.name, player.status.value, current_track, service)

    # Render table to string
    output = StringIO()
    console = Console(file=output, force_terminal=True)
    console.print(table)
    return output.getvalue()


def format_status_table(player: Player) -> str:
    """Format a single player's now-playing status as a table."""
    table = Table(title=f"Now Playing - {player.name}")
    table.add_column("Field", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Track", player.media.track or "-")
    table.add_row("Artist", player.media.artist or "-")
    table.add_row("Album", player.media.album or "-")
    table.add_row("Service", player.media.service or "-")
    table.add_row("Status", player.status.value)
    if player.media.art_url:
        table.add_row("Art URL", player.media.art_url)

    # Render table to string
    output = StringIO()
    console = Console(file=output, force_terminal=True)
    console.print(table)
    return output.getvalue()


def format_response(response: CLIResponse, output_format: str = "text") -> str:
    """Format a CLI response according to requested format."""
    if output_format == "json":
        return response.to_json()
    elif output_format == "yaml":
        return response.to_yaml()
    else:  # text
        # If data contains a table-like structure, return formatted
        if isinstance(response.data, str) and ("\n" in response.data or "─" in response.data):
            return response.data
        # Otherwise simple text
        if response.success:
            msg = response.message
            if response.data:
                msg += f"\n{response.data}"
            return msg
        else:
            return f"ERROR: {response.error or response.message}"
