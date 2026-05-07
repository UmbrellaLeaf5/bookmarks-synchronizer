# Bookmarks Synchronizer

Tool for syncing Chrome bookmarks across multiple profiles.

## Purpose

If you have multiple Chrome profiles (e.g., personal, study, work) - each has
both unique bookmark folders and shared ones (e.g., Tools, Important).
Bookmarks Synchronizer finds discrepancies in shared folders and helps bring them
to a unified up-to-date state - without manual copying.

## How it works

1. Export bookmarks from each Chrome profile to HTML
   (Ctrl+Shift+O → "Export bookmarks") and place files in `bookmarks/`
2. Configure `config.json` - specify file paths and shared folder names
3. Run the script - it finds discrepancies and suggests solutions for each:
   - **a** - add bookmark/folder to all profiles where it's missing
   - **r** - remove bookmark/folder from all profiles
   - **s** - skip (leave as is)
4. The script creates backups of modified files in `bookmarks/backups/`
   (filename: `{original}_YYYYMMDD_HHMMSS.html`)
   and writes updated files

### Logging

All sync operations are logged to `bookmarks/sync.log`
(1 MB rotation). Logging is file-only - terminal stays
clean for interactive interaction.

### Sync features

- Folders listed in `shared_folders` are considered shared - all their contents
  (including nested subfolders) sync recursively
- If a shared folder is missing in a profile - it's created automatically
- When adding a folder, all its bookmarks and subfolders are copied from the source profile
  (deep copy)
- Bookmark icons (favicon) are preserved
- Parent folders are created automatically when needed
- Folder names with slashes are supported (e.g., `Info/program` is a single folder)

## Installation and usage

```bash
uv venv .venv
source .venv/Scripts/activate
uv sync
```

Configure `config.json` for your profiles.

```bash
uv run main.py              # interactive mode
uv run main.py --dry-run    # check without writing changes
```

Dependencies: `loguru` (logging), `pytest` (dev).

## Code verification

```bash
ruff check .
ruff format --check .
pyright .
python -m pytest tests/ -v
```

## Configuration format

```json
{
  "profiles": {
    "pc": "bookmarks/bookmarks_for_pc.html",
    "study": "bookmarks/bookmarks_for_study.html",
    "work": "bookmarks/bookmarks_for_work.html"
  },
  "shared_folders": ["Tools", "Important"]
}
```

- `profiles` - list of profiles with paths to HTML files
- `shared_folders` - names of shared folders (including all nested contents)

## License

Public Domain (Unlicense). See [LICENSE](LICENSE) for details.
