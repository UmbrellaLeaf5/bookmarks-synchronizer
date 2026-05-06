from __future__ import annotations

import copy

from src.models import BookmarkItem
from src.syncer import (
  UserDecision,
  apply_decisions,
  collect_conflicts,
  count_bookmarks,
  find_folder,
)
from tests.conftest import (
  TOOLS_PC_SUBTREE,
  TOOLS_WORK_SUBTREE,
  load_profile,
  make_bookmark,
  make_folder,
)


# === find_folder ===


def test_find_folder_exists() -> None:
  tree = make_folder(
    "Root",
    children=[
      make_folder("A", children=[make_bookmark("b1", "http://b1")]),
      make_folder("B"),
    ],
  )
  assert find_folder(tree, "A") is not None
  assert find_folder(tree, "B") is not None


def test_find_folder_missing() -> None:
  tree = make_folder("Root", children=[make_folder("A")])
  assert find_folder(tree, "Z") is None


def test_find_folder_not_in_nested() -> None:
  tree = make_folder(
    "Root",
    children=[
      make_folder("A", children=[make_folder("B")]),
    ],
  )
  assert find_folder(tree, "B") is None  # B is nested, not at root


# === count_bookmarks ===


def test_count_bookmarks_empty() -> None:
  assert count_bookmarks(make_folder("Empty")) == 0


def test_count_bookmarks_flat() -> None:
  tree = make_folder(
    "R",
    children=[
      make_bookmark("a", "http://a"),
      make_bookmark("b", "http://b"),
    ],
  )
  assert count_bookmarks(tree) == 2  # noqa: PLR2004


def test_count_bookmarks_nested() -> None:
  tree = make_folder(
    "R",
    children=[
      make_bookmark("a", "http://a"),
      make_folder(
        "Sub",
        children=[
          make_bookmark("b", "http://b"),
          make_bookmark("c", "http://c"),
        ],
      ),
    ],
  )
  assert count_bookmarks(tree) == 3  # noqa: PLR2004


# === collect_conflicts ===


class TestCollectConflicts:
  def test_no_conflicts_when_identical(self) -> None:
    children = [
      make_bookmark("x", "http://x"),
      make_bookmark("y", "http://y"),
    ]
    tree_a = make_folder("Root", children=children)
    tree_b = make_folder("Root", children=children)
    conflicts = collect_conflicts({"a": tree_a, "b": tree_b}, ["Root"])
    assert len(conflicts) == 0

  def test_bookmark_missing_in_one_profile(self) -> None:
    tree_a = make_folder(
      "Root",
      children=[
        make_bookmark("x", "http://x"),
        make_bookmark("y", "http://y"),
      ],
    )
    tree_b = make_folder(
      "Root",
      children=[
        make_bookmark("x", "http://x"),
      ],
    )
    conflicts = collect_conflicts({"a": tree_a, "b": tree_b}, ["Root"])
    assert len(conflicts) == 1
    c = conflicts[0]
    assert c.url == "http://y"
    assert c.present_in == ["a"]
    assert c.missing_from == ["b"]

  def test_icon_in_conflict(self) -> None:
    tree_a = make_folder(
      "Root",
      children=[
        make_bookmark("x", "http://x", icon="icon:data"),
      ],
    )
    tree_b = make_folder("Root", children=[])
    conflicts = collect_conflicts({"a": tree_a, "b": tree_b}, ["Root"])
    assert len(conflicts) == 1
    assert conflicts[0].icon == "icon:data"

  def test_folder_missing_in_one_profile(self) -> None:
    tree_a = make_folder(
      "Root",
      children=[
        make_folder("Sub", children=[make_bookmark("b", "http://b")]),
      ],
    )
    tree_b = make_folder("Root", children=[])
    conflicts = collect_conflicts({"a": tree_a, "b": tree_b}, ["Root"])
    folder_cf = [c for c in conflicts if c.url.startswith("__folder__")]
    assert len(folder_cf) == 1
    assert folder_cf[0].title == "[Папка] Sub"
    assert folder_cf[0].present_in == ["a"]
    assert folder_cf[0].missing_from == ["b"]

  def test_real_files_have_conflicts(self) -> None:
    pc_root = load_profile("pc")
    work_root = load_profile("work")
    tools_pc = find_folder(pc_root, "Tools")
    tools_work = find_folder(work_root, "Tools")
    assert tools_pc is not None and tools_work is not None
    conflicts = collect_conflicts({"pc": tools_pc, "work": tools_work}, ["Tools"])
    assert len(conflicts) > 0

  def test_nested_folder_missing(self) -> None:
    root_a = make_folder(
      "Root",
      children=[
        make_folder(
          "Neyro",
          children=[
            make_bookmark("x", "http://x"),
          ],
        ),
      ],
    )
    root_b = make_folder(
      "Root",
      children=[
        make_folder(
          "Neyro",
          children=[
            make_bookmark("x", "http://x"),
            make_folder(
              "chats",
              children=[
                make_bookmark("g", "http://g"),
              ],
            ),
          ],
        ),
      ],
    )
    conflicts = collect_conflicts({"a": root_a, "b": root_b}, ["Root"])
    folder_cf = [c for c in conflicts if c.url.startswith("__folder__")]
    assert len(folder_cf) == 1
    assert folder_cf[0].title == "[Папка] chats"
    assert folder_cf[0].folder_path == ["Root", "Neyro"]


# === apply_decisions — Bug 1: deep-copy folder ===


class TestApplyDecisionsFolderAdd:
  def _make_maps(self):
    """Return (dst_tools, src_tools, maps) where dst is PC and src is Work.
    dst and src are already TOOLS-PC and TOOLS-WORK subtrees."""
    dst = copy.deepcopy(TOOLS_PC_SUBTREE)
    src = copy.deepcopy(TOOLS_WORK_SUBTREE)
    return dst, src, {"pc": dst, "work": src}

  def test_add_folder_deep_copies_content(self) -> None:
    """Bug 1: when adding a folder, entire subtree must be deep-copied."""
    dst, _, maps = self._make_maps()
    d = UserDecision(
      url="__folder__:chats",
      title="[Папка] chats",
      add_date=0,
      folder_path=["Tools", "Neyro"],
      action="add",
      target_profiles=["pc"],
      source_profile="work",
    )
    apply_decisions(maps, [d])
    neyro = find_folder(dst, "Neyro")
    chats = find_folder(neyro, "chats")
    assert chats is not None
    assert count_bookmarks(chats) == 2, (  # noqa: PLR2004
      f"Expected 2 bookmarks (deep-copied), got {count_bookmarks(chats)}"
    )

  def test_add_folder_is_deep_copy_independent(self) -> None:
    dst, src, maps = self._make_maps()
    d = UserDecision(
      url="__folder__:chats",
      title="[Папка] chats",
      add_date=0,
      folder_path=["Tools", "Neyro"],
      action="add",
      target_profiles=["pc"],
      source_profile="work",
    )
    apply_decisions(maps, [d])

    neyro_src = find_folder(src, "Neyro")
    chats_src = find_folder(neyro_src, "chats")
    neyro_dst = find_folder(dst, "Neyro")
    chats_dst = find_folder(neyro_dst, "chats")
    chats_dst.name = "MODIFIED"
    assert chats_src.name == "chats", "Source was modified by deep copy mutation"

  def test_add_folder_does_not_create_duplicate(self) -> None:
    dst, _, maps = self._make_maps()
    neyro = find_folder(dst, "Neyro")
    neyro.children.append(
      make_folder(
        "chats",
        children=[
          make_bookmark("x", "http://x"),
        ],
      )
    )
    before = count_bookmarks(dst)
    d = UserDecision(
      url="__folder__:chats",
      title="[Папка] chats",
      add_date=0,
      folder_path=["Tools", "Neyro"],
      action="add",
      target_profiles=["pc"],
      source_profile="work",
    )
    apply_decisions(maps, [d])
    assert count_bookmarks(dst) == before, "Duplicate folder was added"

  def test_add_folder_fallback_when_no_source(self) -> None:
    dst = copy.deepcopy(TOOLS_PC_SUBTREE)
    d = UserDecision(
      url="__folder__:NewFolder",
      title="[Папка] NewFolder",
      add_date=0,
      folder_path=["Tools"],
      action="add",
      target_profiles=["pc"],
      source_profile=None,
    )
    apply_decisions({"pc": dst}, [d])
    new_f = find_folder(dst, "NewFolder")
    assert new_f is not None, "Folder not created (fallback)"
    assert count_bookmarks(new_f) == 0, "Fallback folder should be empty"

  def test_add_folder_over_multiple_profiles(self) -> None:
    src = copy.deepcopy(TOOLS_WORK_SUBTREE)
    dst_pc = copy.deepcopy(TOOLS_PC_SUBTREE)
    dst_study = copy.deepcopy(TOOLS_PC_SUBTREE)
    maps = {"pc": dst_pc, "study": dst_study, "work": src}
    d = UserDecision(
      url="__folder__:chats",
      title="[Папка] chats",
      add_date=0,
      folder_path=["Tools", "Neyro"],
      action="add",
      target_profiles=["pc", "study"],
      source_profile="work",
    )
    apply_decisions(maps, [d])
    for dst in (dst_pc, dst_study):
      n = find_folder(dst, "Neyro")
      c = find_folder(n, "chats")
      assert c is not None, "chats not created"
      assert count_bookmarks(c) == 2  # noqa: PLR2004


# === apply_decisions — Bug 2: auto-create parent folder ===


class TestAutoCreateParent:
  def test_add_bookmark_auto_creates_missing_parent(self) -> None:
    """Bug 2: adding a bookmark should auto-create the parent folder hierarchy."""
    dst = copy.deepcopy(TOOLS_PC_SUBTREE)
    src = copy.deepcopy(TOOLS_WORK_SUBTREE)
    maps = {"pc": dst, "work": src}
    neyro = find_folder(dst, "Neyro")
    assert find_folder(neyro, "chats") is None, "chats should not exist yet"

    d = UserDecision(
      url="http://google.ai/",
      title="Google Ai",
      add_date=500,
      folder_path=["Tools", "Neyro", "chats"],
      action="add",
      target_profiles=["pc"],
      source_profile="work",
    )
    apply_decisions(maps, [d])

    chat = find_folder(neyro, "chats")
    assert chat is not None, "chats folder was not auto-created"
    has_bm = any(
      isinstance(c, BookmarkItem) and c.title == "Google Ai" for c in chat.children
    )
    assert has_bm, "The specific bookmark should be in the auto-created folder"

  def test_auto_create_nested_hierarchy(self) -> None:
    dst = make_folder(
      "Root",
      children=[
        make_folder(
          "a",
          children=[
            make_folder("b"),
          ],
        ),
      ],
    )
    src = make_folder(
      "Root",
      children=[
        make_folder(
          "a",
          children=[
            make_folder(
              "b",
              children=[
                make_folder(
                  "c",
                  children=[
                    make_bookmark("x", "http://x/", icon="icon:x"),
                  ],
                ),
              ],
            ),
          ],
        ),
      ],
    )
    d = UserDecision(
      url="http://x/",
      title="x",
      add_date=100,
      folder_path=["Root", "a", "b", "c"],
      action="add",
      target_profiles=["pc"],
      source_profile="src",
    )
    apply_decisions({"pc": dst, "src": src}, [d])

    a = find_folder(dst, "a")
    b = find_folder(a, "b")
    c = find_folder(b, "c")
    assert c is not None, "nested folder 'c' not auto-created"
    assert count_bookmarks(c) >= 1

  def test_no_duplicate_bookmark_when_folder_auto_created(self) -> None:
    dst = copy.deepcopy(TOOLS_PC_SUBTREE)
    src = copy.deepcopy(TOOLS_WORK_SUBTREE)
    maps = {"pc": dst, "work": src}
    neyro = find_folder(dst, "Neyro")

    d_folder = UserDecision(
      url="__folder__:chats",
      title="[Папка] chats",
      add_date=0,
      folder_path=["Tools", "Neyro"],
      action="add",
      target_profiles=["pc"],
      source_profile="work",
    )
    apply_decisions(maps, [d_folder])

    d_bm = UserDecision(
      url="http://google.ai/",
      title="Google Ai",
      add_date=500,
      folder_path=["Tools", "Neyro", "chats"],
      action="add",
      target_profiles=["pc"],
      source_profile="work",
    )
    apply_decisions(maps, [d_bm])

    chat = find_folder(neyro, "chats")
    urls = [c.url for c in chat.children if isinstance(c, BookmarkItem)]
    assert len(urls) == len(set(urls)), f"Duplicate URLs found: {urls}"


# === apply_decisions — Bug 3: icon preservation ===


class TestIconPreservation:
  def test_add_bookmark_preserves_icon(self) -> None:
    """Bug 3: when adding a bookmark, the icon must be preserved."""
    dst = copy.deepcopy(TOOLS_PC_SUBTREE)
    neyro = find_folder(dst, "Neyro")

    d = UserDecision(
      url="http://new-url/",
      title="New Bookmark",
      add_date=100,
      folder_path=["Tools", "Neyro"],
      action="add",
      target_profiles=["pc"],
      icon="data:icon:test",
    )
    apply_decisions({"pc": dst}, [d])

    added = next(
      (
        c
        for c in neyro.children
        if isinstance(c, BookmarkItem) and c.url == "http://new-url/"
      ),
      None,
    )
    assert added is not None, "Bookmark not added"
    assert added.icon == "data:icon:test"

  def test_remove_bookmark(self) -> None:
    dst = copy.deepcopy(TOOLS_PC_SUBTREE)
    neyro = find_folder(dst, "Neyro")
    before = count_bookmarks(dst)

    d = UserDecision(
      url="https://chatgpt.com/",
      title="ChatGPT",
      add_date=100,
      folder_path=["Tools", "Neyro"],
      action="remove",
      target_profiles=["pc"],
    )
    apply_decisions({"pc": dst}, [d])
    assert count_bookmarks(dst) == before - 1
    remaining = [c for c in neyro.children if isinstance(c, BookmarkItem)]
    assert all(c.url != "https://chatgpt.com/" for c in remaining)

  def test_remove_folder(self) -> None:
    dst = copy.deepcopy(TOOLS_PC_SUBTREE)
    neyro = find_folder(dst, "Neyro")
    neyro.children.append(
      make_folder("ToRemove", children=[make_bookmark("x", "http://x")])
    )
    assert find_folder(neyro, "ToRemove") is not None

    d = UserDecision(
      url="__folder__:ToRemove",
      title="[Папка] ToRemove",
      add_date=0,
      folder_path=["Tools", "Neyro"],
      action="remove",
      target_profiles=["pc"],
    )
    apply_decisions({"pc": dst}, [d])
    assert find_folder(neyro, "ToRemove") is None

  def test_skip_does_nothing(self) -> None:
    dst = copy.deepcopy(TOOLS_PC_SUBTREE)
    before = count_bookmarks(dst)
    d = UserDecision(
      url="http://dummy/",
      title="dummy",
      add_date=0,
      folder_path=["Tools", "Neyro"],
      action="skip",
      target_profiles=["pc"],
    )
    apply_decisions({"pc": dst}, [d])
    assert count_bookmarks(dst) == before


# === Integration with real files ===


class TestIntegrationRealFiles:
  def test_collect_and_apply_roundtrip_on_tools(self) -> None:
    pc = load_profile("pc")
    work = load_profile("work")
    tools_pc = find_folder(pc, "Tools")
    tools_work = find_folder(work, "Tools")
    assert tools_pc is not None and tools_work is not None

    conflicts = collect_conflicts({"pc": tools_pc, "work": tools_work}, ["Tools"])
    assert len(conflicts) > 0

    before = count_bookmarks(pc)
    c0 = conflicts[0]
    skip_d = UserDecision(
      url=c0.url,
      title=c0.title,
      add_date=c0.add_date,
      folder_path=c0.folder_path,
      action="skip",
      target_profiles=[],
      icon=c0.icon,
    )
    apply_decisions({"pc": tools_pc, "work": tools_work}, [skip_d])
    assert count_bookmarks(pc) == before
