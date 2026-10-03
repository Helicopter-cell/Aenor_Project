import json

from modules import base_converter, utils


def test_decimal_to_base12_handles_symbols_and_negative_values():
    assert base_converter.decimal_to_base12(0) == "0"
    assert base_converter.decimal_to_base12(13) == "11"
    assert base_converter.decimal_to_base12(15) == "13"
    assert base_converter.decimal_to_base12(144) == "100"
    assert base_converter.decimal_to_base12(-13) == "-11"


def test_process_aenor_numbers_replaces_only_marked_values():
    assert base_converter.process_aenor_numbers("Valeur %13%, puis %144%.") == (
        "Valeur 11, puis 100."
    )
    assert base_converter.process_aenor_numbers("Non marqué: 13") == "Non marqué: 13"


def test_aenor_phonetic_and_latin_conversion_rules():
    assert utils.convert_aenor_to_latin("§/µ=*²") == "šrm'l'ou"
    assert utils.convert_aenor_to_phonetic("§=/µ*²") == "[ʃlɾmu]"


def test_rendered_lexicon_entries_include_safe_speech_data_attributes():
    html = str(utils.render_cours_value({
        "mot": {
            "french": 'mot "test"',
            "aenor": '<mot>',
            "latin": "mot",
            "phonetic": "[mɔt]",
        },
    }))

    assert 'class="btn-tts"' in html
    assert 'data-text="&lt;mot&gt;"' in html
    assert 'data-ipa="[mɔt]"' in html


def test_lexicon_is_cached_per_file_version_and_can_be_invalidated(tmp_path, monkeypatch):
    lexicon_file = tmp_path / "lexicon.json"
    lexicon_file.write_text(json.dumps({"mot": "b"}), encoding="utf-8")
    monkeypatch.setattr(utils, "get_path", lambda _alias: lexicon_file)
    utils.clear_cours_cache()

    first_load = utils.load_cours()
    assert utils.load_cours() is first_load
    assert first_load["mot"]["phonetic"] == "[b]"

    lexicon_file.write_text(json.dumps({"mot": "§"}), encoding="utf-8")
    refreshed = utils.load_cours()
    assert refreshed is not first_load
    assert refreshed["mot"]["phonetic"] == "[ʃ]"

    utils.clear_cours_cache()
    assert utils.load_cours() is not refreshed
