from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BookmarkItem:
  title: str
  url: str
  add_date: int
  icon: str | None = None


@dataclass
class FolderNode:
  name: str
  add_date: int
  last_modified: int
  children: list[FolderNode | BookmarkItem] = field(default_factory=list)


@dataclass
class Profile:
  name: str
  filepath: str
  root: FolderNode | None = None
