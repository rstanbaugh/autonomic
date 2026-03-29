"""Autonomic CLI - Control Autonomic Mirage Media Servers from the command line."""

__version__ = "0.1.0"
__author__ = "Autonomic CLI Contributors"

from .main import cli
from .config import Config
from .clients import MirageClient

__all__ = ["cli", "Config", "MirageClient"]
