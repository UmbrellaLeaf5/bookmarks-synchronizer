import re
import time
from datetime import datetime
from pathlib import Path

from loguru import logger

from src.models.tree import BookmarkItem, FolderNode


BACKUP_DIR = Path("bookmarks") / "backups"

_ESCAPES = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}
_UNESCAPES = {"amp": "&", "lt": "<", "gt": ">", "quot": '"'}

_ESCAPE_RE = re.compile(r"[&<>\"]")
_UNESCAPE_RE = re.compile(r"&(amp|lt|gt|quot);")


def now_ts() -> int:
  return int(time.time())


def format_timestamp(ts: int) -> str:
  return datetime.fromtimestamp(ts).strftime("%d.%m.%Y %H:%M")


def escape_html(text: str) -> str:
  return _ESCAPE_RE.sub(lambda m: _ESCAPES[m.group(0)], text)


def unescape_html(text: str) -> str:
  return _UNESCAPE_RE.sub(lambda m: _UNESCAPES[m.group(1)], text)


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


def is_folder_url(url: str) -> bool:
  return url.startswith("__folder__:")


def folder_name_from_url(url: str) -> str:
  return url.split(":", 1)[1]


def setup_logging(log_path: str = "bookmarks/sync.log") -> None:
  logger.remove()
  logger.add(log_path, rotation="1 MB", retention="7 days", level="DEBUG")
