# Contributing

Thank you for considering contributing! Follow these guidelines to facilitate reviews:

- Use Python 3.9+ and follow PEP 8.
- Run `ruff`, `black`, and `pytest` before opening a PR.
- Include tests for new features and fixes.
- Clearly explain the motivation, approach, and impacts of the change.

## Development environment

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -e .[dev]
pytest
```

## Workflow
- Open an issue to discuss major changes.
- Use small, focused PRs with objective descriptions.
- Keep the history clean (rebase preferred).

