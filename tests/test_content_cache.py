from modules import obsidian_vault


def test_obsidian_vault_is_cached_until_explicit_refresh(tmp_path):
    note = tmp_path / "note.md"
    note.write_text("# Première version\nTexte initial.", encoding="utf-8")
    obsidian_vault.clear_obsidian_cache()

    first_graph, first_outline = obsidian_vault.load_obsidian_vault(tmp_path)
    note.write_text("# Version actualisée\nNouveau texte.", encoding="utf-8")

    cached_graph, cached_outline = obsidian_vault.load_obsidian_vault(tmp_path)
    assert cached_graph is first_graph
    assert cached_outline == first_outline
    assert cached_graph["nodes"][0]["title"] == "Première version"

    obsidian_vault.clear_obsidian_cache()
    refreshed_graph, refreshed_outline = obsidian_vault.load_obsidian_vault(tmp_path)
    assert refreshed_graph["nodes"][0]["title"] == "Version actualisée"
    assert refreshed_outline != first_outline
