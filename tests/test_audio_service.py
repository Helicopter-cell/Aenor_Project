import io
import xml.etree.ElementTree as ET

import pytest

from routes import audio as audio_routes
from services import audio_service


def test_get_or_create_audio_uses_ipa_and_caches_mp3(tmp_path, monkeypatch):
    monkeypatch.setattr(audio_service, "CACHE_AUDIO_DIR", tmp_path)
    generated_ssml = []

    def fake_synthesis(ssml):
        generated_ssml.append(ssml)
        return b"fake-mp3-audio"

    monkeypatch.setattr(audio_service, "_synthesize_audio", fake_synthesis)

    audio_file = audio_service.get_or_create_audio('<mot & "test">', '[mɔt]')
    cached_file = audio_service.get_or_create_audio('<mot & "test">', 'mɔt')

    assert audio_file == cached_file
    assert audio_file.suffix == ".mp3"
    assert audio_file.read_bytes() == b"fake-mp3-audio"
    assert len(generated_ssml) == 1

    root = ET.fromstring(generated_ssml[0])
    phoneme = root.find(".//{http://www.w3.org/2001/10/synthesis}phoneme")
    assert phoneme is not None
    assert phoneme.attrib["alphabet"] == "ipa"
    assert phoneme.attrib["ph"] == "mɔt"
    assert phoneme.text == '<mot & "test">'


def test_audio_route_rejects_missing_pronunciation(client):
    response = client.get("/api/tts", query_string={"text": "mot"})

    assert response.status_code == 400
    assert response.json["success"] is False


def test_audio_route_returns_cached_file_as_mpeg(client, tmp_path, monkeypatch):
    audio_file = tmp_path / "cached.mp3"
    audio_file.write_bytes(b"fake-mp3-audio")
    calls = []

    def fake_get_or_create_audio(text, ipa):
        calls.append((text, ipa))
        return audio_file

    monkeypatch.setattr(audio_routes, "get_or_create_audio", fake_get_or_create_audio)
    response = client.get(
        "/api/tts",
        query_string={"text": "mot", "ipa": "[mɔt]"},
    )

    assert response.status_code == 200
    assert response.mimetype == "audio/mpeg"
    assert response.data == b"fake-mp3-audio"
    assert calls == [("mot", "[mɔt]")]


def test_synthesis_requires_azure_credentials(monkeypatch):
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_KEY", "")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_REGION", "")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_ENDPOINT", "")

    with pytest.raises(audio_service.AudioConfigurationError):
        audio_service._synthesize_audio("<speak />")


def test_build_speech_endpoint_uses_azure_region(monkeypatch):
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_REGION", "francecentral")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_ENDPOINT", "")

    assert audio_service.build_speech_endpoint() == (
        "https://francecentral.tts.speech.microsoft.com/cognitiveservices/v1"
    )


def test_build_speech_endpoint_supports_resource_endpoint(monkeypatch):
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_ENDPOINT", "https://aenor.cognitiveservices.azure.com/")

    assert audio_service.build_speech_endpoint() == (
        "https://aenor.cognitiveservices.azure.com/cognitiveservices/v1"
    )


def test_build_speech_endpoint_rejects_non_https_endpoint(monkeypatch):
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_ENDPOINT", "http://localhost:5000")

    with pytest.raises(audio_service.AudioConfigurationError, match="HTTPS"):
        audio_service.build_speech_endpoint()


def test_synthesis_posts_ssml_to_azure_endpoint(monkeypatch):
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_REGION", "westeurope")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_ENDPOINT", "")

    class FakeResponse(io.BytesIO):
        status = 200
        headers = {"Content-Type": "audio/mpeg"}

    def fake_urlopen(request, timeout):
        assert request.full_url == (
            "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"
        )
        assert request.get_header("Ocp-apim-subscription-key") == "test-key"
        assert request.get_header("Content-type") == "application/ssml+xml"
        assert timeout == audio_service.SYNTHESIS_TIMEOUT_SECONDS
        return FakeResponse(b"azure-mp3")

    monkeypatch.setattr(audio_service, "urlopen", fake_urlopen)

    assert audio_service._synthesize_audio("<speak />") == b"azure-mp3"


def test_synthesis_reports_dns_failure_with_endpoint_guidance(monkeypatch):
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_REGION", "francecentral")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_ENDPOINT", "")

    def fake_urlopen(request, timeout):
        assert request is not None
        assert timeout > 0
        raise audio_service.URLError(
            audio_service.socket.gaierror(11001, "getaddrinfo failed")
        )

    monkeypatch.setattr(audio_service, "urlopen", fake_urlopen)

    with pytest.raises(audio_service.AudioSynthesisError, match="Échec DNS.*francecentral"):
        audio_service._synthesize_audio("<speak />")


def test_synthesis_rejects_non_audio_azure_response(monkeypatch):
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_KEY", "test-key")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_REGION", "westeurope")

    class FakeResponse(io.BytesIO):
        status = 200
        headers = {"Content-Type": "application/json"}

    def fake_urlopen(request, timeout):
        assert request is not None
        assert timeout > 0
        return FakeResponse(b'{"error":"invalid SSML"}')

    monkeypatch.setattr(
        audio_service,
        "urlopen",
        fake_urlopen,
    )

    with pytest.raises(audio_service.AudioSynthesisError, match="type de contenu inattendu"):
        audio_service._synthesize_audio("<speak />")


def test_audio_route_reports_missing_service_configuration(client, monkeypatch):
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_KEY", "")
    monkeypatch.setattr(audio_service, "AZURE_SPEECH_REGION", "")

    response = client.get(
        "/api/tts",
        query_string={"text": "mot", "ipa": "[mɔt]"},
    )

    assert response.status_code == 503
    assert response.json["success"] is False
