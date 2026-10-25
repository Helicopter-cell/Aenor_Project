from types import SimpleNamespace

from services import gemini_service


def test_load_prompt_strips_previously_assembled_references(monkeypatch, tmp_path):
    prompt_file = tmp_path / "legacy-prompt.txt"
    prompt_file.write_text(
        "Consigne de rôle\n\n---\n\nAncienne grammaire\n\n---\n\nAncien lexique",
        encoding="utf-8",
    )
    monkeypatch.setattr(gemini_service, "prompt_path", lambda _role: str(prompt_file))

    assert gemini_service.load_prompt("legacy-test") == "Consigne de rôle"


def test_global_prompt_debug_shows_each_destination(monkeypatch, capsys, tmp_path):
    monkeypatch.setattr(gemini_service, "PRINT_GLOBAL_PROMPT", True)
    monkeypatch.setattr(
        gemini_service,
        "get_path",
        lambda alias: tmp_path / (
            "Global_Manual_V2.md"
            if alias == "|rootPATH|grammaire_aenor"
            else "Lexique_ae_V2.json"
        ),
    )
    monkeypatch.setattr(
        gemini_service,
        "prompt_path",
        lambda role: str(
            tmp_path
            / (
                "prompt_revision_traduction.txt"
                if role == "revision"
                else "prompt_trad_fr2ae.txt"
            )
        ),
    )

    gemini_service._print_global_prompt(
        "fr2aenor",
        reference_is_cached=False,
        model_name="gemini-3.6-flash",
        additional_prompt_roles=("revision",),
    )

    output = capsys.readouterr().out
    assert "Modèle LLM utilisé : gemini-3.6-flash" in output
    assert "Global_Manual_V2.md -> Gemini system_instruction" in output
    assert "Lexique_ae_V2.json -> Gemini contents (bloc de données de référence)" in output
    assert "prompt_trad_fr2ae.txt -> Gemini contents" in output
    assert "prompt_revision_traduction.txt -> Gemini contents" in output
    assert "Règles globales" not in output
    assert '{"bonjour":"bon"}' not in output
    assert "Consigne ciblée" not in output
    assert "Bonjour" not in output


def _prepare_translation(monkeypatch, keys, clients):
    monkeypatch.setattr(gemini_service, "load_prompt", lambda _role: "system context")
    monkeypatch.setattr(
        gemini_service,
        "_load_reference_resources",
        lambda: ("V2 manual", '{"bonjour":"bon"}'),
    )
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
    monkeypatch.setattr(
        gemini_service,
        "_print_global_prompt",
        lambda *_args, **_kwargs: None,
    )
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
    requests = []

    def generate_content(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(text="Résultat %13%")

    _prepare_translation(
        monkeypatch,
        ["test-key"],
        {"test-key": _client(generate_content)},
    )

    translation, comment = gemini_service.traduire_avec_gemini("Bonjour")

    assert translation == "Résultat 11"
    assert comment == ""
    assert requests[0]["config"].system_instruction == "V2 manual"
    assert "### DONNÉES DE RÉFÉRENCE — LEXIQUE AËNOR (JSON)" in requests[0]["contents"]
    assert '{"bonjour":"bon"}' in requests[0]["contents"]
    assert "Phrase à traduire :\nBonjour" in requests[0]["contents"]


def test_reverse_translation_preprocesses_base12_numbers_and_cleans_markers(monkeypatch):
    requests = []
    _prepare_translation(
        monkeypatch,
        ["test-key"],
        {
            "test-key": _client(
                lambda **kwargs: (
                    requests.append(kwargs)
                    or SimpleNamespace(text="Valeur %30%")
                )
            )
        },
    )

    translation, _comment = gemini_service.traduire_avec_gemini(
        "26",
        direction="aenor2fr",
    )

    assert "Phrase à traduire :\n%30%" in requests[0]["contents"]
    assert translation == "Valeur 30"


def test_translation_uses_cached_reference_data(monkeypatch):
    requests = []
    _prepare_translation(
        monkeypatch,
        ["test-key"],
        {
            "test-key": _client(
                lambda **kwargs: (
                    requests.append(kwargs) or SimpleNamespace(text="Réponse")
                )
            ),
        },
    )
    monkeypatch.setattr(
        gemini_service,
        "get_or_create_cache",
        lambda *_args: SimpleNamespace(name="cached-reference"),
    )

    translation, _comment = gemini_service.traduire_avec_gemini("Bonjour")

    assert translation == "Réponse"
    assert requests[0]["config"].cached_content == "cached-reference"
    assert requests[0]["contents"] == "system context\n\nPhrase à traduire :\nBonjour"
    assert "bonjour" not in requests[0]["contents"]


def test_cache_stores_manual_as_system_and_lexicon_as_reference(monkeypatch):
    captured = {}

    def create_cache(*, model, config):
        captured["model"] = model
        captured["config"] = config
        return SimpleNamespace(name="cached-reference")

    monkeypatch.setattr(gemini_service, "CACHED_CONTEXTS_ACTIVATION", True)
    monkeypatch.setattr(gemini_service, "GEMINI_CACHES", {})
    monkeypatch.setattr(gemini_service, "CACHE_EXPIRATIONS", {})
    client = SimpleNamespace(caches=SimpleNamespace(create=create_cache))

    cache = gemini_service.get_or_create_cache(
        client,
        "test-key",
        "fr2aenor",
        "V2 manual",
        '{"bonjour":"bon"}',
    )

    assert cache.name == "cached-reference"
    assert captured["config"].system_instruction == "V2 manual"
    assert "### DONNÉES DE RÉFÉRENCE — LEXIQUE AËNOR (JSON)" in captured["config"].contents
    assert '{"bonjour":"bon"}' in captured["config"].contents


def test_reliable_translation_keeps_separated_context(monkeypatch):
    requests = []
    responses = iter(("Première version", "Version vérifiée"))

    def generate_content(**kwargs):
        requests.append(kwargs)
        return SimpleNamespace(text=next(responses))

    _prepare_translation(
        monkeypatch,
        ["test-key"],
        {"test-key": _client(generate_content)},
    )

    translation, _comment = gemini_service.traduire_avec_gemini(
        "Bonjour",
        traduction_fiable=True,
    )

    assert translation == "Version vérifiée"
    assert len(requests) == 2
    for request in requests:
        assert request["config"].system_instruction == "V2 manual"
        assert "### DONNÉES DE RÉFÉRENCE — LEXIQUE AËNOR (JSON)" in request["contents"]


def test_legacy_fallback_keeps_manual_in_system_instruction(monkeypatch):
    def network_error(**_kwargs):
        raise ConnectionError("Gemini is unreachable")

    _prepare_translation(
        monkeypatch,
        ["test-key"],
        {"test-key": _client(network_error)},
    )
    captured = {}

    class LegacyModel:
        def __init__(self, _model_name, **kwargs):
            captured["system_instruction"] = kwargs["system_instruction"]

        def generate_content(self, contents):
            captured["contents"] = contents
            return SimpleNamespace(text="Réponse legacy")

    monkeypatch.setattr(
        gemini_service,
        "get_legacy_client",
        lambda _key: SimpleNamespace(GenerativeModel=LegacyModel),
    )

    translation, _comment = gemini_service.traduire_avec_gemini("Bonjour")

    assert translation == "Réponse legacy"
    assert captured["system_instruction"] == "V2 manual"
    assert "### DONNÉES DE RÉFÉRENCE — LEXIQUE AËNOR (JSON)" in captured["contents"]


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
