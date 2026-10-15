"""
tools/file_ops.py
=================
Safe file and folder operations.

All destructive operations (delete) require explicit confirmation from the caller.
The GUI layer handles the "are you sure?" prompt before calling these functions.
"""

import os
import shutil
from pathlib import Path
from typing import Tuple, List

from core.logger import get_logger

logger = get_logger(__name__)


# ── Read operations ───────────────────────────────────────────────────────────

def list_files(directory: str) -> Tuple[bool, str]:
    """
    List files and folders in `directory`.

    Returns (success, formatted_string).
    """
    path = Path(directory.strip())
    logger.info(f"Listing directory: {path}")

    if not path.exists():
        return False, f"❌ Path does not exist: {path}"
    if not path.is_dir():
        return False, f"❌ Not a directory: {path}"

    try:
        entries: List[str] = []
        for item in sorted(path.iterdir()):
            if item.is_dir():
                entries.append(f"📁 {item.name}/")
            else:
                size_kb = round(item.stat().st_size / 1024, 1)
                entries.append(f"📄 {item.name}  ({size_kb} KB)")

        if not entries:
            return True, f"📂 **{path}** is empty."

        listing = "\n".join(entries)
        return True, f"📂 **Contents of {path}:**\n{listing}"

    except PermissionError:
        msg = f"❌ Permission denied: {path}"
        logger.warning(msg)
        return False, msg
    except Exception as exc:
        msg = f"❌ Error listing directory: {exc}"
        logger.error(msg)
        return False, msg


def read_file(file_path: str, max_chars: int = 3000) -> Tuple[bool, str]:
    """
    Read and return the text content of a file (truncated to `max_chars`).
    """
    path = Path(file_path.strip())
    logger.info(f"Reading file: {path}")

    if not path.exists():
        return False, f"❌ File not found: {path}"
    if not path.is_file():
        return False, f"❌ Not a file: {path}"

    try:
        content = path.read_text(encoding="utf-8", errors="replace")
        if len(content) > max_chars:
            content = content[:max_chars] + f"\n\n... [truncated at {max_chars} chars]"
        return True, f"📄 **{path.name}:**\n```\n{content}\n```"
    except Exception as exc:
        msg = f"❌ Failed to read file: {exc}"
        logger.error(msg)
        return False, msg


# ── Write operations ──────────────────────────────────────────────────────────

def create_folder(folder_path: str) -> Tuple[bool, str]:
    """Create a new directory (including intermediate parents)."""
    path = Path(folder_path.strip())
    logger.info(f"Creating folder: {path}")

    try:
        path.mkdir(parents=True, exist_ok=True)
        return True, f"✅ Folder created: {path}"
    except Exception as exc:
        msg = f"❌ Failed to create folder: {exc}"
        logger.error(msg)
        return False, msg


def write_file(file_path: str, content: str) -> Tuple[bool, str]:
    """
    Write text `content` to `file_path`, creating parent directories as needed.
    Overwrites if the file already exists.
    """
    path = Path(file_path.strip())
    logger.info(f"Writing file: {path}")

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return True, f"✅ File saved: {path}"
    except Exception as exc:
        msg = f"❌ Failed to write file: {exc}"
        logger.error(msg)
        return False, msg


def rename_file(old_path: str, new_name: str) -> Tuple[bool, str]:
    """
    Rename a file or folder.

    Parameters
    ----------
    old_path : str  Full path to the existing file/folder.
    new_name : str  Just the new name (not a full path).
    """
    src = Path(old_path.strip())
    logger.info(f"Renaming: {src} → {new_name}")

    if not src.exists():
        return False, f"❌ Path does not exist: {src}"

    dest = src.parent / new_name.strip()
    if dest.exists():
        return False, f"❌ A file/folder named '{new_name}' already exists in {src.parent}"

    try:
        src.rename(dest)
        return True, f"✏️  Renamed '{src.name}' → '{new_name}'"
    except Exception as exc:
        msg = f"❌ Failed to rename: {exc}"
        logger.error(msg)
        return False, msg


def move_file(src_path: str, dest_path: str) -> Tuple[bool, str]:
    """
    Move a file or folder to a new location.

    Parameters
    ----------
    src_path  : str  Full path to source.
    dest_path : str  Full path to destination directory (or new full path).
    """
    src  = Path(src_path.strip())
    dest = Path(dest_path.strip())
    logger.info(f"Moving: {src} → {dest}")

    if not src.exists():
        return False, f"❌ Source does not exist: {src}"

    try:
        # If dest is an existing directory, move INTO it
        if dest.is_dir():
            final = dest / src.name
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            final = dest

        shutil.move(str(src), str(final))
        return True, f"📦 Moved '{src.name}' → {final}"
    except Exception as exc:
        msg = f"❌ Failed to move: {exc}"
        logger.error(msg)
        return False, msg


# ── Destructive operations ────────────────────────────────────────────────────

def delete_file(target_path: str) -> Tuple[bool, str]:
    """
    Delete a file or directory.

    ⚠️  IMPORTANT: The GUI must ask for user confirmation BEFORE calling this.

    Returns (success, message).
    """
    path = Path(target_path.strip())
    logger.info(f"Deleting: {path}")

    if not path.exists():
        return False, f"❌ Path does not exist: {path}"

    try:
        if path.is_file():
            path.unlink()
            msg = f"🗑️  File deleted: {path}"
        elif path.is_dir():
            shutil.rmtree(path)
            msg = f"🗑️  Folder deleted: {path}"
        else:
            return False, f"❌ Unknown path type: {path}"

        logger.info(msg)
        return True, msg

    except PermissionError:
        msg = f"❌ Permission denied — cannot delete: {path}"
        logger.warning(msg)
        return False, msg
    except Exception as exc:
        msg = f"❌ Failed to delete: {exc}"
        logger.error(msg)
        return False, msg
