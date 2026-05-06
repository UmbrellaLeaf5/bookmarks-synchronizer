from __future__ import annotations

import os

from src.models import BookmarkItem, FolderNode
from src.parser import parse_bookmark_file
from src.syncer import count_bookmarks, find_folder
from src.writer import write_bookmark_file
from tests.conftest import load_profile


def test_roundtrip_pc_preserves_count() -> None:
  root = load_profile("pc")
  orig = count_bookmarks(root)
  orig_folders = [c.name for c in root.children if isinstance(c, FolderNode)]

  tmp = "bookmarks/_test_rt.html"
  try:
    write_bookmark_file(root, tmp)
    root2 = parse_bookmark_file(tmp)
    new_count = count_bookmarks(root2)
    new_folders = [c.name for c in root2.children if isinstance(c, FolderNode)]
    assert orig == new_count, f"Bookmark count changed: {orig} → {new_count}"
    assert orig_folders == new_folders, "Top-level folders changed"
  finally:
    for f in (tmp, tmp + ".bak"):
      if os.path.exists(f):
        os.remove(f)


def test_roundtrip_all_profiles() -> None:
  for name in ("pc", "study", "work"):
    root = load_profile(name)
    orig_count = count_bookmarks(root)
    tmp = f"bookmarks/_test_rt_{name}.html"
    try:
      write_bookmark_file(root, tmp)
      root2 = parse_bookmark_file(tmp)
      assert orig_count == count_bookmarks(root2)
    finally:
      for f in (tmp, tmp + ".bak"):
        if os.path.exists(f):
          os.remove(f)


def test_backup_created() -> None:
  root = load_profile("pc")
  tmp = "bookmarks/_test_bak.html"
  try:
    # First create a dummy file
    with open(tmp, "w") as f:
      f.write("dummy")
    write_bookmark_file(root, tmp)
    assert os.path.exists(tmp + ".bak"), "Backup file not created"
  finally:
    for f in (tmp, tmp + ".bak"):
      if os.path.exists(f):
        os.remove(f)


def test_backup_not_created_for_new_file() -> None:
  root = load_profile("pc")
  tmp = "bookmarks/_test_new.html"
  try:
    assert not os.path.exists(tmp)
    write_bookmark_file(root, tmp)
    assert os.path.exists(tmp), "File not written"
    assert not os.path.exists(tmp + ".bak"), "Backup should not exist for new file"
  finally:
    for f in (tmp, tmp + ".bak"):
      if os.path.exists(f):
        os.remove(f)


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
    write_bookmark_file(root, tmp)
    root2 = parse_bookmark_file(tmp)
    tools2 = find_folder(root2, "Tools")
    neyro2 = find_folder(tools2, "Neyro")
    found = next(
      (c for c in neyro2.children if isinstance(c, BookmarkItem) and c.icon == orig_icon),
      None,
    )
    assert found is not None, f"Icon not preserved: {orig_icon[:30]}..."
  finally:
    for f in (tmp, tmp + ".bak"):
      if os.path.exists(f):
        os.remove(f)
