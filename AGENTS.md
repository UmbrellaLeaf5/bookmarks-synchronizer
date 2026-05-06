# AGENTS.md

## Project

`bookmarks-manager` syncs Chrome bookmarks across multiple profiles. Exported
HTML files live in `bookmarks/`, configured in `config.json`. Dev dependency: pytest.

## Commands

```bash
uv sync                        # install dev deps (pytest)
uv run main.py                 # run the tool interactively

# Verification pipeline (run in order):
ruff check .                   # lint
ruff format --check .          # format check
pyright .                      # type-check src/ and main.py
python -m pytest tests/ -v     # 38 tests

# Fix formatting:
ruff check --fix . && ruff format .
```

## Code style

### Blank lines before control flow

Insert a **blank line before** every `if`, `else`, `try`, `except`, `for`,
`while`, `raise`, `with`, `finally`, `assert`, `return`, `continue` that sits at the indentation margin of its containing
block. Deeply nested one-line conditionals (e.g. inside a tight loop) may omit
the blank line.

```python
# Yes:
  result = compute()

  if result is None:
    return

  for item in items:
    process(item)

# No:
  result = compute()
  if result is None:
    return
  for item in items:
    process(item)
```

### Indentation and layout

- **2-space indentation** everywhere (ruff `indent-width = 2`)
- **Line length**: 90 characters
- **2 blank lines** between top-level definitions (classes, functions) —
  enforced by ruff `lines-after-imports = 2`
- `from __future__ import annotations` is the first line in every `.py` file,
  followed by a blank line, then standard library imports, then project imports
- Long function signatures and calls are broken with **hanging indentation**:

```python
def func(
  self,
  arg1: str,
  arg2: int,
) -> ReturnType:
  ...
```

### Exports

- `src/models/__init__.py` uses `__all__` to declare public re-exports.
  No `import X as X` or `# noqa` — ruff respects `__all__`.

### Type annotations

- All functions have return type annotations
- `from __future__ import annotations` everywhere (PEP 563)
- pyright in `basic` mode, checks `src/` and `main.py` only

## Data model quirks

- **URL is the primary key** for bookmark identity — two bookmarks with the
  same HREF are considered the same bookmark regardless of title
- **`__folder__:NAME`** is a sentinel URL prefix in `ConflictItem.url` and
  `UserDecision.url` used to distinguish folder-level conflicts from bookmark
  conflicts. Use `is_folder_url()` / `folder_name_from_url()` from `utils.py`.
- **`folder_path` is `list[str]`**, not a string — folder names may contain
  `/` (e.g. `"Info/program"` is a single folder name)
- `SyncAction` is a `str, Enum` with values `"add"`, `"remove"`, `"skip"`,
  `"exit"` — never compare to raw strings

## Gotchas

- **`copy.deepcopy` is used for folder cloning** — use `FolderNode.deep_copy()`
  or `Syncer._deep_copy_child()`
- **Backup files** go to `bookmarks/backups/` (gitignored), named with
  timestamp: `{stem}_YYYYMMDD_HHMMSS.html`
- **The writer performs a backup before every write** — the first run on a new
  file creates no backup, subsequent runs create one
