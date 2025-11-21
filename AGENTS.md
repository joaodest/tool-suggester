# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/suggester/` (core in `engine.py`, `trie.py`, `tokenizer.py`, `ranking.py`, adapters em `adapters/`).
- Schemas e tipos: `src/suggester/schemas.py`.
- Testes: `tests/` (arquivos `test_*.py`).
- Documentação: `docs/` (planejamento em `docs/planning_tasks.md`).
- Metadados: `pyproject.toml`, `README.md`, `CHANGELOG.md`.

## Build, Test, and Development Commands
- Instalação dev: `pip install -e .[dev]`
- Testes: `pytest`
- Lint: `ruff check .`
- Formatação: `black .`
- Tipagem (opcional): `mypy src`
Exemplo rápido (REPL):
```py
from suggester.engine import SuggestionEngine
eng = SuggestionEngine([{"name":"export_csv","description":"Exporta CSV","keywords":["csv","exportar"]}])
eng.submit("exportar para csv", session_id="s1")
```

## Coding Style & Naming Conventions
- PEP 8, indentação de 4 espaços, largura 100 colunas.
- `black` e `ruff` são a fonte da verdade de estilo.
- Nomes: módulos/variáveis `snake_case`, classes `CamelCase`, constantes `UPPER_SNAKE`.
- Prefira type hints; docstrings concisas (one‑liner quando possível).

## Testing Guidelines
- Use `pytest`. Nomeie testes como `tests/test_<módulo>.py` e funções `test_*`.
- Foque em unidades: tokenização, trie, ranking e engine.
- Adicione testes ao corrigir bugs e atualizar APIs.

## Commit & Pull Request Guidelines
- Siga Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`.
- Mensagem curta (<=72 chars) + corpo explicando motivação e abordagem.
- PRs devem: linkar issues, incluir testes, atualizar docs/README quando necessário e entry no `CHANGELOG.md`.
- Rode `ruff`, `black`, `pytest` antes de abrir o PR.

## Security & Configuration Tips
- Não logue PII; mantenha logs concisos. Veja `SECURITY.md`.
- Re‑ranking por LLM é opt‑in (quando implementado). Evite enviar dados externos por padrão.

## Agent-Specific Notes
- Respeite esta AGENTS.md ao editar arquivos. Mantenha mudanças focadas, com referências explícitas a caminhos (ex.: `src/suggester/engine.py:1`).
