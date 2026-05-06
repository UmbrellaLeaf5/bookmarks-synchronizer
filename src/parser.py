from __future__ import annotations

import re

from src.models import BookmarkItem, FolderNode


_H3_RE = re.compile(
  r'<DT><H3\s+ADD_DATE="(\d+)"\s+LAST_MODIFIED="(\d+)"(?:\s+PERSONAL_TOOLBAR_FOLDER="true")?>(.+?)</H3>'
)
_A_RE = re.compile(
  r'<DT><A\s+HREF="(.*?)"\s+ADD_DATE="(\d+)"(?:\s+ICON="(.*?)")?>(.*?)</A>'
)


def parse_bookmark_file(filepath: str) -> FolderNode:
  with open(filepath, encoding="utf-8") as f:
    lines = f.readlines()

  # Find the Bookmarks bar H3
  for i, line in enumerate(lines):
    m = _H3_RE.search(line)
    if m and "PERSONAL_TOOLBAR_FOLDER" in line:
      bar_name = _unescape(m.group(3).strip()) or "Bookmarks bar"
      bar_add_date = int(m.group(1))
      bar_last_mod = int(m.group(2))

      # Find the content DL after this H3
      children, _ = _parse_children(lines, i + 1)

      return FolderNode(
        name=bar_name,
        add_date=bar_add_date,
        last_modified=bar_last_mod,
        children=children,
      )

  raise ValueError("Invalid bookmark file: no Bookmarks bar found")


def _parse_children(lines: list[str], start: int) -> tuple[list, int]:
  entries: list[FolderNode | BookmarkItem] = []
  i = start

  while i < len(lines):
    line = lines[i].strip()

    # End of current DL block
    if line.startswith("</DL>"):
      return entries, i

    # <DL><p> starts a children block - skip into it
    if line.startswith("<DL>"):
      i += 1
      continue

    # Folder entry
    m = _H3_RE.search(line)
    if m:
      name = _unescape(m.group(3).strip())
      add_date = int(m.group(1))
      last_modified = int(m.group(2))

      # Find the following DL with children
      children: list[FolderNode | BookmarkItem] = []
      j = i + 1
      while j < len(lines):
        if "<DL>" in lines[j]:
          children, j = _parse_children(lines, j + 1)
          break
        j += 1
      else:
        j = i + 1

      entries.append(
        FolderNode(
          name=name,
          add_date=add_date,
          last_modified=last_modified,
          children=children,
        )
      )
      i = j + 1
      continue

    # Bookmark entry
    m2 = _A_RE.search(line)
    if m2:
      url = m2.group(1)
      add_date = int(m2.group(2))
      icon = m2.group(3)
      title = _unescape(m2.group(4).strip())

      entries.append(
        BookmarkItem(
          title=title,
          url=url,
          add_date=add_date,
          icon=icon,
        )
      )

    i += 1

  return entries, len(lines)


def _unescape(text: str) -> str:
  return (
    text.replace("&amp;", "&")
    .replace("&lt;", "<")
    .replace("&gt;", ">")
    .replace("&quot;", '"')
  )
