"""Main CLI application and command handlers."""
import sys
import argparse
from typing import Optional
from .config import Config
from .clients import MirageClient
from .models import CLIResponse, Player, PlaybackState, MediaItem
from .utils import format_response, format_players_table, format_status_table


class AutonomicCLI:
    """Main CLI application class."""

    def __init__(self):
        self.config = Config()
        self.client: Optional[MirageClient] = None
        self.output_format = "text"

    def connect(self) -> CLIResponse:
        """Establish connection to Mirage server."""
        is_valid, error = self.config.validate()
        if not is_valid:
            return CLIResponse(success=False, message="Config validation failed", error=error)

        self.client = MirageClient(self.config.host, self.config.port)
        success, message = self.client.connect()

        if not success:
            return CLIResponse(success=False, message="Connection failed", error=message)

        # Set default instance
        success, msg = self.client.set_instance(self.config.default_player)
        if not success:
            return CLIResponse(success=False, message="Failed to set instance", error=msg)

        return CLIResponse(success=True, message=message)

    def disconnect(self):
        """Close connection."""
        if self.client:
            self.client.disconnect()

    def cmd_list_players(self, player_name: Optional[str] = None) -> CLIResponse:
        """FR1: List players and their status."""
        if not self.client or not self.client.connected:
            connect_resp = self.connect()
            if not connect_resp.success:
                return connect_resp

        try:
            success, instances = self.client.get_instances()
            if not success:
                return CLIResponse(success=False, message="Failed to list instances", error=str(instances))

            players = []
            for instance in instances:
                self.client.set_instance(instance)
                _, status_dict = self.client.get_status()

                # Build Player object from status
                media = MediaItem(
                    track=status_dict.get("TrackName", ""),
                    artist=status_dict.get("ArtistName", ""),
                    album=status_dict.get("MediaName", ""),
                    art_url=status_dict.get("ArtURL", ""),
                    service=status_dict.get("NowPlayingSrceName", ""),
                )

                play_state_str = status_dict.get("PlayState", "Stopped")
                if play_state_str == "Playing":
                    pstate = PlaybackState.PLAYING
                elif play_state_str == "Paused":
                    pstate = PlaybackState.PAUSED
                else:
                    pstate = PlaybackState.STOPPED

                player = Player(
                    name=instance,
                    description=status_dict.get("NowPlayingSrceName", ""),
                    status=pstate,
                    media=media,
                )
                players.append(player)

            # Filter by player_name if specified
            if player_name:
                players = [p for p in players if p.name.lower() == player_name.lower()]
                if not players:
                    return CLIResponse(success=False, message=f"Player not found: {player_name}")

            table_output = format_players_table(players)
            return CLIResponse(success=True, message="Players listed", data=table_output)
        except Exception as e:
            return CLIResponse(success=False, message="Error listing players", error=str(e))

    def cmd_status(self, player_name: Optional[str] = None) -> CLIResponse:
        """FR2: Get now-playing status."""
        if not self.client or not self.client.connected:
            connect_resp = self.connect()
            if not connect_resp.success:
                return connect_resp

        try:
            target_player = player_name or self.config.default_player
            self.client.set_instance(target_player)
            _, status_dict = self.client.get_status()

            # Build Player object
            media = MediaItem(
                track=status_dict.get("TrackName", ""),
                artist=status_dict.get("ArtistName", ""),
                album=status_dict.get("MediaName", ""),
                art_url=status_dict.get("ArtURL", ""),
                service=status_dict.get("NowPlayingSrceName", ""),
            )

            play_state_str = status_dict.get("PlayState", "Stopped")
            if play_state_str == "Playing":
                pstate = PlaybackState.PLAYING
            elif play_state_str == "Paused":
                pstate = PlaybackState.PAUSED
            else:
                pstate = PlaybackState.STOPPED

            player = Player(name=target_player, status=pstate, media=media)
            table_output = format_status_table(player)
            return CLIResponse(success=True, message="Status retrieved", data=table_output)
        except Exception as e:
            return CLIResponse(success=False, message="Error getting status", error=str(e))

    def cmd_playback(self, player_name: str, action: str) -> CLIResponse:
        """FR3: Execute playback control action."""
        if not self.client or not self.client.connected:
            connect_resp = self.connect()
            if not connect_resp.success:
                return connect_resp

        try:
            self.client.set_instance(player_name)

            if action == "play":
                success, msg = self.client.play()
            elif action == "pause":
                success, msg = self.client.pause()
            elif action == "stop":
                success, msg = self.client.stop()
            elif action == "toggle":
                _, status_dict = self.client.get_status()
                play_state = status_dict.get("PlayState", "Stopped")
                if play_state == "Playing":
                    success, msg = self.client.pause()
                else:
                    success, msg = self.client.play()
            elif action == "next":
                success, msg = self.client.skip_next()
            elif action == "previous":
                success, msg = self.client.skip_previous()
            elif action in ("thumbsup", "thumbsdown"):
                # TODO: implement thumbs up/down
                return CLIResponse(success=False, message=f"Action not yet implemented: {action}")
            else:
                return CLIResponse(success=False, message=f"Unknown action: {action}")

            if not success:
                return CLIResponse(success=False, message="Action failed", error=msg)

            return CLIResponse(success=True, message=msg)
        except Exception as e:
            return CLIResponse(success=False, message="Error executing action", error=str(e))

    def cmd_favorites(self) -> CLIResponse:
        """FR4: List favorites."""
        if not self.client or not self.client.connected:
            connect_resp = self.connect()
            if not connect_resp.success:
                return connect_resp

        try:
            success, favorites = self.client.get_favorites()
            if not success:
                return CLIResponse(success=False, message="Failed to get favorites", error=str(favorites))

            # TODO: format favorites list
            return CLIResponse(success=True, message=f"Found {len(favorites)} favorites", data=favorites)
        except Exception as e:
            return CLIResponse(success=False, message="Error getting favorites", error=str(e))

    def cmd_config(self) -> CLIResponse:
        """FR6: Show configuration."""
        config_data = {
            "host": self.config.host,
            "port": self.config.port,
            "default_player": self.config.default_player,
        }
        return CLIResponse(success=True, message="Configuration", data=config_data)


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        description="Autonomic Mirage Media Server CLI",
        prog="autonomic-cli",
    )

    # Global options
    parser.add_argument(
        "--host",
        help="Mirage server hostname/IP (default: $AUTONOMIC_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        help="Mirage server port (default: 5004)",
    )
    parser.add_argument(
        "--player",
        help="Default player instance (default: Main)",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="JSON output format",
    )
    parser.add_argument(
        "--yaml",
        action="store_true",
        help="YAML output format",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # list/players command
    list_parser = subparsers.add_parser("list", aliases=["players"], help="List players")
    list_parser.add_argument("player", nargs="?", help="Optional: specific player name")

    # status command
    status_parser = subparsers.add_parser("status", help="Get now-playing status")
    status_parser.add_argument("player", nargs="?", help="Optional: specific player name")

    # playback command
    play_parser = subparsers.add_parser("play", help="Play on player")
    play_parser.add_argument("player", help="Player instance name")

    pause_parser = subparsers.add_parser("pause", help="Pause player")
    pause_parser.add_argument("player", help="Player instance name")

    stop_parser = subparsers.add_parser("stop", help="Stop player")
    stop_parser.add_argument("player", help="Player instance name")

    next_parser = subparsers.add_parser("next", help="Skip to next track")
    next_parser.add_argument("player", help="Player instance name")

    prev_parser = subparsers.add_parser("previous", help="Skip to previous track")
    prev_parser.add_argument("player", help="Player instance name")

    # favorites command
    subparsers.add_parser("favorites", help="List favorites")

    # config command
    subparsers.add_parser("config", help="Show configuration")

    return parser


def cli():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Handle no command
    if not args.command:
        parser.print_help()
        sys.exit(2)

    # Initialize CLI app
    cli_app = AutonomicCLI()
    cli_app.config.update_from_args(host=args.host, port=args.port, player=args.player, verbose=args.verbose)

    if args.json:
        cli_app.output_format = "json"
    elif args.yaml:
        cli_app.output_format = "yaml"

    try:
        # Execute command
        if args.command in ("list", "players"):
            response = cli_app.cmd_list_players(args.player if hasattr(args, 'player') else None)
        elif args.command == "status":
            response = cli_app.cmd_status(args.player if hasattr(args, 'player') else None)
        elif args.command == "play":
            response = cli_app.cmd_playback(args.player, "play")
        elif args.command == "pause":
            response = cli_app.cmd_playback(args.player, "pause")
        elif args.command == "stop":
            response = cli_app.cmd_playback(args.player, "stop")
        elif args.command == "next":
            response = cli_app.cmd_playback(args.player, "next")
        elif args.command == "previous":
            response = cli_app.cmd_playback(args.player, "previous")
        elif args.command == "favorites":
            response = cli_app.cmd_favorites()
        elif args.command == "config":
            response = cli_app.cmd_config()
        else:
            response = CLIResponse(success=False, message="Unknown command", error=args.command)

        # Format and output response
        output = format_response(response, cli_app.output_format)
        print(output)

        # Exit with appropriate code
        sys.exit(0 if response.success else 1)

    except KeyboardInterrupt:
        print("\nInterrupted", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        cli_app.disconnect()


if __name__ == "__main__":
    cli()
