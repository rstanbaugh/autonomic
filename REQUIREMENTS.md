# Autonomic Mirage Media Server cli - Requirements Document

## 1. Purpose
```yaml
project:
  name: autonomic-cli
  description: a python command-line interface to control an autonomic mirage media server
  purpose: |
    build a standalone Python command-line tool that allows user to control Mirage Media Server outputs for desktop/scripting use and OpenClaw agents

usage_contexts:
  - standalone terminal tool for direct human use (after installation or symlink)
  - executed as a tool/skill by OpenClaw agents via bash wrapper:
    exec "$PY" "$TOOL" "$@"
    where TOOL points to autonomic-cli.py
  - simple to run standalone / easy to call as a tool from OpenClaw agents via structured output

metadata:
  spec_date: 2026-03-28
  target_environment: Python in conda env named `openclaw`
```

## 2. Scope
### In Scope (MVP)
- direct IP control of autonomic mirage media server (mms-1e/3e/5e and compatible eSeries)
- playback control (play, pause, stop, next, previous)
- output discovery and selection (Player A, Player B, etc)
- now-playing status with metadata and album art url
- favorites and presets recall
- human-readable tables by default
- structured output (--json, --yaml) for automation
- simple configuration via environment variables or .env

### Out of Scope (MVP)
- browse and search
- zone discovery and selection
- volume and mute per zone
- scene/snapshot recall (if exposed in API)
- full graphical UI (this is cli only)
- in-app account login flows for streaming services (assume pre-configured on the mms)
- advanced queue editing (reorder, delete items)
- zone grouping / party mode (future)
- video/OSD control
- any functionality requiring amplifier/zone mapping or MAS control system integration
- any networking beyond the mms control socket (e.g., HTTP APIs, UDP multicast, or control system bridges)
- web browser-based control fallback
- playback control (seek)

## 3. External Constraints
### Autonomic
- control is performed via the mms IP control protocol over tcp
- support current eSeries firmware (Mirage OS 7.x+ where possible)
- rely on services and accounts already configured in the mms web interface
- tuneBridge functionality must be accessible where the server exposes it
- Primary protocol reference (tcp socket commands, connection sequence, player control):
  [Autonomic Media Server Control Protocol](https://autonomic.atlassian.net/wiki/spaces/ASKB/pages/1509556225/Autonomic+Media+Server+Control+Protocol) 

### Networking
- no dependency on Crestron Home, Control4, or any other control system

## 4. High-Level Architecture
- cli → tcp socket → mms → player 
- standalone Python package named `autonomic-cli` launched from bash wrapper
- core client module that speaks the autonomic IP protocol
- cli built with argparse (per AGENTS.md guidelines)
- shared configuration and structured output utilities
- clear separation between protocol client, business logic, and cli layer

## 6. Functional Requirements
```yaml
- conventions:
    < ... >: required argument
    [ ... ]: optional argument

- id: FR1
  name: player List
  command: autonomic-cli <player> [list]
  description: list players and current status
  [player]:
    with player-name: only player-name details are shown
    without player-name: information for all available players is shown
  output:
    - name: Name of the output stream / player
    - description: Name of the streaming service or library currently active
    - status: Current playback status of the player
  return:
    exit_code: success | failure

- id: FR2
  name: now playing status
  command: autonomic-cli [player] <status>
  description: status of media currently playing
  [player]:
    with player-name: only player-name details are shown
    without player-name: information for all available players is shown
  output:
    track: song name
    artist: artist name
    album: album name
    art: art URL only or blank
    service: streaming service or local library name
  return:
    exit_code: success | failure

- id: FR3
  name: playback controls
  command: autonomic-cli <player> <action> [favorites]
  description: Controls playback on a specific player
  valid actions: 
    play: resume playback of current queue
    pause: pause playback of the player
    toggle: will toggle player state between play and pause
    stop: stop playback on the player
    next: skip to next item in current queue
    previous: skip to previous item in queue
    thumbsup: toggles the ThumbsUp state between 0 and 1
    thumbsdown: toggles the ThumbsDown state between 0 and 1; some service skip to next track
  favorites: optional argument for <item-id> to play favorites
  output:
    message: confirmation or error text
  return:
    exit_code: success | failure

- id: FR4
  name: list favorites
  commands: autonomic-cli favorites
  description: list favorites and presets
  output:
    <item-id>:
    track: song name
    artist: artist name
    album: album name
    art: art URL only or blank
    service: streaming service or local library name
  return:
    exit_code: success | failure
    
- id: FR5
  name: Structured Output
  flags: --json and --yaml on all commands
  description: clean, stable contract per AGENTS.md

- id: FR6
  name: configuration
  description: mirage server configuration information
  output:
    ip address:
    port:

  return:
    exit_code: success | failure
```

## 7. Non-Functional Requirements
```yaml
- cli framework: argparse (per AGENTS.md)
- output: Human-readable tables by default; structured only when --json/--yaml used
- configuration precedence: cli flags > environment variables > .env file
- error handling: Clear stderr messages, proper exit codes (0 success, 1 error, 2 usage)
- logging: stdout for command output, stderr for diagnostics
- security: Never log credentials or full protocol payloads; sanitize artifacts
- dependencies: Keep minimal (socket or asyncio tcp client, rich, pyyaml, python-dotenv)
- extensibility: Easy to add new commands or support additional Autonomic models
```

## 8. Operating Environment & Execution
```yaml
entrypoint:
  type: direct_script
  filename: autonomic-cli.py
  description: |
    top-level script that is directly executed by OpenClaw bash wrappers.
    must handle sys.argv correctly and launch the cli. (no PYTHONPATH required)
  example_path: ~/.openclaw/tools/autonomic/autonomic-cli.py

configuration:
  AUTONOMIC_HOST: ip address of the mirage server
  AUTONOMIC_PORT: tcp port (default from docs)
  AUTONOMIC_DEFAULT_PLAYER: Optional default mirage player

package:
- target: new dedicated repository or package.
- installation: via pip / conda for easy use in OpenClaw environments
- python_version: 3.11+

file placement:
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
      - "ReportState <player> <state> ..."
      - "OK"
      - "Error <code> <message>"
  notes:
    - Plain tcp socket (telnet-style)
    - No authentication in basic mode
    - CLI commands are case-insensitive
    - MMS protocol commands should be sent using documented casing
    - CRLF required for all commands
```

## 10. Command Flow
```yaml
- Typical command flow includes:
  - SetClientType
  - SetClientVersion
  - SetEncoding 65001
  - SetInstance <player>
  - SubscribeEvents
  - GetStatus
```

## 11. Suggested Internal Message Shape
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

## 12. Error Handling Requirements
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

## 13. Implementation Preferences
- **MUST** use project's conda openclaw environment
    - new packages installed in to this environment
    - Python 3.11+
- use argparse for cli
- provide top-level `autonomic-cli.py` entrypoint
- keep runtime dependencies minimal
- run syntax checks + pytest before committing

## 14. Testing Requirements
```yaml
unit tests:
  - command parsing
  - help text
  - output formatting
  - tcp responses
  - data model serialization

integration tests:
  - smoke tests for core commands (status, play/pause)
  - end-to-end happy path against a real or mocked Mirage server
```

## 15. Acceptance Criteria
### MVP
- all commands in section 6 work against a real Autonomic Mirage Media Server
- help text is complete and accurate (`autonomic -h`, `autonomic status -h`, etc.)
- `--json` output follows the stable contract
- no secrets committed
- tests pass and cover new functionality
- tool can be called cleanly from OpenClaw agents


## 16. Future Enhancements
- full queue management
- zone grouping and linking
- advanced TuneBridge features (mixed playlists, instant album queuing)
- server discovery
- local library upload/sync helpers
- support for Advanced Music Bridge (AMB) features
- webSocket feedback for real-time updates
- Playback control (seek)


## 17. Design Principle
### Follow AGENTS.md fully:
- simplicity first
- clarity and consistency over cleverness
- optimize for both humans (readable tables) and automation agents (stable JSON)
- explicit over implicit
- keep all Autonomic-specific behavior in this REQUIREMENTS.md



