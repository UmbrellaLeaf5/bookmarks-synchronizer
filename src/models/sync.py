from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class SyncAction(str, Enum):
  ADD = "add"
  REMOVE = "remove"
  SKIP = "skip"
  EXIT = "exit"


@dataclass
class ConflictItem:
  url: str
  title: str
  present_in: list[str]
  missing_from: list[str]
  add_date: int
  folder_path: list[str]
  icon: str | None = None


@dataclass
class UserDecision:
  url: str
  title: str
  add_date: int
  folder_path: list[str]
  action: SyncAction
  target_profiles: list[str]
  icon: str | None = None
  source_profile: str | None = None


@dataclass
class SyncReport:
  conflicts: list[ConflictItem] = field(default_factory=list)
  decisions: list[UserDecision] = field(default_factory=list)
  changes_made: int = 0
