from flask import Blueprint, jsonify, render_template, request

from extensions import limiter
from modules.exercices import get_random_phrase
from modules.utils import convert_aenor_to_phonetic
from services.gemini_service import COMMENT_PROMPT_FILES, PROMPT_FILES, evaluer_avec_gemini, load_prompt, logger, sauvegarder_exercice, traduire_avec_gemini

translation_bp = Blueprint('translation', __name__)


@translation_bp.route('/exercice', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def exercice():
    if request.method == 'POST':
        user = request.form['answer']
        phrase = request.form['phrase']

        # Évaluer la traduction de l'élève via Gemini (professeur virtuel)
        evaluation = evaluer_avec_gemini(phrase, user)
        note = evaluation.get('note', 0)
        commentaire = evaluation.get('commentaire', '')
        sauvegarder_exercice(phrase, user, note, commentaire)

        return render_template(
            'result.html',
            note=note,
            commentaire=commentaire,
            phrase=phrase,
            user=user,
        )

    phrase = get_random_phrase()
    return render_template('exercice.html', phrase=phrase)


# =============================
# ROUTES - API / STATISTIQUES
# =============================

@translation_bp.route('/traduire', methods=['POST'])
@limiter.limit('10 per minute')
def traduire_api():
    """
    Route POST pour la traduction via Gemini.
    Utilise le contexte mis en cache et le pool de clés API pour minimiser
    les coûts, la latence et les interruptions liées aux quotas.

    L'enregistrement de la traduction dans traductions.json est géré à
    l'intérieur de traduire_avec_gemini(), uniquement en cas de succès.

    Requête JSON:
        {
            "texte": "Texte à traduire"
        }

    Réponse JSON:
        {
            "success": true/false,
            "traduction": "...",
            "erreur": "..."  // si success = false
        }
    """
    try:
        data = request.get_json()

        if not data or 'texte' not in data:
            return jsonify({
                'success': False,
                'erreur': 'Champ "texte" manquant dans la requête',
            }), 400

        texte = data['texte'].strip()
        direction = data.get('direction', 'fr2aenor')
        if direction not in ('fr2aenor', 'aenor2fr'):
            direction = 'fr2aenor'

        if not texte:
            return jsonify({
                'success': False,
                'erreur': 'Le texte à traduire ne peut pas être vide',
            }), 400

        autoriser_apprentissage = data.get('autoriser_apprentissage', False) is True
        traduction_fiable = data.get('traduction_fiable', False) is True
        prompt_roles = COMMENT_PROMPT_FILES if autoriser_apprentissage else PROMPT_FILES
        if not load_prompt(prompt_roles[direction]):
            logger.error('Contexte manquant pour la traduction')
            return jsonify({
                'success': False,
                'erreur': 'Erreur système : contexte de configuration manquant',
            }), 500

        traduction, commentaire = traduire_avec_gemini(
            texte,
            direction=direction,
            provenance='traduction',
            autoriser_apprentissage=autoriser_apprentissage,
            traduction_fiable=traduction_fiable,
        )

        result = {
            'success': True,
            'traduction': traduction,
            'commentaire': commentaire,
        }
        if direction == 'fr2aenor':
            result['phonetic'] = convert_aenor_to_phonetic(traduction)
        return jsonify(result), 200

    except Exception as exc:
        logger.error(f'Erreur non gérée dans /traduire: {exc}')
        return jsonify({
            'success': False,
            'erreur': f'Erreur serveur : {str(exc)}',
        }), 500
