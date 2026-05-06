from __future__ import annotations

from pathlib import Path

import pytest

from src.models import BookmarkItem
from src.parser import parse_bookmark_file
from src.syncer import find_folder
from tests.conftest import load_profile


def test_parse_pc_profile() -> None:
  root = load_profile("pc")
  assert root.name == "Bookmarks bar"
  assert len(root.children) >= 3  # noqa: PLR2004
  folder_names = {c.name for c in root.children if hasattr(c, "name")}
  assert "Tools" in folder_names
  assert "Important" in folder_names


def test_parse_study_profile() -> None:
  root = load_profile("study")
  assert root.name == "Bookmarks bar"
  assert len(root.children) >= 2  # noqa: PLR2004
  folder_names = {c.name for c in root.children if hasattr(c, "name")}
  assert "Tools" in folder_names


def test_parse_work_profile() -> None:
  root = load_profile("work")
  assert root.name == "Bookmarks bar"
  assert len(root.children) >= 2  # noqa: PLR2004
  folder_names = {c.name for c in root.children if hasattr(c, "name")}
  assert "Tools" in folder_names
  assert "DeevLab" in folder_names


def test_parse_bookmarks_bar_detected() -> None:
  for name in ("pc", "study", "work"):
    root = load_profile(name)
    assert root.name == "Bookmarks bar"
    assert root.add_date > 0


def test_parse_nonexistent_file() -> None:
  with pytest.raises(FileNotFoundError):
    parse_bookmark_file("nonexistent.html")


def test_parse_invalid_file(tmp_path: Path) -> None:
  bad = tmp_path / "bad.html"
  bad.write_text("<html><body>Not bookmarks</body></html>")
  with pytest.raises(ValueError, match="no Bookmarks bar found"):
    parse_bookmark_file(str(bad))


def test_parse_missing_bookmarks_bar(tmp_path: Path) -> None:
  no_bar = tmp_path / "no_bar.html"
  no_bar.write_text("<DL><p><DT><H3 ADD_DATE='1' LAST_MODIFIED='2'>NoBar</H3></DL>")
  with pytest.raises(ValueError, match="no Bookmarks bar found"):
    parse_bookmark_file(str(no_bar))


def test_parse_bookmark_attributes() -> None:
  """Verify that bookmark attributes (url, add_date, icon) are preserved."""
  root = load_profile("work")
  tools = find_folder(root, "Tools")
  assert tools is not None
  neyro = find_folder(tools, "Neyro")
  assert neyro is not None
  bookmarks = [c for c in neyro.children if isinstance(c, BookmarkItem)]
  assert len(bookmarks) > 0
  for b in bookmarks:
    assert b.url.startswith("http"), f"Missing URL for {b.title}"
    assert b.add_date > 0, f"Missing add_date for {b.title}"
