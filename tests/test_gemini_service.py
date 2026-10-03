from types import SimpleNamespace

from services import gemini_service


def _prepare_translation(monkeypatch, keys, clients):
    monkeypatch.setattr(gemini_service, "load_prompt", lambda _role: "system context")
    monkeypatch.setattr(gemini_service, "API_KEYS_POOL", keys)
    monkeypatch.setattr(gemini_service, "CURRENT_KEY_INDEX", 0)
    monkeypatch.setattr(gemini_service, "POOL_API_KEYS_ACTIVATION", True)
    monkeypatch.setattr(gemini_service, "get_gemini_client", lambda key: clients.get(key))
    monkeypatch.setattr(gemini_service, "get_or_create_cache", lambda *_args: None)
    monkeypatch.setattr(
        gemini_service,
        "_call_gemini_with_latency",
        lambda generate, *_args, **_kwargs: generate(),
    )
    monkeypatch.setattr(gemini_service, "_print_global_prompt", lambda *_args: None)
    monkeypatch.setattr(gemini_service, "enregistrer_mots_non_traduits", lambda _text: None)
    monkeypatch.setattr(gemini_service, "sauvegarder_traduction", lambda *_args: None)
    monkeypatch.setattr(
        gemini_service,
        "enregistrer_traduction_commentaire",
        lambda *_args: None,
    )


def _client(generate_content):
    return SimpleNamespace(
        models=SimpleNamespace(generate_content=generate_content),
    )


def test_translation_uses_successful_gemini_response(monkeypatch):
    _prepare_translation(
        monkeypatch,
        ["test-key"],
        {"test-key": _client(lambda **_kwargs: SimpleNamespace(text="Résultat %13%"))},
    )

    translation, comment = gemini_service.traduire_avec_gemini("Bonjour")

    assert translation == "Résultat 11"
    assert comment == ""


def test_translation_rotates_keys_after_quota_error(monkeypatch):
    def quota_error(**_kwargs):
        raise RuntimeError("429 resource exhausted: quota exceeded")

    _prepare_translation(
        monkeypatch,
        ["first-key", "second-key"],
        {
            "first-key": _client(quota_error),
            "second-key": _client(lambda **_kwargs: SimpleNamespace(text="Réponse")),
        },
    )

    translation, _comment = gemini_service.traduire_avec_gemini("Bonjour")

    assert translation == "Réponse"
    assert gemini_service.CURRENT_KEY_INDEX == 1


def test_translation_returns_error_after_network_failure(monkeypatch):
    def network_error(**_kwargs):
        raise ConnectionError("Gemini is unreachable")

    _prepare_translation(
        monkeypatch,
        ["test-key"],
        {"test-key": _client(network_error)},
    )
    monkeypatch.setattr(gemini_service, "get_legacy_client", lambda _key: None)

    translation, comment = gemini_service.traduire_avec_gemini("Bonjour")

    assert translation.startswith("Erreur : Impossible de générer la traduction.")
    assert "Gemini is unreachable" in translation
    assert comment == ""
