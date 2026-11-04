"""HTTP endpoints for cached Aënor speech audio."""

import logging

from flask import Blueprint, jsonify, request, send_file

from extensions import limiter
from services.audio_service import (
    AudioConfigurationError,
    AudioSynthesisError,
    get_or_create_audio,
)


audio_bp = Blueprint("audio", __name__)
logger = logging.getLogger(__name__)


@audio_bp.get("/api/tts")
@limiter.limit("30 per minute")
def synthesize_aenor_audio():
    text = request.args.get("text", "")
    ipa = request.args.get("ipa", "")

    try:
        audio_path = get_or_create_audio(text, ipa)
    except ValueError as error:
        return jsonify({"success": False, "error": str(error)}), 400
    except AudioConfigurationError as error:
        return jsonify({"success": False, "error": str(error)}), 503
    except AudioSynthesisError as error:
        logger.error("Échec de synthèse vocale Azure: %s", error)
        return jsonify({
            "success": False,
            "error": str(error),
        }), 502

    response = send_file(
        audio_path,
        mimetype="audio/mpeg",
        conditional=True,
        etag=True,
        max_age=31536000,
    )
    logger.info(
        "Réponse TTS servie: status=%s content_type=%s bytes=%s",
        response.status_code,
        response.mimetype,
        response.content_length,
    )
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response
