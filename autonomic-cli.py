#!/usr/bin/env python3
"""
Autonomic Mirage Media Server CLI

Top-level entry point for direct invocation.
No PYTHONPATH modification required.

Usage examples:
  autonomic-cli --help
  autonomic-cli list
  autonomic-cli status --player Main
  autonomic-cli play Main
  autonomic-cli pause Main
  autonomic-cli status --json
"""
import sys
from autonomic_cli.main import cli

if __name__ == "__main__":
    cli()
