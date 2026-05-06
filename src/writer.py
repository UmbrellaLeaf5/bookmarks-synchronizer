from __future__ import annotations

import os
import shutil
import time
from datetime import datetime
from pathlib import Path

from src.models import BookmarkItem, FolderNode


BACKUP_DIR = Path("bookmarks") / "backups"


def backup_file(filepath: str) -> str:
  if not os.path.exists(filepath):
    return ""
  BACKUP_DIR.mkdir(parents=True, exist_ok=True)
  stem = Path(filepath).stem
  ts = datetime.fromtimestamp(os.path.getmtime(filepath)).strftime("%Y%m%d_%H%M%S")
  backup_path = str(BACKUP_DIR / f"{stem}_{ts}.html")
  shutil.copy2(filepath, backup_path)
  return backup_path


def write_bookmark_file(root: FolderNode, filepath: str) -> str:
  """Write bookmark file. Returns the backup path if one was created, else ''."""
  bak = backup_file(filepath)

  lines: list[str] = [
    "<!DOCTYPE NETSCAPE-Bookmark-file-1>",
    "<!-- This is an automatically generated file.",
    "     It will be read and overwritten.",
    "     DO NOT EDIT! -->",
    '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
    "<TITLE>Bookmarks</TITLE>",
    "<H1>Bookmarks</H1>",
    "<DL><p>",
  ]

  bar_add_date = root.add_date or 0
  timestamps = []
  for child in root.children:
    if isinstance(child, FolderNode):
      timestamps.append(child.last_modified)
    elif isinstance(child, BookmarkItem):
      timestamps.append(child.add_date)
  bar_last_mod = max(timestamps) if timestamps else 0

  lines.append(
    f'    <DT><H3 ADD_DATE="{bar_add_date}"'
    f' LAST_MODIFIED="{bar_last_mod}"'
    f' PERSONAL_TOOLBAR_FOLDER="true">{root.name}</H3>'
  )
  lines.append("    <DL><p>")
  for child in root.children:
    _write_entry(child, lines, indent=8)
  lines.append("    </DL><p>")
  lines.append("</DL><p>")

  with open(filepath, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

  return bak


def _write_entry(entry: FolderNode | BookmarkItem, lines: list[str], indent: int) -> None:
  prefix = " " * indent
  if isinstance(entry, FolderNode):
    lines.append(
      f'{prefix}<DT><H3 ADD_DATE="{entry.add_date}"'
      f' LAST_MODIFIED="{entry.last_modified}">{_escape_html(entry.name)}</H3>'
    )
    lines.append(f"{prefix}<DL><p>")
    for child in entry.children:
      _write_entry(child, lines, indent + 4)
    lines.append(f"{prefix}</DL><p>")
  elif isinstance(entry, BookmarkItem):
    icon_attr = f' ICON="{entry.icon}"' if entry.icon else ""
    lines.append(
      f'{prefix}<DT><A HREF="{entry.url}"'
      f' ADD_DATE="{entry.add_date}"{icon_attr}>{_escape_html(entry.title)}</A>'
    )


def _escape_html(text: str) -> str:
  return (
    text.replace("&", "&amp;")
    .replace("<", "&lt;")
    .replace(">", "&gt;")
    .replace('"', "&quot;")
  )


def now_timestamp() -> int:
  return int(time.time())


def format_timestamp(ts: int) -> str:
  return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")
