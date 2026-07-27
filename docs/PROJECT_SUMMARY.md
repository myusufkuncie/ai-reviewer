# Project Summary

## What It Is

AI Code Reviewer is a multi-platform automated code review tool. It integrates with GitHub Actions and GitLab CI to post inline comments on PRs/MRs, powered by any LLM available via OpenRouter.

## Status

- Platform: GitHub Actions + GitLab CI
- Languages: Python, JS/TS, Dart/Flutter, Go, Rust, Java, PHP
- AI Provider: OpenRouter (any hosted model)
- Pipeline: linter-first → batch AI → 2-pass verification → explainer

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

## Documentation Index

| Doc | Purpose |
| --- | --- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Module descriptions, pipeline diagram, extension guide |
| [FLOW.md](FLOW.md) | Mermaid flow diagrams for each pipeline phase |
| [FEATURES.md](FEATURES.md) | Feature list, language/linter matrix, config reference |
| [QUICKSTART.md](QUICKSTART.md) | 5-minute setup |
| [SETUP.md](SETUP.md) | Full setup for GitHub and GitLab |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Dev setup, coding guidelines, how to add languages |
| [MIGRATION.md](MIGRATION.md) | Migrating from the old monolithic `ai_reviewer.py` |

## Key Design Decisions

- **Single batch AI call per PR** — all pending files in one prompt. No per-file loops.
- **Linter runs before AI** — static findings are embedded in the prompt context, reducing false positives.
- **Verification is additive** — never removes comments, only tags them with linter evidence.
- **Cache is per-file** — a changed file doesn't invalidate cached results for unchanged files.
- **Provider is swappable** — implement `AIProviderAdapter` to add Anthropic, OpenAI, or any other backend.

## Dependencies

```text
requests>=2.31.0
python-gitlab>=4.4.0
PyGithub>=2.1.1
```

Linters (pylint, eslint, dart, golangci-lint, cargo, checkstyle, phpcs) must be pre-installed in the CI environment. Missing linters are skipped without failing the review.

## Version History

- **v3** (2026-02-06): Modular refactor, GitHub support added
- **v6-linter-first** (2026-07-27): Linter-first batch pipeline, 2-pass verification, explainer output
