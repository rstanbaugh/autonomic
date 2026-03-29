"""Data models for Autonomic Mirage responses and internal structures."""
from dataclasses import dataclass, asdict, field
from typing import Any, Optional, Dict
from enum import Enum
import json
import yaml


class PlaybackState(Enum):
    """Playback states."""
    PLAYING = "Playing"
    PAUSED = "Paused"
    STOPPED = "Stopped"
    UNKNOWN = "Unknown"


@dataclass
class MediaItem:
    """Represents currently playing media."""
    track: str = ""
    artist: str = ""
    album: str = ""
    art_url: str = ""
    service: str = ""
    duration: int = 0
    current_time: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Player:
    """Represents a Mirage player instance."""
    name: str
    description: str = ""
    status: PlaybackState = PlaybackState.UNKNOWN
    media: MediaItem = field(default_factory=MediaItem)
    volume: int = 0
    muted: bool = False

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "description": self.description,
            "status": self.status.value,
            "media": self.media.to_dict(),
            "volume": self.volume,
            "muted": self.muted,
        }


@dataclass
class CLIResponse:
    """Standard response contract for CLI output."""
    success: bool
    message: str
    error: Optional[str] = None
    data: Optional[Any] = None

    def to_dict(self) -> dict:
        """Convert to dict for JSON/YAML serialization."""
        result = {
            "success": self.success,
            "message": self.message,
        }
        if self.error:
            result["error"] = self.error
        if self.data is not None:
            result["data"] = self.data
        return result

    def to_json(self) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=2)

    def to_yaml(self) -> str:
        """Serialize to YAML."""
        return yaml.dump(self.to_dict(), default_flow_style=False)

    def to_text(self) -> str:
        """Simple text representation."""
        text = self.message
        if self.error:
            text = f"ERROR: {self.error}"
        return text
