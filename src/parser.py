import re

from src.models.tree import BookmarkItem, FolderNode
from src.utils import unescape_html


class Parser:
  _H3_RE = re.compile(
    r"<DT><H3\s+ADD_DATE=\"(\d+)\"\s+LAST_MODIFIED=\"(\d+)\""
    r"(?:\s+PERSONAL_TOOLBAR_FOLDER=\"true\")?>"
    r"(.+?)</H3>"
  )

  _A_RE = re.compile(
    r"<DT><A\s+HREF=\"(.*?)\"\s+ADD_DATE=\"(\d+)\""
    r"(?:\s+ICON=\"(.*?)\")?"
    r">(.*?)</A>"
  )

  def parse(self, filepath: str) -> FolderNode:
    with open(filepath, encoding="utf-8") as f:
      lines = f.readlines()

    for i, line in enumerate(lines):
      m = self._H3_RE.search(line)

      if m and "PERSONAL_TOOLBAR_FOLDER" in line:
        bar_name = unescape_html(m.group(3).strip()) or "Bookmarks bar"
        bar_add_date = int(m.group(1))
        bar_last_mod = int(m.group(2))
        children, _ = self._parse_children(lines, i + 1)

        return FolderNode(
          name=bar_name,
          add_date=bar_add_date,
          last_modified=bar_last_mod,
          children=children,
        )

    raise ValueError("Invalid bookmark file: no Bookmarks bar found")

  def _parse_children(
    self, lines: list[str], start: int
  ) -> tuple[list[FolderNode | BookmarkItem], int]:
    entries: list[FolderNode | BookmarkItem] = []
    i = start

    while i < len(lines):
      line = lines[i].strip()

      if line.startswith("</DL>"):
        return entries, i

      if line.startswith("<DL>"):
        i += 1
        continue

      m = self._H3_RE.search(line)

      if m:
        name = unescape_html(m.group(3).strip())
        add_date = int(m.group(1))
        last_modified = int(m.group(2))
        children: list[FolderNode | BookmarkItem] = []
        j = i + 1

        while j < len(lines):
          if "<DL>" in lines[j]:
            children, j = self._parse_children(lines, j + 1)
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

      m2 = self._A_RE.search(line)

      if m2:
        url = m2.group(1)
        add_date = int(m2.group(2))
        icon = m2.group(3)
        title = unescape_html(m2.group(4).strip())
        entries.append(BookmarkItem(title=title, url=url, add_date=add_date, icon=icon))

      i += 1

    return entries, len(lines)
