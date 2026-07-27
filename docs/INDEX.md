# Documentation Index

## Getting Started

| Doc | Purpose |
| --- | --- |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup |
| [SETUP.md](SETUP.md) | Full setup for GitHub and GitLab |
| [FEATURES.md](FEATURES.md) | Feature list, language/linter matrix, config reference |

## Technical Reference

| Doc | Purpose |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module descriptions, pipeline diagram, extension guide |
| [FLOW.md](FLOW.md) | Mermaid flow diagrams for each pipeline phase |
| [PROMPT.md](PROMPT.md) | Full prompt structure sent to the AI model |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project overview, key decisions, version history |

## Contributing

| Doc | Purpose |
| --- | --- |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, coding guidelines, how to add languages |
| [MIGRATION.md](MIGRATION.md) | Migrating from the old monolithic `ai_reviewer.py` |
| [PRD.md](PRD.md) | Original product requirements |

## Source Layout

```text
src/
├── core/          config · cache · reviewer (orchestrator)
├── adapters/      base interfaces · github · gitlab · openrouter
├── analyzers/     language_detector · context_builder
├── tools/         base · registry · linter · file_reader · git_history
├── verification/  verifier (DoubleCheckVerifier)
└── utils/         file_utils · timer

main_gitlab.py     GitLab CI entry point
main_github.py     GitHub Actions entry point
```

## Common Tasks

**Add a new platform** → implement `PlatformAdapter` in `src/adapters/`, see [ARCHITECTURE.md](ARCHITECTURE.md#extending-the-system)

**Add a new linter** → update `LinterTool.LINTER_COMMANDS` in `src/tools/linter.py`, see [ARCHITECTURE.md](ARCHITECTURE.md#add-a-new-language-to-the-linter)

**Understand the pipeline** → [FLOW.md](FLOW.md)

**Configure exclusions / model / cache** → [FEATURES.md](FEATURES.md#configuration)
