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
