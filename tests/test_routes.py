from routes import admin as admin_routes
from routes import translation as translation_routes
from modules import utils


def test_main_pages_and_scenario_are_accessible(client):
    for path in (
        "/",
        "/cours",
        "/grammaire_3",
        "/ia-trad",
        "/scenario",
        "/commentaires",
        "/historique",
        "/exercice",
        "/obj_project",
        "/admin",
        "/stats/optimisation",
    ):
        response = client.get(path)
        assert response.status_code == 200, path


def test_obj_project_page_renders(client):
    response = client.get("/obj_project")

    assert response.status_code == 200
    assert b"Mais en fait, pourquoi faire tout \xc3\xa7a ?" in response.data
    assert b"/static/CSS/main.css?v=" in response.data


def test_home_page_loads_animation_and_3d_enhancements(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"gsap.min.js" in response.data
    assert b"atropos@2.0.2" in response.data
    assert b"split-type@0.3.4" in response.data
    assert b"js/aenor-motion.js" in response.data
    assert b'id="home-voice-orb"' in response.data
    assert b"js/home-orb.js" in response.data
    assert b'data-split="words"' in response.data
    assert b'data-atropos' in response.data


def test_artistic_libraries_have_marked_content_on_target_pages(client):
    for path in ("/cours", "/grammaire_3", "/ia-trad", "/exercice", "/obj_project"):
        response = client.get(path)

        assert response.status_code == 200
        assert b'data-split="words"' in response.data, path

    for path in ("/ia-trad", "/exercice", "/obj_project"):
        response = client.get(path)

        assert b'data-atropos' in response.data, path


def test_lenis_is_loaded_only_on_lexique_and_grammar_pages(client):
    for path in ("/cours", "/grammaire_3"):
        response = client.get(path)

        assert response.status_code == 200
        assert b"js/lenis-scroll.js" in response.data

    for path in ("/", "/ia-trad", "/exercice"):
        response = client.get(path)

        assert response.status_code == 200
        assert b"js/lenis-scroll.js" not in response.data


def test_lexique_controls_render_for_real_lexicon_columns(client):
    response = client.get("/cours")

    assert response.status_code == 200
    assert b'data-lexique-toggle-all' in response.data
    assert b'id="lexique-categories"' in response.data
    assert b'data-lexique-column="aenor"' in response.data
    assert b'data-lexique-column="audio"' in response.data
    assert b'data-lexique-column="latin"' in response.data
    assert b'data-lexique-column="phonetic"' in response.data
    assert b'data-lexique-column="french"' in response.data
    assert b"js/lexique-controls.js" in response.data


def test_swup_shell_is_shared_by_public_pages_and_admin_uses_native_navigation(client):
    for path in ("/", "/cours", "/ia-trad", "/grammaire_3"):
        response = client.get(path)

        assert response.status_code == 200
        assert b'id="swup" class="transition-room"' in response.data
        assert b'data-csrf-token="' in response.data
        assert b"swup@4.10.0" in response.data
        assert b"scripts-plugin@2.1.0" in response.data
        assert b"js/swup-navigation.js" in response.data

    translator = client.get("/ia-trad")
    assert b'href="/admin" class="nav-element" data-no-swup' in translator.data

    admin = client.get("/admin")
    assert admin.status_code == 200
    assert b"swup@4.10.0" not in admin.data
    assert b'id="swup"' not in admin.data


def test_liquid_glass_filter_is_global_and_included_once(client):
    for path in ("/cours", "/grammaire_3"):
        response = client.get(path)

        assert response.status_code == 200
        assert response.data.count(b'id="glass-distortion"') == 1
        assert b'<body>\n\n<svg aria-hidden="true" focusable="false"' in response.data


def test_ambient_curves_are_persistent_on_public_pages(client):
    for path in ("/", "/cours", "/ia-trad"):
        response = client.get(path)

        assert response.status_code == 200
        assert response.data.count(b'class="ambient-curves"') == 1
        assert response.data.count(b'class="ambient-curve ') == 5
        assert response.data.count(b'class="ambient-glyph ') == 8
        assert response.data.count(b'class="ambient-ink-dust"') == 1
        assert b"js/ambient-curves.js" in response.data
        assert response.data.index(b'class="ambient-curves"') < response.data.index(b'id="swup"')


def test_audio_controller_is_loaded_only_on_pages_with_audio_players(client):
    for path in ("/cours", "/ia-trad"):
        response = client.get(path)

        assert response.status_code == 200
        assert b"js/speech.js" in response.data
        assert b'class="tts-waveform"' in response.data
        assert b"wavesurfer.js" not in response.data

    for path in ("/", "/grammaire_3", "/exercice"):
        response = client.get(path)

        assert response.status_code == 200
        assert b"wavesurfer.js" not in response.data
        assert b"js/speech.js" not in response.data


def test_template_auto_reload_is_enabled(app):
    assert app.config["TEMPLATES_AUTO_RELOAD"] is True
    assert app.jinja_env.auto_reload is True


def test_css_fingerprint_changes_when_imported_styles_change(tmp_path, monkeypatch):
    static_root = tmp_path / "static"
    css_root = static_root / "CSS"
    css_root.mkdir(parents=True)
    main_css = css_root / "main.css"
    imported_css = css_root / "components" / "pages.css"
    imported_css.parent.mkdir()
    main_css.write_text('@import url("components/pages.css");', encoding="utf-8")
    imported_css.write_text(".project-page { display: block; }", encoding="utf-8")
    monkeypatch.setattr(utils, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(utils, "get_path", lambda _alias: main_css)

    original_version = utils.static_version("|staticPATH|main")
    imported_css.write_text(".project-page { display: grid; }", encoding="utf-8")

    assert utils.static_version("|staticPATH|main") != original_version


def test_comment_form_validates_and_persists_submission(client):
    invalid = client.post("/commentaires", data={"target_element": "", "content": ""})
    assert invalid.status_code == 400

    response = client.post(
        "/commentaires",
        data={"target_element": "Interface", "content": "Tout fonctionne."},
    )
    assert response.status_code == 302
    assert client.get("/commentaires").status_code == 200


def test_exercise_form_uses_evaluation_without_calling_gemini(client, monkeypatch):
    monkeypatch.setattr(
        translation_routes,
        "evaluer_avec_gemini",
        lambda _phrase, _answer: {"note": 8, "commentaire": "Bien."},
    )
    saved = []
    monkeypatch.setattr(
        translation_routes,
        "sauvegarder_exercice",
        lambda *values: saved.append(values),
    )

    response = client.post(
        "/exercice",
        data={"answer": "roy", "phrase": "phrase d'exercice"},
    )

    assert response.status_code == 200
    assert b"Bien." in response.data
    assert saved == [("phrase d'exercice", "roy", 8, "Bien.")]


def test_translation_endpoint_rejects_missing_text(client):
    response = client.post("/traduire", json={})
    assert response.status_code == 400
    assert response.json["success"] is False


def test_translation_endpoint_returns_aenor_phonetics(client, monkeypatch):
    monkeypatch.setattr(translation_routes, "load_prompt", lambda _prompt: True)
    monkeypatch.setattr(
        translation_routes,
        "traduire_avec_gemini",
        lambda *_args, **_kwargs: ("§=/µ*²", ""),
    )

    response = client.post("/traduire", json={"texte": "salut"})

    assert response.status_code == 200
    assert response.json["traduction"] == "§=/µ*²"
    assert response.json["phonetic"] == "[ʃlɾmu]"


def test_mutating_form_rejects_request_without_csrf_token(app):
    app.config["WTF_CSRF_ENABLED"] = True
    response = app.test_client().post(
        "/commentaires",
        data={"target_element": "Interface", "content": "Commentaire"},
    )
    assert response.status_code == 400


def test_admin_cache_refresh_requires_admin_session(client, monkeypatch):
    calls = []
    monkeypatch.setattr(admin_routes, "refresh_content_caches", lambda: calls.append(True))

    unauthorized = client.post("/admin/refresh-content-cache")
    assert unauthorized.status_code == 302

    with client.session_transaction() as session:
        session["admin_authenticated"] = True
    response = client.post("/admin/refresh-content-cache")
    assert response.status_code == 200
    assert response.json["success"] is True
    assert calls == [True]
