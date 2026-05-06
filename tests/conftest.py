from __future__ import annotations

from pathlib import Path

from src.models import BookmarkItem, FolderNode
from src.parser import parse_bookmark_file


BOOKMARKS_DIR = Path("bookmarks")


def load_profile(name: str) -> FolderNode:
  path = BOOKMARKS_DIR / f"bookmarks_for_{name}.html"
  return parse_bookmark_file(str(path))


# Shared test data: synthetic folder structures for precise control


def make_bookmark(
  title: str, url: str, add_date: int = 100, icon: str | None = None
) -> BookmarkItem:
  return BookmarkItem(title=title, url=url, add_date=add_date, icon=icon)


def make_folder(
  name: str,
  children: list[FolderNode | BookmarkItem] | None = None,
  add_date: int = 100,
  last_modified: int = 200,
) -> FolderNode:
  return FolderNode(
    name=name,
    add_date=add_date,
    last_modified=last_modified,
    children=children or [],
  )


TOOLS_WORK_SUBTREE = make_folder(
  "Tools",
  children=[
    make_folder(
      "Neyro",
      children=[
        make_bookmark("ChatGPT", "https://chatgpt.com/", 100, "icon:chatgpt"),
        make_bookmark("DeepSeek", "https://deepseek.com/", 150, "icon:deepseek"),
        make_folder(
          "chats",
          children=[
            make_bookmark("Google Ai", "https://google.ai/", 500, "icon:google"),
            make_bookmark(
              "ChatBotChatApp", "https://chatbotchatapp.com/", 510, "icon:chatbot"
            ),
          ],
        ),
      ],
    ),
    make_bookmark("Pres templates", "https://create.microsoft.com/", 300),
  ],
)

TOOLS_PC_SUBTREE = make_folder(
  "Tools",
  children=[
    make_folder(
      "Neyro",
      children=[
        make_bookmark("ChatGPT", "https://chatgpt.com/", 100, "icon:chatgpt"),
      ],
    ),
    make_folder(
      "Important",
      children=[
        make_bookmark("nbki", "https://nbki.ru/", 200),
      ],
    ),
  ],
)
