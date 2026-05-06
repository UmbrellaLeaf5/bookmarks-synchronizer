from __future__ import annotations

import time
from dataclasses import dataclass, field

from src.models import BookmarkItem, FolderNode


@dataclass
class ConflictItem:
  url: str
  title: str
  present_in: list[str]
  missing_from: list[str]
  add_date: int
  folder_path: str


@dataclass
class UserDecision:
  url: str
  title: str
  add_date: int
  folder_path: str
  action: str
  target_profiles: list[str]


@dataclass
class SyncReport:
  conflicts: list[ConflictItem] = field(default_factory=list)
  decisions: list[UserDecision] = field(default_factory=list)
  changes_made: int = 0


def find_folder(root: FolderNode, name: str) -> FolderNode | None:
  for child in root.children:
    if isinstance(child, FolderNode) and child.name == name:
      return child
  return None


def count_bookmarks(node: FolderNode) -> int:
  count = 0
  for child in node.children:
    if isinstance(child, BookmarkItem):
      count += 1
    elif isinstance(child, FolderNode):
      count += count_bookmarks(child)
  return count


def collect_conflicts(
  folder_maps: dict[str, FolderNode | None],
  path: str,
) -> list[ConflictItem]:
  conflicts: list[ConflictItem] = []
  all_profiles = list(folder_maps.keys())
  present_profiles = {p for p, f in folder_maps.items() if f is not None}

  if not present_profiles:
    return conflicts

  # Bookmark conflicts at this level
  url_presence: dict[str, dict[str, BookmarkItem]] = {}
  for pname in present_profiles:
    folder = folder_maps[pname]
    assert folder is not None
    for child in folder.children:
      if isinstance(child, BookmarkItem):
        url_presence.setdefault(child.url, {})[pname] = child

  for url, presences in url_presence.items():
    present = sorted(presences.keys())
    if set(present) == set(all_profiles):
      continue
    missing = sorted(p for p in all_profiles if p not in presences)
    best = max(presences.values(), key=lambda b: b.add_date)
    conflicts.append(
      ConflictItem(
        url=url,
        title=best.title,
        present_in=present,
        missing_from=missing,
        add_date=best.add_date,
        folder_path=path,
      )
    )

  # Folder-level conflicts
  subfolder_names: set[str] = set()
  for pname in present_profiles:
    folder = folder_maps[pname]
    assert folder is not None
    for child in folder.children:
      if isinstance(child, FolderNode):
        subfolder_names.add(child.name)

  for sf_name in sorted(subfolder_names):
    sf_maps: dict[str, FolderNode | None] = {}
    for pname in all_profiles:
      if pname in present_profiles:
        folder = folder_maps[pname]
        assert folder is not None
        found = next(
          (c for c in folder.children if isinstance(c, FolderNode) and c.name == sf_name),
          None,
        )
        sf_maps[pname] = found
      else:
        sf_maps[pname] = None

    present_sf = sorted(p for p, f in sf_maps.items() if f is not None)
    missing_sf = sorted(p for p, f in sf_maps.items() if f is None)

    if missing_sf:
      conflicts.append(
        ConflictItem(
          url=f"__folder__:{sf_name}",
          title=f"[Папка] {sf_name}",
          present_in=present_sf,
          missing_from=missing_sf,
          add_date=0,
          folder_path=path,
        )
      )

    filtered = ((p, f) for p, f in sf_maps.items() if f is not None)
    existing_maps: dict[str, FolderNode | None] = dict(filtered)
    if existing_maps:
      conflicts.extend(collect_conflicts(existing_maps, f"{path}/{sf_name}"))

  return conflicts


def apply_decisions(
  shared_root_maps: dict[str, FolderNode | None],
  decisions: list[UserDecision],
) -> None:
  for d in decisions:
    if d.action == "skip":
      continue

    path_parts = d.folder_path.split("/")
    navigate_parts = path_parts[1:] if len(path_parts) > 1 else []

    for profile_name in d.target_profiles:
      if profile_name not in shared_root_maps:
        continue

      folder = shared_root_maps[profile_name]
      if folder is None:
        continue

      # Navigate to the target subfolder
      target = folder
      for part in navigate_parts:
        found = next(
          (c for c in target.children if isinstance(c, FolderNode) and c.name == part),
          None,
        )
        if found is None:
          break
        target = found
      else:
        _apply_change(target, d)


def _apply_change(folder: FolderNode, decision: UserDecision) -> None:
  if decision.action == "add":
    if decision.url.startswith("__folder__"):
      fname = decision.url.split(":", 1)[1]
      has_folder = any(
        isinstance(c, FolderNode) and c.name == fname for c in folder.children
      )
      if not has_folder:
        folder.children.append(
          FolderNode(
            name=fname,
            add_date=now_ts(),
            last_modified=now_ts(),
            children=[],
          )
        )
        folder.last_modified = now_ts()
    elif not any(
      isinstance(c, BookmarkItem) and c.url == decision.url for c in folder.children
    ):
      folder.children.append(
        BookmarkItem(
          title=decision.title,
          url=decision.url,
          add_date=decision.add_date or now_ts(),
        )
      )
      folder.last_modified = now_ts()

  elif decision.action == "remove":
    if decision.url.startswith("__folder__"):
      fname = decision.url.split(":", 1)[1]
      folder.children = [
        c for c in folder.children if not (isinstance(c, FolderNode) and c.name == fname)
      ]
    else:
      folder.children = [
        c
        for c in folder.children
        if not (isinstance(c, BookmarkItem) and c.url == decision.url)
      ]
    folder.last_modified = now_ts()


def now_ts() -> int:
  return int(time.time())
