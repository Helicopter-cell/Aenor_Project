"""Compatibility exports for Obsidian vault helpers."""

from functools import lru_cache
from pathlib import Path

from services.obsidian_service import build_obsidian_outline, parse_obsidian_vault


@lru_cache(maxsize=8)
def _load_obsidian_vault(vault_path):
    path = Path(vault_path)
    return parse_obsidian_vault(path), build_obsidian_outline(path)


def load_obsidian_vault(vault_path):
    """Load the vault graph and outline once per path."""
    return _load_obsidian_vault(str(Path(vault_path).resolve()))


def clear_obsidian_cache():
    """Clear cached vault data after Markdown files have changed."""
    _load_obsidian_vault.cache_clear()


__all__ = [
    "build_obsidian_outline",
    "clear_obsidian_cache",
    "load_obsidian_vault",
    "parse_obsidian_vault",
]
