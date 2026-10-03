"""Cache invalidation helpers for reloadable application data."""

from modules.obsidian_vault import clear_obsidian_cache
from modules.utils import clear_cours_cache


def refresh_content_caches() -> None:
    """Clear cached lexicon and Obsidian data after source files change."""
    clear_cours_cache()
    clear_obsidian_cache()
