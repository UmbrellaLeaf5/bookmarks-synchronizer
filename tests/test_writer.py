from __future__ import annotations

import os
import shutil

from src.models import BookmarkItem, FolderNode
from src.parser import Parser
from src.utils import BACKUP_DIR, count_bookmarks, find_folder
from src.writer import Writer
from tests.conftest import load_profile


def _cleanup(files: list[str]) -> None:
  for f in files:
    if os.path.exists(f):
      os.remove(f)

  # Clean backup dir after each test
  if BACKUP_DIR.exists():
    shutil.rmtree(BACKUP_DIR)


def test_roundtrip_pc_preserves_count() -> None:
  root = load_profile("pc")
  orig = count_bookmarks(root)
  orig_folders = [c.name for c in root.children if isinstance(c, FolderNode)]

  tmp = "bookmarks/_test_rt.html"

  try:
    Writer().write(root, tmp)
    root2 = Parser().parse(tmp)
    new_count = count_bookmarks(root2)
    new_folders = [c.name for c in root2.children if isinstance(c, FolderNode)]
    assert orig == new_count, f"Bookmark count changed: {orig} → {new_count}"
    assert orig_folders == new_folders, "Top-level folders changed"

  finally:
    _cleanup([tmp])


def test_roundtrip_all_profiles() -> None:
  for name in ("pc", "study", "work"):
    root = load_profile(name)
    orig_count = count_bookmarks(root)
    tmp = f"bookmarks/_test_rt_{name}.html"

    try:
      Writer().write(root, tmp)
      root2 = Parser().parse(tmp)
      assert orig_count == count_bookmarks(root2)

    finally:
      _cleanup([tmp])


def test_backup_created_in_backups_dir() -> None:
  root = load_profile("pc")

  tmp = "bookmarks/_test_bak.html"

  try:
    with open(tmp, "w") as f:
      f.write("dummy")
    bak = Writer().write(root, tmp)

    assert bak != "", "Backup path should not be empty"
    assert os.path.exists(bak), f"Backup not found: {bak}"
    assert "backups" in bak, f"Backup not in backups dir: {bak}"
    assert bak.endswith(".html"), f"Backup should have .html extension: {bak}"

  finally:
    _cleanup([tmp])


def test_backup_not_created_for_new_file() -> None:
  root = load_profile("pc")
  tmp = "bookmarks/_test_new.html"

  try:
    assert not os.path.exists(tmp)
    bak = Writer().write(root, tmp)
    assert bak == "", "Backup should not be created for new file"
    assert os.path.exists(tmp), "File not written"

  finally:
    _cleanup([tmp])


def test_icon_preserved_in_roundtrip() -> None:
  root = load_profile("work")
  tools = find_folder(root, "Tools")

  assert tools is not None

  neyro = find_folder(tools, "Neyro")

  assert neyro is not None

  bms = [c for c in neyro.children if isinstance(c, BookmarkItem) and c.icon]

  assert len(bms) > 0, "No bookmarks with icons found"

  orig_icon = bms[0].icon

  tmp = "bookmarks/_test_icon.html"

  try:
    Writer().write(root, tmp)
    root2 = Parser().parse(tmp)
    tools2 = find_folder(root2, "Tools")
    neyro2 = find_folder(tools2, "Neyro")
    found = next(
      (c for c in neyro2.children if isinstance(c, BookmarkItem) and c.icon == orig_icon),
      None,
    )
    assert found is not None, f"Icon not preserved: {orig_icon[:30]}..."

  finally:
    _cleanup([tmp])
