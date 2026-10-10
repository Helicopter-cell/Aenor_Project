import hmac
import sqlite3
from datetime import datetime

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from modules.utils import load_cours
from services.gemini_service import DB_FILE, FEEDBACK_TARGETS, get_admin_password

main_bp = Blueprint('main', __name__)


@main_bp.route('/historique')
def historique():
    """Affiche l'historique associé à la session courante."""
    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        traductions = conn.execute(
            '''SELECT source_text, target_text, direction, timestamp, traduction_fiable
               FROM traductions_historique
               WHERE user_uuid = ? ORDER BY timestamp DESC, id DESC''',
            (session['user_uuid'],),
        ).fetchall()
        exercices = conn.execute(
            '''SELECT intitule_exercice, reponse_utilisateur, correction, feedback, timestamp
               FROM exercices_historique
               WHERE user_uuid = ? ORDER BY timestamp DESC, id DESC''',
            (session['user_uuid'],),
        ).fetchall()
    return render_template('historique.html', traductions=traductions, exercices=exercices)

# =============================
# ROUTES - PAGES PRINCIPALES
# =============================

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/cours')
def cours():
    cours = load_cours()
    return render_template('cours.html', cours=cours)

@main_bp.route('/grammaire_3')
def grammaire_3():
    return render_template('grammaire_3.html')

@main_bp.route('/ia-trad')
def ia_trad():
    return render_template('IA-trad.html')

@main_bp.route('/obj_project')
def obj_project():
    return render_template('obj_project.html')

@main_bp.route('/commentaires', methods=['GET', 'POST'])
def commentaires():
    """Affiche et enregistre les retours publics des utilisateurs."""
    if request.method == 'POST':
        target_element = request.form.get('target_element', '').strip()
        content = request.form.get('content', '').strip()
        if target_element not in FEEDBACK_TARGETS or not content:
            return render_template(
                'commentaires.html',
                comments=[],
                targets=FEEDBACK_TARGETS,
                selected_target=target_element,
                selected_sort='recent',
                error='Sélectionnez un élément et rédigez un commentaire.',
            ), 400
        if len(content) > 2000:
            return render_template(
                'commentaires.html',
                comments=[],
                targets=FEEDBACK_TARGETS,
                selected_target=target_element,
                selected_sort='recent',
                error='Votre commentaire ne peut pas dépasser 2000 caractères.',
            ), 400

        with sqlite3.connect(DB_FILE) as conn:
            conn.execute(
                'INSERT INTO feedback (target_element, content, created_at) VALUES (?, ?, ?)',
                (target_element, content, datetime.now().isoformat(timespec='seconds')),
            )
            conn.commit()
        return redirect(url_for('main.commentaires'))

    with sqlite3.connect(DB_FILE) as conn:
        conn.row_factory = sqlite3.Row
        comments = conn.execute(
            'SELECT id, target_element, content, created_at, likes_count '
            'FROM feedback ORDER BY created_at DESC, id DESC'
        ).fetchall()

    return render_template(
        'commentaires.html',
        comments=comments,
        targets=FEEDBACK_TARGETS,
        selected_target='all',
        selected_sort='recent',
    )

@main_bp.route('/api/like_comment/<int:comment_id>', methods=['POST'])
def like_comment(comment_id):
    """Ajoute un like à un commentaire existant sans recharger la page."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute(
            'UPDATE feedback SET likes_count = likes_count + 1 WHERE id = ?',
            (comment_id,),
        )
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Commentaire introuvable'}), 404
        likes_count = conn.execute(
            'SELECT likes_count FROM feedback WHERE id = ?', (comment_id,)
        ).fetchone()[0]
        conn.commit()
    return jsonify({'success': True, 'likes_count': likes_count})

@main_bp.route('/api/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    """Supprime un commentaire après vérification du mot de passe admin."""
    payload = request.get_json(silent=True) or request.form
    password = str(payload.get('password', ''))
    admin_password = get_admin_password()
    if not admin_password:
        return jsonify({'success': False, 'error': 'Administration non configurée'}), 503
    if not hmac.compare_digest(password, admin_password):
        return jsonify({'success': False, 'error': 'Code incorrect'}), 403

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute('DELETE FROM feedback WHERE id = ?', (comment_id,))
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Commentaire introuvable'}), 404
        conn.commit()
    return jsonify({'success': True})

