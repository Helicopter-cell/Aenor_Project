"""Azure Speech synthesis and on-disk MP3 caching for Aënor."""

import hashlib
import json
import logging
import os
import re
import socket
import tempfile
import threading
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.sax.saxutils import escape, quoteattr


logger = logging.getLogger(__name__)

AZURE_SPEECH_KEY = os.environ.get("AZURE_SPEECH_KEY", "").strip()
AZURE_SPEECH_REGION = os.environ.get("AZURE_SPEECH_REGION", "").strip()
AZURE_SPEECH_ENDPOINT = os.environ.get("AZURE_SPEECH_ENDPOINT", "").strip()
AZURE_SPEECH_LANGUAGE = os.environ.get("AZURE_SPEECH_LANGUAGE", "fr-FR").strip()
AZURE_SPEECH_VOICE = os.environ.get("AZURE_SPEECH_VOICE", "fr-FR-DeniseNeural").strip()
AZURE_SPEECH_RATE = float(os.environ.get("AZURE_SPEECH_RATE", "0.85"))
AZURE_SPEECH_PITCH = float(os.environ.get("AZURE_SPEECH_PITCH", "0"))
AZURE_SPEECH_OUTPUT_FORMAT = os.environ.get(
    "AZURE_SPEECH_OUTPUT_FORMAT",
    "audio-24khz-48kbitrate-mono-mp3",
).strip()

MAX_TEXT_LENGTH = 500
MAX_IPA_LENGTH = 1000
CACHE_AUDIO_DIR = Path(__file__).resolve().parent.parent / "static" / "cache_audio"
SYNTHESIS_TIMEOUT_SECONDS = 30

_cache_locks_guard = threading.Lock()
_cache_locks: dict[str, threading.Lock] = {}


class AudioConfigurationError(RuntimeError):
    """Raised when Azure Speech credentials or settings are unavailable."""


class AudioSynthesisError(RuntimeError):
    """Raised when Azure Speech cannot synthesize the requested audio."""


def build_speech_endpoint() -> str:
    """Build the regional endpoint or a resource-specific Azure TTS endpoint."""
    if AZURE_SPEECH_ENDPOINT:
        parsed_endpoint = urlsplit(AZURE_SPEECH_ENDPOINT)
        if (
            parsed_endpoint.scheme.lower() != "https"
            or not parsed_endpoint.hostname
            or parsed_endpoint.username
            or parsed_endpoint.password
            or parsed_endpoint.query
            or parsed_endpoint.fragment
        ):
            raise AudioConfigurationError(
                "AZURE_SPEECH_ENDPOINT doit être une URL HTTPS valide sans identifiants, "
                "paramètres ni fragment."
            )

        endpoint_path = parsed_endpoint.path.rstrip("/")
        if endpoint_path and endpoint_path != "/cognitiveservices/v1":
            raise AudioConfigurationError(
                "AZURE_SPEECH_ENDPOINT doit être l'endpoint de ressource Azure "
                "ou se terminer par /cognitiveservices/v1."
            )
        return urlunsplit((
            "https",
            parsed_endpoint.netloc,
            endpoint_path or "/cognitiveservices/v1",
            "",
            "",
        ))

    if not re.fullmatch(r"[a-z0-9-]+", AZURE_SPEECH_REGION):
        raise AudioConfigurationError(
            "AZURE_SPEECH_REGION doit être le nom de région Azure, par exemple francecentral."
        )
    return (
        f"https://{AZURE_SPEECH_REGION}.tts.speech.microsoft.com/"
        "cognitiveservices/v1"
    )


def normalize_speech_input(text: str, ipa: str) -> tuple[str, str]:
    """Validate and normalize text and bracketed IPA received from the client."""
    if not isinstance(text, str) or not isinstance(ipa, str):
        raise ValueError("Les paramètres text et ipa doivent être des chaînes.")

    clean_text = text.strip()
    clean_ipa = ipa.strip()
    if clean_ipa.startswith("[") and clean_ipa.endswith("]"):
        clean_ipa = clean_ipa[1:-1].strip()

    if not clean_text or not clean_ipa:
        raise ValueError("Les paramètres text et ipa sont obligatoires.")
    if len(clean_text) > MAX_TEXT_LENGTH or len(clean_ipa) > MAX_IPA_LENGTH:
        raise ValueError("Le texte ou la transcription phonétique est trop longue.")
    if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", clean_text + clean_ipa):
        raise ValueError("Le texte contient des caractères de contrôle invalides.")

    return clean_text, clean_ipa


def build_ssml(text: str, ipa: str) -> str:
    """Build escaped Azure SSML that requests the supplied IPA pronunciation."""
    return (
        '<speak version="1.0" '
        'xmlns="http://www.w3.org/2001/10/synthesis" '
        f'xml:lang={quoteattr(AZURE_SPEECH_LANGUAGE)}>'
        f'<voice name={quoteattr(AZURE_SPEECH_VOICE)}>'
        f'<prosody rate="{AZURE_SPEECH_RATE * 100:.0f}%" '
        f'pitch="{AZURE_SPEECH_PITCH:+g}st">'
        f'<phoneme alphabet="ipa" ph={quoteattr(ipa)}>{escape(text)}</phoneme>'
        '</prosody></voice></speak>'
    )


def _synthesize_audio(ssml: str) -> bytes:
    if not AZURE_SPEECH_KEY or (not AZURE_SPEECH_REGION and not AZURE_SPEECH_ENDPOINT):
        raise AudioConfigurationError(
            "Configurez AZURE_SPEECH_KEY et soit AZURE_SPEECH_REGION, soit "
            "AZURE_SPEECH_ENDPOINT pour activer la synthèse vocale."
        )

    endpoint = build_speech_endpoint()
    endpoint_host = urlsplit(endpoint).hostname
    request = Request(
        endpoint,
        data=ssml.encode("utf-8"),
        headers={
            "Content-Type": "application/ssml+xml",
            "Ocp-Apim-Subscription-Key": AZURE_SPEECH_KEY,
            "X-Microsoft-OutputFormat": AZURE_SPEECH_OUTPUT_FORMAT,
            "User-Agent": "AenorTTS/1.0",
        },
        method="POST",
    )

    try:
        with urlopen(request, timeout=SYNTHESIS_TIMEOUT_SECONDS) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            audio = response.read()
    except HTTPError as error:
        detail = error.read(1024).decode("utf-8", errors="replace").strip()
        raise AudioSynthesisError(
            f"Azure Speech a refusé la synthèse (HTTP {error.code}): {detail}"
        ) from error
    except URLError as error:
        if isinstance(error.reason, socket.gaierror):
            raise AudioSynthesisError(
                f"Échec DNS pour l'hôte Azure Speech « {endpoint_host} ». "
                "Vérifiez la résolution DNS et l'accès réseau, ou définissez "
                "AZURE_SPEECH_ENDPOINT avec l'endpoint HTTPS de la ressource "
                "indiqué dans Azure (Keys and Endpoint)."
            ) from error
        raise AudioSynthesisError(
            f"Azure Speech est injoignable à l'hôte « {endpoint_host} »: {error.reason}"
        ) from error

    if not audio:
        raise AudioSynthesisError("Azure Speech a renvoyé un fichier audio vide.")
    if not content_type.lower().startswith("audio/"):
        logger.error(
            "Azure Speech a renvoyé une réponse non audio: status=%s content_type=%s bytes=%s",
            status,
            content_type or "<absent>",
            len(audio),
        )
        raise AudioSynthesisError(
            f"Azure Speech a renvoyé un type de contenu inattendu: {content_type or 'absent'}."
        )

    logger.info(
        "Synthèse Azure réussie: status=%s content_type=%s bytes=%s",
        status,
        content_type,
        len(audio),
    )
    return audio


def _cache_key(text: str, ipa: str) -> str:
    settings = {
        "text": text,
        "ipa": ipa,
        "language": AZURE_SPEECH_LANGUAGE,
        "voice": AZURE_SPEECH_VOICE,
        "rate": AZURE_SPEECH_RATE,
        "pitch": AZURE_SPEECH_PITCH,
        "output_format": AZURE_SPEECH_OUTPUT_FORMAT,
    }
    serialized = json.dumps(settings, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _lock_for_cache_key(cache_key: str) -> threading.Lock:
    with _cache_locks_guard:
        return _cache_locks.setdefault(cache_key, threading.Lock())


def get_or_create_audio(text: str, ipa: str) -> Path:
    """Return the cached MP3 for a pronunciation, generating it on a cache miss."""
    clean_text, clean_ipa = normalize_speech_input(text, ipa)
    cache_key = _cache_key(clean_text, clean_ipa)
    cached_file = CACHE_AUDIO_DIR / f"{cache_key}.mp3"

    with _lock_for_cache_key(cache_key):
        if cached_file.is_file() and cached_file.stat().st_size:
            return cached_file

        CACHE_AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        audio = _synthesize_audio(build_ssml(clean_text, clean_ipa))

        temporary_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="wb",
                prefix=f"{cache_key}-",
                suffix=".tmp",
                dir=CACHE_AUDIO_DIR,
                delete=False,
            ) as temporary_file:
                temporary_path = Path(temporary_file.name)
                temporary_file.write(audio)
            os.replace(temporary_path, cached_file)
        finally:
            if temporary_path and temporary_path.exists():
                temporary_path.unlink()

    return cached_file
