# EverBrain

**Persistent workflow continuity for AI-assisted software development.**

EverBrain preserves your development context across AI sessions, agent switches, and IDE restarts.

## Phase 1: Foundation

This is the initial phase focusing on local-first SQLite storage, CLI scaffolding, and structured project memory.

## Quick Start

```bash
# Install in development mode
pip install -e ".[dev]"

# Initialize EverBrain in your project
eb init

# (Coming in Phase 2: eb start, eb status, eb summary, etc.)
```

## Project Structure

```
src/everbrain/
├── cli/          # Typer CLI command groups
├── core/         # Business logic and state management
├── models/       # Pydantic schemas and validation
├── storage/      # SQLite database layer
├── git/          # Git integration
└── utils/        # Console, I/O, helpers
```

## Documentation

- [Architecture Overview](docs/ARCHITECTURE.md) (Coming soon)
- [Development Guide](docs/DEVELOPMENT.md) (Coming soon)

## Status

**Phase 1 Progress:**
- [x] Project scaffolding
- [x] Database foundation (SQLite)
- [x] Configuration models (Pydantic)
- [x] eb init command
- [x] Session/task tracking
- [x] Handoff generation (Phase 2+)
- [x] Git integration (Phase 2+)
