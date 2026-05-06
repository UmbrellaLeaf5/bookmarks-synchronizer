from __future__ import annotations

import copy

from src.models.sync import ConflictItem, SyncAction, UserDecision
from src.models.tree import BookmarkItem, FolderNode
from src.utils import folder_name_from_url, is_folder_url, now_ts


class Syncer:
  def collect_conflicts(
    self,
    folder_maps: dict[str, FolderNode | None],
    path: list[str],
  ) -> list[ConflictItem]:
    conflicts: list[ConflictItem] = []
    all_profiles = list(folder_maps.keys())
    present_profiles = {p for p, f in folder_maps.items() if f is not None}

    if not present_profiles:
      return conflicts

    # Bookmark conflicts at this level
    url_presence: dict[str, dict[str, BookmarkItem]] = {}

    for pres_name in present_profiles:
      folder = folder_maps[pres_name]
      assert folder is not None

      for child in folder.children:
        if isinstance(child, BookmarkItem):
          url_presence.setdefault(child.url, {})[pres_name] = child

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
          icon=best.icon,
        )
      )

    # Folder-level conflicts
    subfolder_names: set[str] = set()
    for pres_name in present_profiles:
      folder = folder_maps[pres_name]
      assert folder is not None

      for child in folder.children:
        if isinstance(child, FolderNode):
          subfolder_names.add(child.name)

    for sf_name in sorted(subfolder_names):
      sf_maps: dict[str, FolderNode | None] = {}

      for pres_name in all_profiles:
        if pres_name in present_profiles:
          folder = folder_maps[pres_name]
          assert folder is not None

          found = next(
            (
              c
              for c in folder.children
              if isinstance(c, FolderNode) and c.name == sf_name
            ),
            None,
          )

          sf_maps[pres_name] = found

        else:
          sf_maps[pres_name] = None

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
        conflicts.extend(self.collect_conflicts(existing_maps, [*path, sf_name]))

    return conflicts

  def apply_decisions(
    self,
    shared_root_maps: dict[str, FolderNode | None],
    decisions: list[UserDecision],
  ) -> None:
    for d in decisions:
      if d.action in (SyncAction.SKIP, SyncAction.EXIT):
        continue

      navigate_parts = d.folder_path[1:] if len(d.folder_path) > 1 else []

      for profile_name in d.target_profiles:
        folder = shared_root_maps.get(profile_name)

        if folder is None:
          continue

        target = self._navigate_auto_create(
          folder, navigate_parts, shared_root_maps, d.source_profile
        )

        if target is None:
          continue

        if d.action == SyncAction.ADD:
          self._apply_add(target, d, shared_root_maps, d.source_profile, navigate_parts)

        elif d.action == SyncAction.REMOVE:
          self._apply_remove(target, d)

  def _navigate_auto_create(
    self,
    folder: FolderNode,
    navigate_parts: list[str],
    root_maps: dict[str, FolderNode | None],
    source_profile: str | None,
  ) -> FolderNode | None:
    target = folder

    for i, part in enumerate(navigate_parts):
      child = next(
        (c for c in target.children if isinstance(c, FolderNode) and c.name == part),
        None,
      )

      if child is None:
        child = self._deep_copy_child(root_maps, source_profile, navigate_parts[:i], part)

        if child is None:
          return None

        target.children.append(child)
        target.last_modified = now_ts()

      target = child

    return target

  def _deep_copy_child(
    self,
    root_maps: dict[str, FolderNode | None],
    source_profile: str | None,
    parent_parts: list[str],
    child_name: str,
  ) -> FolderNode | None:
    if not source_profile or source_profile not in root_maps:
      return None

    src = root_maps[source_profile]

    if src is None:
      return None

    cur = src

    for part in parent_parts:
      found = next(
        (c for c in cur.children if isinstance(c, FolderNode) and c.name == part),
        None,
      )

      if found is None:
        return None

      cur = found

    child = next(
      (c for c in cur.children if isinstance(c, FolderNode) and c.name == child_name),
      None,
    )

    if child is None:
      return None

    return copy.deepcopy(child)

  def _apply_add(
    self,
    folder: FolderNode,
    decision: UserDecision,
    root_maps: dict[str, FolderNode | None],
    source_profile: str | None,
    parent_parts: list[str],
  ) -> None:
    if is_folder_url(decision.url):
      fname = folder_name_from_url(decision.url)

      if any(isinstance(c, FolderNode) and c.name == fname for c in folder.children):
        return

      source_folder = self._deep_copy_child(
        root_maps, source_profile, parent_parts, fname
      )

      if source_folder is not None:
        folder.children.append(source_folder)

      else:
        folder.children.append(
          FolderNode(name=fname, add_date=now_ts(), last_modified=now_ts(), children=[])
        )

      folder.last_modified = now_ts()

    else:
      has_url = any(
        isinstance(c, BookmarkItem) and c.url == decision.url for c in folder.children
      )

      if has_url:
        return

      folder.children.append(
        BookmarkItem(
          title=decision.title,
          url=decision.url,
          add_date=decision.add_date or now_ts(),
          icon=decision.icon,
        )
      )

      folder.last_modified = now_ts()

  def _apply_remove(self, folder: FolderNode, decision: UserDecision) -> None:
    if is_folder_url(decision.url):
      fname = folder_name_from_url(decision.url)

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
