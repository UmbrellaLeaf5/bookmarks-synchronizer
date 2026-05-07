import sys

from loguru import logger

from src.cli import Cli
from src.config import load_config
from src.models.sync import SyncAction
from src.models.tree import Profile
from src.parser import Parser
from src.syncer import Syncer
from src.utils import count_bookmarks, setup_logging
from src.writer import Writer


def main() -> None:
  setup_logging()
  logger.info("Bookmarks Synchronizer started")

  dry_run = "--dry-run" in sys.argv

  print("=" * 60)
  print("  Bookmarks Synchronizer - Chrome bookmarks sync")
  if dry_run:
    print("  [DRY-RUN] Files will not be modified")
  print("=" * 60)

  parser = Parser()
  writer = Writer()

  cli = Cli()

  # 1. Load config
  print("\n[1/5] Loading configuration...")

  try:
    config = load_config("config.json")

  except (FileNotFoundError, ValueError) as e:
    logger.error(f"Config load failed: {e}")
    print(f"  [X] {e}")
    return

  print(f"  Profiles: {', '.join(config.profiles.keys())}")
  print(f"  Shared folders: {', '.join(config.shared_folders)}")

  # 2. Parse profiles
  print("\n[2/5] Reading bookmark files...")
  profiles: dict[str, Profile] = {}

  for name, path in config.profiles.items():
    logger.debug(f"Parsing {name}: {path}")
    root = parser.parse(path)
    total = count_bookmarks(root)
    profiles[name] = Profile(name=name, filepath=path, root=root)
    print(f"  [V] {name}: {total} bookmarks")

  print("  [V] All files read")

  syncer = Syncer(
    {name: profile.root for name, profile in profiles.items() if profile.root is not None}
  )

  # 3. Collect conflicts
  print("\n[3/5] Searching for conflicts in shared folders...")
  all_conflicts = []

  for shared_folder in config.shared_folders:
    conflicts = syncer.collect_conflicts(shared_folder)
    all_conflicts.extend(conflicts)

    print(f'  Folder "{shared_folder}": {len(conflicts)} conflicts')

  if not all_conflicts:
    print("\n  [V] No conflicts. All profiles synchronized.")
    logger.info("No conflicts found, exiting")
    return

  print(f"\n  Total conflicts: {len(all_conflicts)}")

  # 4. Interactive resolution
  print("\n[4/5] Resolving conflicts (a/r/s/e for each)...")

  decisions = []

  try:
    for i, conflict in enumerate(all_conflicts, 1):
      print(f"\n  --- Conflict {i}/{len(all_conflicts)} ---")
      decision = cli.ask(conflict)

      if decision.action == SyncAction.EXIT:
        print("  Exit by user request.")
        break

      decisions.append(decision)

  except KeyboardInterrupt:
    print("\n\n  Interrupted by user. Applying accepted decisions...")
    logger.info(f"Interrupted by user. Applying {len(decisions)} decisions")

  if not decisions:
    print("  No decisions made. Exiting.")
    return

  # 5. Apply and write
  print(f"\n[5/5] Applying {len(decisions)} decisions...")
  changes = 0

  for shared_folder in config.shared_folders:
    report = syncer.apply_decisions(shared_folder, decisions)
    changes += report.changes_made

  for name, profile in profiles.items():
    assert profile.root is not None

    if dry_run:
      print(f"  [DRY-RUN] Would write {name}: {profile.filepath}")
      continue

    try:
      bak = writer.write(profile.root, profile.filepath)

    except OSError as e:
      logger.error(f"Write failed for {name}: {e}")
      print(f"  [X] {name}: write error - {e}")
      continue

    msg = f"  [V] {name}: saved"

    if bak:
      msg += f" (backup: {bak})"
    print(msg)

  cli.show_summary(
    conflicts_found=len(all_conflicts),
    decisions_made=len(decisions),
    changes_applied=changes,
  )

  print("\n  [V] Done!")
  logger.info("Sync completed")


if __name__ == "__main__":
  main()
