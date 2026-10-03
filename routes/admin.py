import hmac
import os
import sqlite3
import sys
from threading import Timer

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for

from extensions import limiter
from services import gemini_service as service
from services.gemini_service import DB_FILE, get_admin_password, load_prompt, logger, require_admin, reset_gemini_runtime_state, warmup_gemini
from services.cache_service import refresh_content_caches

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/admin', methods=['GET', 'POST'])
@limiter.limit('5 per minute', methods=['POST'])
def admin():
    """Page d'administration principale (affiche login si non authentifié)."""
    admin_password = get_admin_password()

    if not admin_password:
        session.pop('admin_authenticated', None)
        return render_template(
            'admin_data.html',
            error='ADMIN_PASSWORD doit être défini dans l’environnement.',
            authenticated=False,
        ), 503

    if request.method == 'POST' and not session.get('admin_authenticated'):
        form_pw = request.form.get('admin_password', '')
        if form_pw and hmac.compare_digest(form_pw, admin_password):
            session['admin_authenticated'] = True
            return redirect(url_for('admin.admin'))
        else:
            return render_template('admin_data.html', error='Mot de passe incorrect', authenticated=False)

    # Si authentifié, afficher les données d'administration
    authenticated = bool(session.get('admin_authenticated'))

    # Charger les configs actuelles
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute('SELECT value FROM app_config WHERE key = ?', ('CACHED_CONTEXTS_ACTIVATION',))
            row = cur.fetchone()
            cached_flag = (row[0] == '1') if row else service.CACHED_CONTEXTS_ACTIVATION
            cur.execute('SELECT value FROM app_config WHERE key = ?', ('POOL_API_KEYS_ACTIVATION',))
            row = cur.fetchone()
            pool_flag = (row[0] == '1') if row else service.POOL_API_KEYS_ACTIVATION
            cur.execute('SELECT value FROM app_config WHERE key = ?', ('PAIEMENT_ACTIVE',))
            row = cur.fetchone()
            paiement_active = (row[0] == '1') if row else service.PAIEMENT_ACTIVE
            cur.execute('SELECT value FROM app_config WHERE key = ?', ('PRINT_GLOBAL_PROMPT',))
            row = cur.fetchone()
            print_global_prompt = (row[0] == '1') if row else service.PRINT_GLOBAL_PROMPT

            # Metrics: requêtes par jour (last 7 days)
            cur.execute("SELECT date(timestamp) as day, COUNT(*) FROM api_logs WHERE timestamp >= date('now','-6 days') GROUP BY day ORDER BY day DESC")
            per_day = cur.fetchall()

            # Metrics: requêtes par semaine
            cur.execute("SELECT strftime('%Y-%W', timestamp) as week, COUNT(*) FROM api_logs GROUP BY week ORDER BY week DESC LIMIT 8")
            per_week = cur.fetchall()

            # Répartition par provenance
            cur.execute('SELECT provenance, COUNT(*) FROM api_logs GROUP BY provenance')
            prov = cur.fetchall()

            # IP stats
            cur.execute('SELECT ip, visits, last_seen FROM ip_visits ORDER BY visits DESC LIMIT 200')
            ip_stats = cur.fetchall()

            # Translations pagination (strictly 10 rows per page)
            page = max(1, int(request.args.get('page', 1))) if request.args.get('page') else 1
            per_page = 10
            cur.execute('SELECT COUNT(*) FROM traductions')
            translation_count = cur.fetchone()[0]
            total_pages = max(1, (translation_count + per_page - 1) // per_page)
            page = min(page, total_pages)
            offset = (page - 1) * per_page
            cur.execute('SELECT id, input, output, date FROM traductions ORDER BY date DESC LIMIT ? OFFSET ?', (per_page, offset))
            translations = cur.fetchall()

            cur.execute('''
                SELECT user_uuid, source_text, target_text, direction, timestamp, traduction_fiable
                FROM traductions_historique ORDER BY timestamp DESC, id DESC LIMIT 200
            ''')
            user_translation_history = cur.fetchall()
            cur.execute('''
                SELECT user_uuid, intitule_exercice, reponse_utilisateur, correction, feedback, timestamp
                FROM exercices_historique ORDER BY timestamp DESC, id DESC LIMIT 200
            ''')
            exercise_history = cur.fetchall()

            # Recent API logs feed both the charts and the compact log table.
            cur.execute('''
                  SELECT timestamp, provenance, response_time_ms, status, tokens,
                      prompt_tokens, cached_tokens, response_tokens, traduction_fiable
                FROM api_logs ORDER BY timestamp DESC, id DESC LIMIT 100
            ''')
            api_logs = cur.fetchall()

    except Exception as exc:
        logger.error(f'Erreur lors du chargement des données admin: {exc}')
        return render_template(
            'admin_data.html',
            error='Erreur chargement BDD',
            authenticated=authenticated,
            paiement_active=service.PAIEMENT_ACTIVE,
        )

    return render_template(
        'admin_data.html',
        authenticated=authenticated,
        cached_flag=cached_flag,
        pool_flag=pool_flag,
        paiement_active=paiement_active,
        print_global_prompt=print_global_prompt,
        per_day=per_day,
        per_week=per_week,
        provenance_stats=prov,
        ip_stats=ip_stats,
        translations=translations,
        user_translation_history=user_translation_history,
        exercise_history=exercise_history,
        page=page,
        total_pages=total_pages,
        api_logs=api_logs,
    )


@admin_bp.route('/admin/toggle_config', methods=['POST'])
@limiter.limit('30 per minute')
@require_admin
def admin_toggle_config():
    key = request.form.get('key')
    val = request.form.get('value')
    if key not in ('CACHED_CONTEXTS_ACTIVATION', 'POOL_API_KEYS_ACTIVATION', 'PAIEMENT_ACTIVE', 'PRINT_GLOBAL_PROMPT'):
        return jsonify({'success': False, 'error': 'Clé invalide'}), 400
    v = '1' if val in ('1', 'true', 'True', 'on') else '0'
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute('INSERT OR REPLACE INTO app_config (key, value) VALUES (?, ?)', (key, v))
            conn.commit()
        setattr(service, key, (v == '1'))

        if key in ('PAIEMENT_ACTIVE', 'CACHED_CONTEXTS_ACTIVATION', 'PRINT_GLOBAL_PROMPT'):
            reset_gemini_runtime_state()
            warmup_gemini()

        return jsonify({'success': True, 'key': key, 'value': getattr(service, key)}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@admin_bp.route('/admin/shutdown', methods=['POST'])
@limiter.limit('5 per minute')
@require_admin
def admin_shutdown():
    """Arrête proprement le serveur Flask en mode admin uniquement."""
    def _do_shutdown():
        try:
            os._exit(0)
        except Exception:
            sys.exit(0)

    Timer(0.2, _do_shutdown).start()
    return jsonify({'success': True, 'message': 'Le serveur est en cours d\'arrêt.'}), 200


@admin_bp.route('/admin/refresh-content-cache', methods=['POST'])
@limiter.limit('5 per minute')
@require_admin
def admin_refresh_content_cache():
    """Invalidate lexicon and Obsidian caches after content changes."""
    refresh_content_caches()
    return jsonify({'success': True, 'message': 'Caches de contenu actualisés.'}), 200


@admin_bp.route('/admin/logout', methods=['POST'])
@limiter.limit('10 per minute')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin.admin'))


@admin_bp.route('/stats/optimisation', methods=['GET'])
@limiter.limit('30 per minute')
def stats_optimisation():
    """Retourne les statistiques de compression, d'optimisation et l'état du cache Gemini."""
    try:
        stats = {
            'prompt_sizes': {role: len(load_prompt(role)) for role in service.PROMPT_FILES},
            'total_context_size': sum(len(load_prompt(role)) for role in service.PROMPT_FILES),
            'api_keys_pool_size': len(service.API_KEYS_POOL),
            'active_key_index': service.CURRENT_KEY_INDEX if service.API_KEYS_POOL else None,
            'active_caches': len(service.GEMINI_CACHES),
        }

        return jsonify({
            'success': True,
            'stats': stats,
            'message': 'Les prompts complets sont générés par conlang-update.py et chargés depuis data/.',
        }), 200

    except Exception as exc:
        logger.error(f'Erreur dans /stats/optimisation: {exc}')
        return jsonify({
            'success': False,
            'erreur': str(exc),
        }), 500


# =============================
