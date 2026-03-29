# Autonomic Mirage Media Server CLI - Requirements Document

## 1. Purpose
```yaml
project:
  name: autonomic-cli
  description: A Python command-line interface to control an Autonomic Mirage Music Server
  purpose: |
    build a standalone Python command-line tool that allows user to discover and control Mirage Media Server outputs replicates the core music-first experience of the official Autonomic TuneBridge app for desktop/scripting use and OpenClaw agents.

usage_contexts:
  - standalone terminal tool for direct human use (after installation or symlink)
  - executed as a tool/skill by OpenClaw agents via bash wrapper:
    exec "$PY" "$TOOL" "$@"
    where TOOL points to autonomic-cli.py
  - simple to run standalone / easy to call as a tool from OpenClaw agents via structured output.

metadata:
  spec_date: 2026-03-28
  target_environment: Python in conda env named `openclaw`
```

## 2. Scope
### In Scope (MVP)
- Direct IP control of Autonomic Mirage Media Server (MMS-1e/3e/5e and compatible eSeries)
- Playback control (play, pause, stop, next, previous)
- Output discovery and selection (Player A, Player B, etc)
- Now-playing status with metadata and album art
- Browse and search (artists, albums, genres, playlists) across 
- Favorites and presets recall
- Human-readable tables by default
- Structured output (--json, --yaml) for automation
- Simple configuration via environment variables or .env

### Out of Scope (MVP)
- Global/TuneBridge-style search across services and local content
- Zone discovery and selection
- Volume and mute per zone
- Scene/snapshot recall (if exposed in API)
- Full graphical UI (this is CLI only)
- In-app account login flows for streaming services (assume pre-configured on the MMS)
- Advanced queue editing (reorder, delete items)
- Zone grouping / party mode (future)
- Video/OSD control
- Direct control of non-Mirage Autonomic amplifiers (focus on MMS first)
- Web browser-based control fallback
- Playback control (seek)

## 3. External Constraints
### Autonomic
- Use the documented IP/TCP control protocol (same protocol used by Crestron, Control4, URC, and the TuneBridge app)
- Support current eSeries firmware (Mirage OS 7.x+ where possible)
- Rely on services and accounts already configured in the MMS web interface
- TuneBridge functionality must be accessible where the server exposes it

### Networking
- Direct TCP/IP connection to the MMS IP address (default port is usually 5001 or as documented)
- No dependency on Crestron Home, Control4, or any other control system

## 4. High-Level Architecture
- Standalone Python package named `autonomic-cli`
- Core client module that speaks the Autonomic IP protocol
- CLI built with argparse (per AGENTS.md default)
- Shared configuration and structured output utilities
- Clear separation between protocol client, business logic, and CLI layer

## 6. Functional Requirements
```yaml
- id: FR1
  name: Server Connect
  command: autonomic-cli connect
  description: connects to available Mirage servers
- id: FR2
  name: Output List
  command: autonomic-cli player
  description: Shows all outputs with current status
- id: FR3
  name: Now Playing Status
  command: autonomic-cli status
  description: Rich now-playing info (track, artist, album, service, art URL only)
- id: FR4
  name: Playback Controls
  commands: 
    - autonomic-cli play
    - autonomic-cli pause
    - autonomic-cli stop
    - autonomic-cli next
    - autonomic-cli previous
  description: Controls playback on selected or default zone
- id: FR5
  name: Browse & Search
  commands:
    - autonomic-cli  search <query>
    - autonomic-cli  browse artists
    - autonomic-cli  browse albums
  description: Global search and basic category browsing (TuneBridge style)
- id: FR6
  name: Favorites
  commands:
    - autonomic-cli favorites
    - autonomic-cli  play favorite <id>
  description: List and recall favorites/presets
- id: FR7
  name: Structured Output
  flags: --json and --yaml on all commands
  description: Clean, stable contract per AGENTS.md
- id: FR8
  name: Configuration
  description: IP address, port, default zone via env vars or flags
```

## 7. Non-Functional Requirements
```yaml
- CLI framework: argparse (per AGENTS.md)
- Output: Human-readable tables by default; structured only when --json/--yaml used
- Configuration precedence: CLI flags > environment variables > .env file
- Error handling: Clear stderr messages, proper exit codes (0 success, 1 error, 2 usage)
- Logging: stdout for command output, stderr for diagnostics
- Security: Never log credentials or full protocol payloads; sanitize artifacts
- Dependencies: Keep minimal (requests or asyncio TCP client, rich for tables, pyyaml, python-dotenv)
- Extensibility: Easy to add new commands or support additional Autonomic models
```

## 8. Operating Environment & Execution
```yaml
entrypoint:
  type: direct_script
  filename: autonomic-cli.py
  description: |
    Top-level script that is directly executed by OpenClaw bash wrappers.
    It must handle sys.argv correctly and launch the CLI. (no PYTHONPATH required)
  example_path: ~/.openclaw/tools/autonomic/autonomic-cli.py

Configuration:
  AUTONOMIC_HOST: IP address of the Mirage server
  AUTONOMIC_PORT: TCP port (default from docs)
  AUTONOMIC_DEFAULT_ZONE: Optional default zone ID/name

Package:
- target: new dedicated repository or package.
- installation: via pip / conda for easy use in OpenClaw environments
- python_version: 3.11+

File Placement:
  target location: `~/.openclaw/tools/autonomic`
  environment variables:
    local development: `.env` in the project directory
    committed example: `.env.example`
    production: launchd or external environment injection
  recommended package layout:
  tree: |
    autonomic/
    ├── AGENTS.md
    ├── README.md
    ├── REQUIREMENTS.md
    ├── .env
    ├── .env.example
    ├── .gitignore
    ├── pyproject.toml
    ├── autonomic-cli.py
    ├── autonomic-cli/
    │   ├── __init__.py
    │   ├── __main__.py
    │   ├── config.py
    │   ├── main.py
    │   ├── clients.py
    │   ├── models.py
    │   └── utils.py
    └── tests/
        ├── test_clients.py
        ├── test_commands.py
        └── test_outputs.py
```

## 9. Networking / Protocol Assumptions:
```yaml
  protocol: autonomic_mirage_mms
  transport:
    type: tcp
    host: AUTONOMIC_HOST
    port: 5004
    timeout_seconds: 5
    keepalive: true
  encoding:
    charset: ascii
    line_termination: "\r\n"
  connection:
    mode: persistent   # preferred; supports subscriptions/events
    retry:
      enabled: true
      backoff_seconds: 2
      max_attempts: 5
  message_format:
    type: line_delimited
    request:
      format: "<COMMAND> [ARGS...]\\r\\n"
    response:
      format: "<LINE>\\r\\n"
      multi_line: true
  responses:
    examples:
      - "ReportState <zone> <state> ..."
      - "OK"
      - "Error <code> <message>"
  notes:
    - Plain TCP socket (telnet-style)
    - No authentication in basic mode
    - Commands and responses are case-sensitive
    - CRLF required for all commands
```

## 10. Suggested Internal Message Shape
```yaml
fields:
  success: boolean
  message: human readable string
  error: short description when failed
  data: primary payload
rules:
  - treat as api contract
  - avoid silent changes
  - update docs and tests when changed
```

## 11. Error Handling Requirements
```yaml
error_handling:
  exit_codes:
    success: 0
    failure: 1

  connection:
    on_failure: graceful
    on_timeout: graceful
    unreachable_message: "Mirage server is unreachable or not configured"
    retry:
      enabled: true
      strategy:
        type: fixed_backoff
        interval_seconds: 2
        max_attempts: 5

  protocol:
    invalid_response:
      action: log_and_continue
    malformed_message:
      action: log_and_ignore

  logging:
    errors:
      stream: stderr
      include_suggestion: true
    verbose:
      flag: "-v"
      include_protocol_details: true
      include_raw_messages: true
    mapping:
      autonomic_error_codes: true
```

## 12. Implementation Preferences
- **MUST** use project's conda openclaw environment
    - new packages installed in to this environment
    - Python 3.11+
- use argparse for CLI
- provide top-level `autonomic-cli.py` entrypoint
- keep runtime dependencies minimal
- run syntax checks + pytest before committing

## 13. Testing Requirements
```yaml
Unit Tests:
  - command parsing
  - help text
  - ouptut formatting
  - tCP responses
  - data model serialization

Integration Tests:
  - smoke tests for core commands (connect, status, play/pause)
  - end-to-end happy path against a real or mocked Mirage server
```

## 14. Acceptance Criteria
### MVP
- all commands in section 6 work against a real Autonomic Mirage Media Server
- help text is complete and accurate (`autonomic -h`, `autonomic status -h`, etc.)
- `--json` output follows the stable contract
- no secrets committed
- tests pass and cover new functionality
- tool can be called cleanly from OpenClaw agents


## 15. Future Enhancements
- full queue management
- zone grouping and linking
- advanced TuneBridge features (mixed playlists, instant album queuing)
- server discovery
- local library upload/sync helpers
- support for Advanced Music Bridge (AMB) features
- webSocket feedback for real-time updates
- Playback control (seek)


## 16. Design Principle
### Follow AGENTS.md fully:
- simplicity first
- clarity and consistency over cleverness
- optimize for both humans (readable tables) and automation agents (stable JSON)
- explicit over implicit
- keep all Autonomic-specific behavior in this REQUIREMENTS.md



