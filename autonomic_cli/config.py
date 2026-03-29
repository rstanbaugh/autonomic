"""Configuration management for autonomic-cli."""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


class Config:
    """Load and manage configuration from env vars, .env file, and CLI args."""

    def __init__(self):
        # Load .env file if it exists
        env_file = Path.cwd() / ".env"
        if env_file.exists():
            load_dotenv(env_file)

        # Load from environment with defaults
        self.host: str = os.getenv("AUTONOMIC_HOST", "")
        self.port: int = int(os.getenv("AUTONOMIC_PORT", "5004"))
        self.default_player: str = os.getenv("AUTONOMIC_DEFAULT_PLAYER", "Main")
        self.verbose: bool = os.getenv("AUTONOMIC_VERBOSE", "false").lower() == "true"

    def validate(self) -> tuple[bool, str]:
        """Validate required config. Returns (is_valid, error_message)."""
        if not self.host:
            return False, "AUTONOMIC_HOST not set. Set via env var, .env file, or --host flag."
        if self.port <= 0 or self.port > 65535:
            return False, f"Invalid AUTONOMIC_PORT: {self.port}. Must be 1-65535."
        return True, ""

    def update_from_args(self, host: Optional[str] = None, port: Optional[int] = None, 
                         player: Optional[str] = None, verbose: bool = False):
        """Update config from CLI arguments (highest precedence)."""
        if host:
            self.host = host
        if port:
            self.port = port
        if player:
            self.default_player = player
        if verbose:
            self.verbose = verbose
