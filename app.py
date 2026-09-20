"""
Application Flask pour l'Aënor.

Fournit :
    - un traducteur "maison" basé sur un dictionnaire local (modules.traducteur),
    - un traducteur assisté par l'API Gemini avec Context Caching (prompt système,
      grammaire et lexique mis en cache côté serveur Google pour réduire coûts et latence),
    - une rotation automatique sur un pool de clés API Gemini en cas de dépassement de quota,
    - des pages de cours, d'exercices interactifs et de scénarios.
"""

# =============================
# IMPORTS
# =============================

# --- Bibliothèque standard ---
import json
import hashlib
import hmac
import logging
import os
import re
import time
import warnings
import sqlite3
import uuid
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import subprocess
import sys
from threading import Timer
from pathlib import Path

# --- Bibliothèques tierces ---
from tenacity import retry, stop_after_attempt, wait_random_exponential
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from google import genai
from google.genai import types
from werkzeug.middleware.proxy_fix import ProxyFix

try:
    import google.generativeai as legacy_genai
except ImportError:
    legacy_genai = None

# --- Modules locaux ---
from modules.base_converter import process_aenor_numbers
from modules.exercices import get_random_phrase  # pour les exercices interactifs
from modules.utils import load_cours, render_cours_value, clean_text, get_path, static_path  # pour les cours


# =============================
# CODES ANSI (LOGS COLORÉS)
# =============================

RESET = '\033[0m'
BOLD = '\033[1m'
UNDERLINE = '\033[4m'


INVERTION = '\033[7m'

ROUGE = '\033[31m'
ORANGE = '\033[38;5;202m'
VERT = '\033[32m'
JAUNE = '\033[33m'
BLEU = '\033[34m'
MAGENTA = '\033[35m'
CYAN = '\033[36m'

# Ignore l'avertissement de dépréciation du SDK legacy (toujours utilisé en fallback)
warnings.filterwarnings(
    'ignore',
    message='All support for the `google.generativeai` package has ended.*',
    category=FutureWarning,
)


# =============================
# CONFIGURATION ET INITIALISATION
# =============================

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
app.config.update(
    DEBUG=False,
    PREFERRED_URL_SCHEME='https',
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)
app.jinja_env.filters['render_cours_value'] = render_cours_value
app.jinja_env.filters['clean_text'] = clean_text
app.jinja_env.globals['static_path'] = static_path
app.secret_key = os.environ.get('SECRET_KEY') or os.environ.get('FLASK_SECRET_KEY') or 'dev-only-change-this-secret-key'
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Contenus statiques chargés au démarrage ---
PROMPT_FILES = {
    'fr2aenor': '|dataPATH|prompt_trad_fr2ae',
    'aenor2fr': '|dataPATH|prompt_trad_ae2fr',
    'exercice': '|dataPATH|prompt_exercice',
}
COMMENT_PROMPT_FILES = {
    'fr2aenor': '|dataPATH|prompt_trad_fr2ae_comment',
    'aenor2fr': '|dataPATH|prompt_trad_ae2fr_comment',
}
REVISION_PROMPT_FILE = '|dataPATH|prompt_revision_traduction'
PROMPT_ALIASES = {
    **PROMPT_FILES,
    **{alias: alias for alias in COMMENT_PROMPT_FILES.values()},
    'revision': REVISION_PROMPT_FILE,
}
PROMPT_CONTENTS: Dict[str, str] = {}
PROMPT_SIGNATURES: Dict[str, str] = {}

# --- Configuration du modèle Gemini ---
# Remarque : la sélection du modèle dépend dynamiquement du flag PAIEMENT_ACTIVE.
# Lorsque PAIEMENT_ACTIVE == True -> modèles payants (2.5)
# Lorsque PAIEMENT_ACTIVE == False -> modèles recommandés (3.6)
GEMINI_MODEL = 'gemini-3.6-flash'              # Valeur par défaut (utilisée quand PAIEMENT_ACTIVE=False)
GEMINI_MODEL_LEGACY = 'gemini-3.5-flash-lite'  # Valeur legacy par défaut

def get_current_models():
    """Retourne un tuple (model_principal, model_fallback) selon l'état de PAIEMENT_ACTIVE."""
    # Mode Pay-as-you-go activé -> utiliser la famille 2.5 (payante)
    if PAIEMENT_ACTIVE:
        return ('gemini-2.5-flash', 'gemini-2.5-flash-lite')
    # Mode désactivé -> utiliser la famille 3.6
    return (GEMINI_MODEL, 'gemini-3.5-flash-lite')

"""
CACHE_TTL_SECONDS : le stockage du cache Gemini est facturé ~1,00 $ / 1M tokens / heure, en continu
tant que le cache existe, indépendamment du nombre de requêtes. Pour un contexte volumineux mais un
faible nombre de requêtes/jour, un TTL long (ex. 3600s) fait payer du stockage inactif la majeure
partie du temps. Un TTL court limite ce coût de stockage tout en couvrant encore les cas réels où
plusieurs requêtes s'enchaînent en quelques minutes (l'utilisateur traduit plusieurs phrases de
suite) : la lecture du cache reste ~10x moins chère que l'envoi du contexte complet dans ce cas.
600s (10 min) est le compromis retenu : au pire (aucune requête rapprochée, le cache est recréé à
chaque fois), le stockage cumulé reste largement sous le seuil de rentabilité vs. envoi direct du
contexte ; au mieux (requêtes groupées), on profite pleinement de la remise de -90% sur la lecture.
"""

CACHE_TTL_SECONDS = 600
CACHE_REFRESH_MARGIN_SECONDS = 150  # Marge avant expiration pour tenter une prolongation (caches.update) plutôt qu'une recréation


# ===========================================================================
# --- Flags d'activation (configuration financière / fonctionnelle) ---------
CACHED_CONTEXTS_ACTIVATION = False

POOL_API_KEYS_ACTIVATION = True     # False : utilise uniquement la première clé API disponible
                                    #          (GEMINI_API_KEY_1, ou GEMINI_API_KEY / GOOGLE_API_KEY),
                                    #          sans rotation automatique en cas de quota dépassé.

PAIEMENT_ACTIVE = False             # False : utilise les clés standard gratuites
                                    # True  : utilise les clés payantes (env vars préfixées par €)


# Note : Si CACHED_CONTEXTS_ACTIVATION = True, alors il est préférable financièrement 
# de mettre POOL_API_KEYS_ACTIVATION = False pour ne pas générer un context cache par clé.

# ---------------------------------------------------------------------------
# ===========================================================================


# --- Pool de clés API et rotation ---
API_KEYS_POOL: List[str] = []
CURRENT_KEY_INDEX = 0

# --- Clients et caches Gemini ---
CLIENTS_BY_KEY: Dict[str, object] = {}
# GEMINI_CACHES / CACHE_EXPIRATIONS sont indexés par (api_key, direction) : chaque sens de
# traduction ('fr2aenor' / 'aenor2fr') dispose ainsi de son propre cache Gemini distinct,
# au lieu de partager (et donc d'écraser) le même cache pour une clé API donnée.
CacheKey = Tuple[str, str, str]
GEMINI_CACHES: Dict[CacheKey, object] = {}
CACHE_EXPIRATIONS: Dict[CacheKey, float] = {}
LEGACY_CONFIGURED_KEY: Optional[str] = None  # Dernière clé utilisée pour configurer le SDK legacy

# --- Pour l'enregistrment des traductions ---
PROJECT_ROOT = Path(__file__).resolve().parent
DB_FILE = PROJECT_ROOT / 'data' / 'SQLite.db'

FEEDBACK_TARGETS = (
    'Grammaire',
    'Lexique',
    'Traducteur',
    'Interface',
    'Exercices',
    'Problèmes techniques',
    'Autre',
)

PRINT_GLOBAL_PROMPT = False


# =============================
# FONCTIONS UTILITAIRES
# =============================

def prompt_path(role: str) -> str:
    """Retourne le chemin absolu d'un prompt logique ou d'un alias de chemin."""
    filename = PROMPT_ALIASES.get(role, role if role in PROMPT_ALIASES.values() else None)
    if not filename:
        raise ValueError(f'Rôle de prompt inconnu: {role}')
    return str(get_path(filename))


def load_prompt(role: str) -> str:
    """Charge un prompt complet et invalide son cache local s'il a changé."""
    path = prompt_path(role)
    try:
        with open(path, 'r', encoding='utf-8') as handle:
            content = handle.read()
    except OSError as exc:
        logger.error(f'Prompt introuvable ({path}): {exc}')
        return ''

    signature = hashlib.sha256(content.encode('utf-8')).hexdigest()
    if PROMPT_SIGNATURES.get(role) not in (None, signature):
        for cache_key in list(GEMINI_CACHES):
            if cache_key[1] == role:
                GEMINI_CACHES.pop(cache_key, None)
                CACHE_EXPIRATIONS.pop(cache_key, None)
        logger.info(f'{CYAN}ℹ Prompt modifié, cache invalidé: {role}{RESET}')
    PROMPT_SIGNATURES[role] = signature
    PROMPT_CONTENTS[role] = content
    return content


def separer_traduction_commentaire(texte: str) -> Tuple[str, str]:
    """Sépare une réponse pédagogique encadrée par deux délimiteurs `|@|`."""
    morceaux = texte.split('|@|')
    if len(morceaux) != 3:
        return texte.strip(), ''
    return morceaux[0].strip(), morceaux[1].strip()


def enregistrer_traduction_commentaire(source: str, traduction: str, commentaire: str) -> None:
    """Ajoute une traduction pédagogique au fichier JSON dédié."""
    chemin = get_path('|dataPATH|traductions_commentaires')
    try:
        donnees = json.loads(chemin.read_text(encoding='utf-8')) if chemin.exists() else []
        if not isinstance(donnees, list):
            donnees = []
        donnees.append({
            'source': source,
            'traduction': traduction,
            'commentaire': commentaire,
            'date': datetime.now().isoformat(timespec='seconds'),
        })
        chemin.write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    except (OSError, json.JSONDecodeError) as exc:
        logger.error(f'❌ Impossible de sauvegarder le commentaire pédagogique : {exc}')


def get_api_keys_pool() -> List[str]:
    """
    Récupère l'ensemble des clés API Gemini configurées dans l'environnement,
    dans l'ordre de priorité, sans doublons.
    """
    keys: List[str] = []
    if PAIEMENT_ACTIVE:
        candidates = (
            '€GEMINI_API_KEY_1',
            '€GEMINI_API_KEY_2',
            '€GEMINI_API_KEY_3',
            '€GEMINI_API_KEY',
            '€GOOGLE_API_KEY',
        )
    else:
        candidates = (
            'GEMINI_API_KEY_1',
            'GEMINI_API_KEY_2',
            'GEMINI_API_KEY_3',
            'GEMINI_API_KEY',
            'GOOGLE_API_KEY',
        )

    for env_name in candidates:
        value = os.getenv(env_name)
        if value and value.strip() and value.strip() not in keys:
            keys.append(value.strip())

    if not keys and PAIEMENT_ACTIVE:
        legacy_candidates = (
            'GEMINI_API_KEY_1',
            'GEMINI_API_KEY_2',
            'GEMINI_API_KEY_3',
            'GEMINI_API_KEY',
            'GOOGLE_API_KEY',
        )
        for env_name in legacy_candidates:
            value = os.getenv(env_name)
            if value and value.strip() and value.strip() not in keys:
                keys.append(value.strip())

    return keys


def reset_gemini_runtime_state() -> None:
    """Réinitialise le pool actif, les clients et les caches Gemini."""
    global API_KEYS_POOL, CURRENT_KEY_INDEX, CLIENTS_BY_KEY, GEMINI_CACHES, CACHE_EXPIRATIONS, LEGACY_CONFIGURED_KEY
    API_KEYS_POOL = get_api_keys_pool()
    CURRENT_KEY_INDEX = 0
    CLIENTS_BY_KEY.clear()
    GEMINI_CACHES.clear()
    CACHE_EXPIRATIONS.clear()
    LEGACY_CONFIGURED_KEY = None
    logger.info(
        f'{CYAN}ℹ️ Pool Gemini rechargé ({len(API_KEYS_POOL)} clé(s), mode payant={PAIEMENT_ACTIVE}){RESET}'
    )


def _mask_key(api_key: Optional[str]) -> str:
    """Masque une clé API pour les logs, en n'affichant que ses 4 derniers caractères."""
    if not api_key:
        return '????'
    return api_key[-4:]


# =============================
# CHARGEMENT DES FICHIERS AU DÉMARRAGE
# =============================

def create_cached_context(direction: str = 'fr2aenor') -> Optional[str]:
    """Charge le fichier de prompt complet utilisé comme contexte Gemini."""
    context = load_prompt(direction)
    if context:
        logger.info(f'{VERT}✓ Prompt chargé pour {direction} ({len(context)} caractères){RESET}')
    return context or None

def init_db():
    """Initialise la base de données SQLite et crée la table si elle n'existe pas."""
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # On crée les colonnes : id (auto), input (fr), output (aenor) et date
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traductions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input TEXT NOT NULL,
                output TEXT NOT NULL,
                date TEXT NOT NULL
            )
        ''')
        # Table pour journaliser les appels API Gemini
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS api_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                provenance TEXT NOT NULL,
                tokens INTEGER,
                ip TEXT,
                response_time_ms REAL
            )
        ''')
        existing_columns = {
            row[1] for row in cursor.execute('PRAGMA table_info(api_logs)').fetchall()
        }
        for column_name, column_type in (
            ('response_time_ms', 'REAL'),
            ('prompt_tokens', 'INTEGER'),
            ('cached_tokens', 'INTEGER'),
            ('response_tokens', 'INTEGER'),
            ('status', "TEXT NOT NULL DEFAULT 'success'"),
            ('traduction_fiable', 'INTEGER NOT NULL DEFAULT 0'),
        ):
            if column_name not in existing_columns:
                cursor.execute(f'ALTER TABLE api_logs ADD COLUMN {column_name} {column_type}')

        # Table pour statistiques IP (agrégat rapide)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS ip_visits (
                ip TEXT PRIMARY KEY,
                visits INTEGER NOT NULL,
                last_seen TEXT NOT NULL
            )
        ''')

        # Table pour stocker des configurations persistantes modifiables via l'admin
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS app_config (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                target_element TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL,
                likes_count INTEGER NOT NULL DEFAULT 0
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS traductions_historique (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_uuid TEXT NOT NULL,
                source_text TEXT NOT NULL,
                target_text TEXT NOT NULL,
                direction TEXT NOT NULL CHECK (direction IN ('ae2fr', 'fr2ae')),
                timestamp TEXT NOT NULL,
                traduction_fiable INTEGER NOT NULL DEFAULT 0
            )
        ''')
        existing_history_columns = {
            row[1] for row in cursor.execute('PRAGMA table_info(traductions_historique)').fetchall()
        }
        if 'traduction_fiable' not in existing_history_columns:
            cursor.execute(
                'ALTER TABLE traductions_historique '
                'ADD COLUMN traduction_fiable INTEGER NOT NULL DEFAULT 0'
            )
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS exercices_historique (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_uuid TEXT NOT NULL,
                intitule_exercice TEXT NOT NULL,
                reponse_utilisateur TEXT NOT NULL,
                correction TEXT NOT NULL,
                note INTEGER,
                feedback TEXT,
                timestamp TEXT NOT NULL
            )
        ''')

        # Insérer valeurs par défaut si absentes
        cursor.execute('INSERT OR IGNORE INTO app_config (key, value) VALUES (?, ?)', ('CACHED_CONTEXTS_ACTIVATION', '1'))
        cursor.execute('INSERT OR IGNORE INTO app_config (key, value) VALUES (?, ?)', ('POOL_API_KEYS_ACTIVATION', '1'))
        cursor.execute('INSERT OR IGNORE INTO app_config (key, value) VALUES (?, ?)', ('PAIEMENT_ACTIVE', '0'))
        cursor.execute('INSERT OR IGNORE INTO app_config (key, value) VALUES (?, ?)', ('PRINT_GLOBAL_PROMPT', '0'))
        conn.commit()

def load_files_at_startup() -> None:
    """Charge les prompts générés et prépare Gemini."""
    init_db()
    global API_KEYS_POOL
    try:
        for role in PROMPT_FILES:
            if not load_prompt(role):
                raise FileNotFoundError(prompt_path(role))

        # Charger configurations persistantes depuis la BDD avant le warmup Gemini
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute('SELECT key, value FROM app_config')
            for key, value in cur.fetchall():
                if key in ('CACHED_CONTEXTS_ACTIVATION', 'POOL_API_KEYS_ACTIVATION', 'PAIEMENT_ACTIVE', 'PRINT_GLOBAL_PROMPT'):
                    globals()[key] = (value == '1')

        reset_gemini_runtime_state()
        warmup_gemini()

    except Exception as exc:
        logger.error(f'❌ Erreur lors du chargement des fichiers: {exc}')


# =============================
# CLIENT GEMINI & ROTATION DE CLÉS
# =============================

def get_current_api_key() -> Optional[str]:
    """Retourne la clé API actuellement active dans le pool de rotation."""
    if not API_KEYS_POOL:
        return None
    return API_KEYS_POOL[CURRENT_KEY_INDEX % len(API_KEYS_POOL)]


def rotate_api_key() -> Optional[str]:
    """Passe à la clé API suivante du pool (rotation circulaire) et la retourne.

    Si POOL_API_KEYS_ACTIVATION est False, la rotation est un no-op : la clé
    actuelle (index 0, donc la première clé disponible) est conservée telle quelle.
    """
    global CURRENT_KEY_INDEX

    if not API_KEYS_POOL:
        return None

    if not POOL_API_KEYS_ACTIVATION:
        logger.info(
            f'{JAUNE}ℹ️ Rotation de clé désactivée (POOL_API_KEYS_ACTIVATION=False) : '
            f'la clé actuelle est conservée.{RESET}'
        )
        return get_current_api_key()

    CURRENT_KEY_INDEX = (CURRENT_KEY_INDEX + 1) % len(API_KEYS_POOL)
    logger.warning(
        f'{JAUNE}⟳ Rotation vers la clé API #{CURRENT_KEY_INDEX + 1}/{len(API_KEYS_POOL)}{RESET}'
    )
    return get_current_api_key()


def get_gemini_client(api_key: Optional[str]):
    """
    Retourne le client officiel `google-genai` associé à une clé API, en le créant
    et en le mettant en cache si nécessaire (pour éviter les ré-instanciations coûteuses).
    """
    if not api_key:
        return None

    if api_key in CLIENTS_BY_KEY:
        return CLIENTS_BY_KEY[api_key]

    try:
        client = genai.Client(api_key=api_key)
        CLIENTS_BY_KEY[api_key] = client
        logger.info(f'{VERT}✓ Client Gemini officiel initialisé (clé ...{_mask_key(api_key)}){RESET}')
        return client
    except Exception as exc:
        logger.warning(f'{ROUGE}⚠ Configuration du SDK officiel impossible: {exc}{RESET}')
        return None


def get_legacy_client(api_key: Optional[str]):
    """Configure (si nécessaire) et retourne le SDK legacy `google.generativeai`, utilisé en dernier recours."""
    global LEGACY_CONFIGURED_KEY

    if legacy_genai is None or not api_key:
        return None

    if LEGACY_CONFIGURED_KEY != api_key:
        try:
            legacy_genai.configure(api_key=api_key)
            LEGACY_CONFIGURED_KEY = api_key
            logger.info(f'{VERT}✓ Client Gemini legacy configuré (clé ...{_mask_key(api_key)}){RESET}')
        except Exception as exc:
            logger.warning(f'⚠ Configuration du SDK legacy impossible: {exc}')
            return None

    return legacy_genai


def is_quota_error(exc: Exception) -> bool:
    """Détecte si une exception correspond à un dépassement de quota / de débit."""
    message = str(exc).lower()
    status_code = getattr(exc, 'code', None) or getattr(exc, 'status_code', None)
    return (
        status_code == 429
        or 'quota' in message
        or 'resource_exhausted' in message
        or 'rate limit' in message
    )


# =============================
# CONTEXT CACHING GEMINI
# =============================

def get_or_create_cache(client, api_key: str, direction: str, context: str):
    """
    Récupère le cache Gemini associé à une clé API ET à un sens de traduction donné,
    en le créant (ou en prolongeant son TTL) si nécessaire.

    La clé de cache est composée de (api_key, direction) : 'fr2aenor' et 'aenor2fr'
    ont donc chacun leur propre cache Gemini distinct, même pour une même clé API.

    Si CACHED_CONTEXTS_ACTIVATION est False, retourne toujours None sans effectuer
    aucun appel réseau : le contexte complet sera alors envoyé directement dans
    chaque requête (voir prompt_fallback dans traduire_avec_gemini()).
    """
    if not CACHED_CONTEXTS_ACTIVATION:
        return None

    if not context or client is None:
        return None

    cache_key: CacheKey = (api_key, direction, get_current_models()[0])
    now = time.time()
    cached = GEMINI_CACHES.get(cache_key)
    expiration = CACHE_EXPIRATIONS.get(cache_key)

    # Cache encore largement valide : on le réutilise tel quel, sans aucun appel réseau.
    if cached is not None and expiration is not None and now < (expiration - CACHE_REFRESH_MARGIN_SECONDS):
        return cached

    if not hasattr(client, 'caches') or not hasattr(client.caches, 'create'):
        return None

    # Cache existant mais proche de l'expiration (ou déjà expiré localement) :
    # on tente de PROLONGER son TTL côté Gemini plutôt que de le jeter et d'en recréer un.
    if cached is not None and hasattr(client.caches, 'update'):
        try:
            updated_cache = client.caches.update(
                name=getattr(cached, 'name', None),
                config=types.UpdateCachedContentConfig(ttl=f'{CACHE_TTL_SECONDS}s'),
            )
            if updated_cache is not None:
                GEMINI_CACHES[cache_key] = updated_cache
                CACHE_EXPIRATIONS[cache_key] = now + CACHE_TTL_SECONDS
                logger.info(
                    f'{VERT}✓ TTL du cache Gemini prolongé: {getattr(updated_cache, "name", "inconnu")} '
                    f'(clé ...{_mask_key(api_key)}, direction={direction}){RESET}'
                )
                return updated_cache
        except Exception as exc:
            # Le cache a probablement déjà expiré côté serveur (ou une autre erreur est survenue) :
            # on bascule sur la création d'un nouveau cache ci-dessous.
            logger.info(
                f'{JAUNE}ℹ️ Impossible de prolonger le cache existant (direction={direction}), '
                f'création d\'un nouveau cache. Détail: {exc}{RESET}'
            )

    try:
        cache_config = types.CreateCachedContentConfig(
            display_name=f'aenor-context-cache-{direction}',
            ttl=f'{CACHE_TTL_SECONDS}s',
            system_instruction=context,
        )
        cache = client.caches.create(model=get_current_models()[0], config=cache_config)

        if cache is not None:
            GEMINI_CACHES[cache_key] = cache
            CACHE_EXPIRATIONS[cache_key] = now + CACHE_TTL_SECONDS
            logger.info(
                f'{VERT}✓ Cache Gemini créé: {getattr(cache, "name", "inconnu")} '
                f'(clé ...{_mask_key(api_key)}, direction={direction}){RESET}'
            )
            return cache

    except Exception as exc:
        # On journalise désormais le détail réel de l'exception pour pouvoir diagnostiquer
        # une éventuelle limitation (Free Tier, seuil minimal de tokens, quota, etc.).
        logger.warning(
            f'{ORANGE}⚠ Cache Gemini non fonctionnel (direction={direction}), les requêtes '
            f'classiques vont donc être utilisées. Détail: {exc}{RESET}'
        )

    return None

def warmup_gemini() -> None:
    """
    Prépare le client Gemini et le cache de contexte dès le démarrage de l'application,
    afin que la toute première requête utilisateur bénéficie déjà du Context Caching
    (au lieu de payer le coût de création du cache sur la requête utilisateur).
    """
    if not API_KEYS_POOL:
        logger.warning(
            f'{ROUGE}⚠ Aucune clé API Gemini trouvée '
            f'(GEMINI_API_KEY_1/2/3, GEMINI_API_KEY ou GOOGLE_API_KEY){RESET}'
        )
        return

    logger.info(f'{CYAN}ℹ Pool de clés API Gemini: {UNDERLINE}{len(API_KEYS_POOL)} clé(s) disponible(s) '
                f'(rotation {"activée" if POOL_API_KEYS_ACTIVATION else "désactivée"}){RESET}')

    if not CACHED_CONTEXTS_ACTIVATION:
        logger.info(
            f'{CYAN}ℹ Context Caching désactivé (CACHED_CONTEXTS_ACTIVATION=False) : '
            f'le contexte complet sera envoyé à chaque requête, warmup ignoré.{RESET}'
        )
        return

    api_key = get_current_api_key()
    client = get_gemini_client(api_key)
    if client is not None:
        for direction in PROMPT_FILES:
            context = load_prompt(direction)
            if context:
                get_or_create_cache(client, api_key, direction, context)

def _get_token_count(response) -> Optional[int]:
    """Calcule le nombre de tokens facturables d'une réponse Gemini."""
    usage = getattr(response, 'usage_metadata', None)
    if not usage:
        return None

    try:
        cached_tokens = getattr(usage, 'cached_content_token_count', 0) or 0
        prompt_tokens = getattr(usage, 'prompt_token_count', 0) or 0
        response_tokens = getattr(usage, 'candidates_token_count', 0) or 0
        return int((prompt_tokens - cached_tokens) + response_tokens)
    except (TypeError, ValueError):
        return None


def _get_token_usage(response) -> Tuple[Optional[int], Optional[int], Optional[int]]:
    """Retourne les compteurs prompt, cache et réponse d'un appel Gemini."""
    usage = getattr(response, 'usage_metadata', None)
    if not usage:
        return None, None, None

    try:
        return (
            int(getattr(usage, 'prompt_token_count', 0) or 0),
            int(getattr(usage, 'cached_content_token_count', 0) or 0),
            int(getattr(usage, 'candidates_token_count', 0) or 0),
        )
    except (TypeError, ValueError):
        return None, None, None


def _get_request_ip() -> Optional[str]:
    try:
        return request.remote_addr if request else None
    except RuntimeError:
        return None


def _log_token_usage(response, response_time_ms: Optional[float] = None) -> None:
    """Affiche les tokens et la latence d'un appel Gemini dans les logs."""
    usage = getattr(response, 'usage_metadata', None)
    
    # Si la réponse n'a pas de métadonnées d'usage
    if not usage:
        logger.info(
            f'{JAUNE}| Latence Gemini: {response_time_ms / 1000:.2f} s |{RESET}'
            if response_time_ms is not None else
            f'{JAUNE}| Latence Gemini: inconnue |{RESET}'
        )
        return

    cached_tokens = getattr(usage, 'cached_content_token_count', 0) or 0
    logger.info(f'{JAUNE}+----------------------------+----------+-------------+{RESET}')
    logger.info(
        f'{JAUNE}|📊 TOKENS -> Prompt: {BOLD}{ORANGE}{usage.prompt_token_count} {RESET} '
        f'{JAUNE}| Cache: {RESET}{ROUGE}{BOLD}{cached_tokens}{RESET} '
        f'{JAUNE}| Réponse: {BOLD}{usage.candidates_token_count} |{RESET} '
        f'{JAUNE}Latence: {BOLD}{response_time_ms / 1000:.2f} s{RESET}'
        if response_time_ms is not None else
        f'{JAUNE}| Réponse: {BOLD}{usage.candidates_token_count} |{RESET} '
        f'{JAUNE}Latence: inconnue{RESET}'
    )
    logger.info(f'{JAUNE}+----------------------------+----------+-------------+{RESET}')


def _call_gemini_with_latency(generate_content, provenance: str, traduction_fiable: bool = False):
    """Exécute un appel Gemini et journalise sa durée, succès ou exception comprise."""
    response = None
    started_at = time.perf_counter()
    try:
        response = generate_content()
        return response
    finally:
        response_time_ms = (time.perf_counter() - started_at) * 1000
        _log_token_usage(response, response_time_ms)
        prompt_tokens, cached_tokens, response_tokens = _get_token_usage(response)
        insert_api_log(
            provenance,
            _get_token_count(response),
            _get_request_ip(),
            response_time_ms,
            prompt_tokens,
            cached_tokens,
            response_tokens,
            'success' if response is not None else 'error',
            traduction_fiable,
        )


def _print_global_prompt(role: str, prompt: str) -> None:
    """Affiche le fichier source et le prompt logique complet si demandé par l'admin."""
    if not PRINT_GLOBAL_PROMPT:
        return
    print(f'\n===== PROMPT GEMINI: {role} =====')


# =============================
# FONCTION DE TRADUCTION AVEC GEMINI
# =============================

def reviser_traduction_avec_gemini(
    texte_source: str,
    traduction_proposee: str,
    direction: str,
    autoriser_apprentissage: bool,
    provenance: str,
) -> str:
    """Fait verifier la traduction initiale par Gemini et retourne la version finale."""
    contexte_traduction = load_prompt(
        COMMENT_PROMPT_FILES[direction] if autoriser_apprentissage else direction
    )
    prompt_revision = load_prompt('revision')
    if not contexte_traduction or not prompt_revision:
        raise RuntimeError('Contexte de revision introuvable')

    demande = (
        f'{prompt_revision.rstrip()}\n\n'
        f'Phrase source :\n{texte_source}\n\n'
        f'Traduction proposee :\n{traduction_proposee}\n\n'
        f'Sens de traduction : {direction}\n'
        f'Mode apprentissage : {"oui" if autoriser_apprentissage else "non"}'
    )
    prompt_complet = f'{contexte_traduction.rstrip()}\n\n{demande}'
    _print_global_prompt('revision', prompt_complet)

    erreurs: List[str] = []
    nb_tentatives = len(API_KEYS_POOL) if POOL_API_KEYS_ACTIVATION else 1
    for _ in range(nb_tentatives):
        api_key = get_current_api_key()
        client = get_gemini_client(api_key)
        if client is None or not hasattr(client, 'models') or not hasattr(client.models, 'generate_content'):
            break
        try:
            response = _call_gemini_with_latency(
                lambda: client.models.generate_content(
                    model=get_current_models()[0],
                    contents=prompt_complet,
                ),
                f'{provenance}_revision',
                True,
            )
            return getattr(response, 'text', str(response)).strip()
        except Exception as exc:
            erreurs.append(str(exc))
            if is_quota_error(exc):
                rotate_api_key()
                continue
            break

    legacy_client = get_legacy_client(get_current_api_key())
    if legacy_client is not None and hasattr(legacy_client, 'GenerativeModel'):
        try:
            model = legacy_client.GenerativeModel(GEMINI_MODEL_LEGACY)
            response = _call_gemini_with_latency(
                lambda: model.generate_content(prompt_complet),
                f'{provenance}_revision',
                True,
            )
            return getattr(response, 'text', str(response)).strip()
        except Exception as exc:
            erreurs.append(str(exc))

    detail = '; '.join(erreurs) or 'raison inconnue'
    raise RuntimeError(f'Impossible de verifier la traduction ({detail})')

def traduire_avec_gemini(
    texte_utilisateur: str,
    direction: str = 'fr2aenor',
    provenance: str = 'autre',
    autoriser_apprentissage: bool = False,
    traduction_fiable: bool = False,
) -> Tuple[str, str]:
    """
    Traduit un texte via l'API Gemini.

    Stratégie :
        1. Réutilise (ou crée) un cache de contexte Gemini pour la clé API active,
           afin de ne pas renvoyer le prompt système, la grammaire et le lexique
           à chaque requête (Context Caching).
        2. En cas de dépassement de quota sur une clé, effectue une rotation
           automatique vers la clé suivante du pool et retente l'appel.
        3. Si le SDK officiel échoue pour toute autre raison, ou si aucune clé
           n'est fonctionnelle, retombe sur le SDK legacy `google.generativeai`.

    L'enregistrement de la traduction (sauvegarder_traduction) n'est déclenché
    que lorsqu'une traduction a effectivement été générée avec succès par
    Gemini (SDK officiel ou fallback legacy) — jamais en cas d'erreur.
    """
    prompt_role = direction if not autoriser_apprentissage else COMMENT_PROMPT_FILES[direction]
    context = load_prompt(prompt_role)
    if not context:
        return "Erreur : le contexte de traduction n'a pas pu être construit.", ''

    if not API_KEYS_POOL:
        return (
            "Erreur : aucune clé API Gemini n'a été configurée. "
            "Définissez GEMINI_API_KEY_1/2/3, GEMINI_API_KEY ou GOOGLE_API_KEY."
        ), ''

    prompt_fallback = f'{context.rstrip()}\n\n{texte_utilisateur}'
    _print_global_prompt(direction, prompt_fallback)

    erreurs_rencontrees: List[str] = []

    # On tente chaque clé du pool au maximum une fois, avec rotation en cas de quota dépassé.
    # Si POOL_API_KEYS_ACTIVATION est False, une seule tentative est faite (avec la première
    # clé disponible) : rotate_api_key() ne changeant plus d'index, retenter en boucle ne
    # servirait qu'à réessayer inutilement la même clé.
    nb_tentatives = len(API_KEYS_POOL) if POOL_API_KEYS_ACTIVATION else 1
    for _ in range(nb_tentatives):
        api_key = get_current_api_key()
        client = get_gemini_client(api_key)

        if client is None or not hasattr(client, 'models') or not hasattr(client.models, 'generate_content'):
            break  # Client officiel indisponible : on passe directement au fallback legacy

        try:
            cache = get_or_create_cache(client, api_key, prompt_role, context)

            if cache is not None and getattr(cache, 'name', None):
                response = _call_gemini_with_latency(
                    lambda: client.models.generate_content(
                        model=get_current_models()[0],
                        contents=texte_utilisateur,
                        config=types.GenerateContentConfig(cached_content=cache.name),
                    ),
                    provenance,
                )
            else:
                response = _call_gemini_with_latency(
                    lambda: client.models.generate_content(
                        model=get_current_models()[0],
                        contents=prompt_fallback,
                    ),
                    provenance,
                )


            # On récupère le texte brut de Gemini
            traduction_brute = getattr(response, 'text', str(response))

            if traduction_fiable:
                traduction_brute = reviser_traduction_avec_gemini(
                    texte_utilisateur,
                    traduction_brute,
                    direction,
                    autoriser_apprentissage,
                    provenance,
                )
            
            # --- APPLICATION DU FILTRE BASE 12 ICI ---
            traduction, commentaire = separer_traduction_commentaire(traduction_brute) if autoriser_apprentissage else (traduction_brute.strip(), '')
            traduction = process_aenor_numbers(traduction)
            # -----------------------------------------
            
            enregistrer_mots_non_traduits(traduction)
            # Sauvegarde en fonction du sens : sauvegarder_traduction(francais, aenor)
            sauvegarder_traduction(texte_utilisateur, traduction, direction, traduction_fiable)
            if autoriser_apprentissage:
                enregistrer_traduction_commentaire(texte_utilisateur, traduction, commentaire)
            return traduction, commentaire


        except Exception as exc:
            erreurs_rencontrees.append(str(exc))

            if is_quota_error(exc):
                logger.warning(
                    f'{JAUNE}⚠ Quota dépassé pour la clé ...{_mask_key(api_key)}, rotation...{RESET}'
                )
                rotate_api_key()
                continue

            logger.warning(f'⚠ Erreur avec le SDK officiel: {exc}')
            break  # Erreur non liée au quota : inutile de changer de clé

    # Fallback : SDK legacy (google.generativeai)
    legacy_key = get_current_api_key()
    legacy_client = get_legacy_client(legacy_key)

    if legacy_client is not None and hasattr(legacy_client, 'GenerativeModel'):
        try:
            model = legacy_client.GenerativeModel(GEMINI_MODEL_LEGACY)
            response = _call_gemini_with_latency(
                lambda: model.generate_content(prompt_fallback),
                provenance,
            )
            
            # On récupère le texte brut de Gemini
            traduction_brute = getattr(response, 'text', str(response))

            if traduction_fiable:
                traduction_brute = reviser_traduction_avec_gemini(
                    texte_utilisateur,
                    traduction_brute,
                    direction,
                    autoriser_apprentissage,
                    provenance,
                )
            
            # --- APPLICATION DU FILTRE BASE 12 ICI ---
            traduction, commentaire = separer_traduction_commentaire(traduction_brute) if autoriser_apprentissage else (traduction_brute.strip(), '')
            traduction = process_aenor_numbers(traduction)
            # -----------------------------------------
            
            # Le fallback legacy n'utilise pas de cache (aucun cached_content transmis),
            # mais on journalise quand même prompt/réponse pour garder une visibilité complète.
            enregistrer_mots_non_traduits(traduction)
            sauvegarder_traduction(texte_utilisateur, traduction, direction, traduction_fiable)
            if autoriser_apprentissage:
                enregistrer_traduction_commentaire(texte_utilisateur, traduction, commentaire)
            return traduction, commentaire
        
        except Exception as exc:
            erreurs_rencontrees.append(str(exc))
            logger.error(f'❌ Échec du fallback legacy: {exc}')

    logger.error(f'❌ Toutes les tentatives de traduction ont échoué: {erreurs_rencontrees}')
    detail = '; '.join(erreurs_rencontrees) or 'raison inconnue'
    return f'Erreur : Impossible de générer la traduction. ({detail})', ''

def enregistrer_mots_non_traduits(texte_traduit: str) -> None:
    """
    Détecte les mots laissés non traduits par Gemini (au format `{EXEMPLE}`)
    et met à jour leur compteur d'occurrences dans `data/non_traduits.json`.
    """
    motifs = re.findall(r'\{([A-ZÂÄÉÈÊËÎÏÔÖÙÛÜÇ]+)\}', texte_traduit)
    if not motifs:
        return

    chemin_fichier = str(get_path('|dataPATH|non_traduits'))

    if os.path.exists(chemin_fichier):
        try:
            with open(chemin_fichier, 'r', encoding='utf-8') as handle:
                donnees = json.load(handle)
        except Exception:
            donnees = {}
    else:
        donnees = {}

    for mot in motifs:
        mot = mot.strip()
        donnees[mot] = donnees.get(mot, 0) + 1

    try:
        with open(chemin_fichier, 'w', encoding='utf-8') as handle:
            json.dump(donnees, handle, ensure_ascii=False, indent=4)
        logger.info(f'📝 {VERT}{len(motifs)} mot(s) non traduit(s) enregistré(s) ou mis à jour.{RESET}')
    except Exception as exc:
        logger.error(f'❌ Impossible de sauvegarder les mots non traduits : {exc}')


def sauvegarder_traduction(francais, aenor, direction='fr2aenor', traduction_fiable=False):
    """
    Enregistre une traduction générée par l'API Gemini dans la base SQLite.
    """
    date_actuelle = datetime.now().isoformat(timespec="seconds")

    try:
        # On se connecte à la base (le bloc 'with' gère la fermeture automatique)
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            # On insère une nouvelle ligne (les ? évitent les failles d'injection)
            cursor.execute(
                "INSERT INTO traductions (input, output, date) VALUES (?, ?, ?)",
                (francais, aenor, date_actuelle)
            )
            historique_direction = 'ae2fr' if direction == 'aenor2fr' else 'fr2ae'
            cursor.execute(
                     '''INSERT INTO traductions_historique
                         (user_uuid, source_text, target_text, direction, timestamp, traduction_fiable)
                         VALUES (?, ?, ?, ?, ?, ?)''',
                     (session['user_uuid'], francais, aenor, historique_direction, date_actuelle, int(traduction_fiable)),
            )
            conn.commit() # Valide l'enregistrement

        logger.info(f'{VERT}{UNDERLINE}✓ Traduction sauvegardée (SQLite).{RESET}')

    except sqlite3.Error as exc:
        logger.error(f'{ROUGE}❌ Erreur lors de la sauvegarde dans SQLite: {exc}{RESET}')


def _extract_json_text(s: str) -> str:
    """Extraire le premier objet JSON trouvé dans une réponse texte (enlève les ``` éventuels)."""
    if not s:
        return ''
    t = s.strip()
    # Retire les blocs markdown ```json ou ```
    t = re.sub(r'```json', '```', t, flags=re.IGNORECASE)
    if t.startswith('```') and t.endswith('```'):
        t = t[3:-3].strip()
    # Cherche le premier objet JSON
    start = t.find('{')
    end = t.rfind('}')
    if start != -1 and end != -1 and end > start:
        return t[start:end+1].strip()
    return t


def evaluer_avec_gemini(phrase_fr: str, reponse_user: str) -> Dict:
    """Évalue la traduction d'un élève via Gemini et retourne {'note': int, 'commentaire': str}.

    En cas d'erreur, retourne {'note': 0, 'commentaire': '...'}.
    """
    direction = 'exercice'
    context = load_prompt(direction)
    if not context:
        return {'note': 0, 'commentaire': 'Erreur : contexte d\'évaluation manquant.'}

    if not API_KEYS_POOL:
        return {'note': 0, 'commentaire': 'Erreur : aucune clé API Gemini configurée.'}

    prompt_evaluation = f'''Phrase originale en français : "{phrase_fr}"
Traduction proposée par l'élève : "{reponse_user}"'''
    prompt_full = f'{context.rstrip()}\n\n{prompt_evaluation}'
    _print_global_prompt(direction, prompt_full)

    nb_tentatives = len(API_KEYS_POOL) if POOL_API_KEYS_ACTIVATION else 1
    erreurs = []
    for _ in range(nb_tentatives):
        api_key = get_current_api_key()
        client = get_gemini_client(api_key)
        if client is None or not hasattr(client, 'models') or not hasattr(client.models, 'generate_content'):
            break
        try:
            cache = get_or_create_cache(client, api_key, direction, context)
            if cache is not None and getattr(cache, 'name', None):
                response = _call_gemini_with_latency(
                    lambda: client.models.generate_content(
                        model=get_current_models()[0],
                        contents=prompt_evaluation,
                        config=types.GenerateContentConfig(cached_content=cache.name),
                    ),
                    'exercice',
                )
            else:
                response = _call_gemini_with_latency(
                    lambda: client.models.generate_content(
                        model=get_current_models()[0],
                        contents=prompt_full,
                    ),
                    'exercice',
                )

            reponse_brute = getattr(response, 'text', str(response))
            # tenter d'extraire JSON
            json_text = _extract_json_text(reponse_brute)
            try:
                parsed = json.loads(json_text)
                note_raw = parsed.get('note', 0)
                try:
                    note = int(float(note_raw))
                except Exception:
                    note = 0
                note = max(0, min(10, note))
                commentaire = str(parsed.get('commentaire', '') or '')
                return {'note': note, 'commentaire': commentaire}
            except Exception as exc:
                erreurs.append(f'Parsing JSON: {exc}')
                return {'note': 0, 'commentaire': f'Erreur parsing JSON depuis Gemini: {exc}'}

        except Exception as exc:
            erreurs.append(str(exc))
            if is_quota_error(exc):
                rotate_api_key()
                continue
            break

    # fallback legacy
    legacy_key = get_current_api_key()
    legacy_client = get_legacy_client(legacy_key)
    if legacy_client is not None and hasattr(legacy_client, 'GenerativeModel'):
        try:
            model = legacy_client.GenerativeModel(GEMINI_MODEL_LEGACY)
            response = _call_gemini_with_latency(
                lambda: model.generate_content(prompt_full),
                'exercice',
            )
            reponse_brute = getattr(response, 'text', str(response))
            json_text = _extract_json_text(reponse_brute)
            try:
                parsed = json.loads(json_text)
                note_raw = parsed.get('note', 0)
                try:
                    note = int(float(note_raw))
                except Exception:
                    note = 0
                note = max(0, min(10, note))
                commentaire = str(parsed.get('commentaire', '') or '')
                return {'note': note, 'commentaire': commentaire}
            except Exception as exc:
                erreurs.append(f'Parsing JSON (legacy): {exc}')
                return {'note': 0, 'commentaire': f'Erreur parsing JSON depuis Gemini (legacy): {exc}'}
        except Exception as exc:
            erreurs.append(str(exc))

    logger.error(f"Échec évaluation Gemini: {erreurs}")
    return {'note': 0, 'commentaire': 'Erreur : impossible d\'obtenir une évaluation de Gemini.'}


def log_ip_visit(ip: str) -> None:
    """Enregistre ou met à jour le compteur de visites pour une IP donnée."""
    if not ip:
        return
    try:
        now = datetime.now().isoformat(timespec='seconds')
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute('SELECT visits FROM ip_visits WHERE ip = ?', (ip,))
            row = cur.fetchone()
            if row:
                cur.execute('UPDATE ip_visits SET visits = visits + 1, last_seen = ? WHERE ip = ?', (now, ip))
            else:
                cur.execute('INSERT INTO ip_visits (ip, visits, last_seen) VALUES (?, ?, ?)', (ip, 1, now))
            conn.commit()
    except Exception as exc:
        logger.debug(f'Erreur log_ip_visit: {exc}')


@app.before_request
def before_request_log_ip():
    """Hook Flask pour logger l'IP de chaque requête."""
    try:
        ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR')
        if isinstance(ip, str) and ',' in ip:
            ip = ip.split(',')[0].strip()
        log_ip_visit(ip)
    except Exception:
        pass


@app.before_request
def ensure_user_uuid():
    """Attribue un identifiant persistant aux visiteurs sans compte."""
    if 'user_uuid' not in session:
        session['user_uuid'] = str(uuid.uuid4())


def insert_api_log(
    provenance: str,
    tokens: Optional[int],
    ip: Optional[str],
    response_time_ms: Optional[float] = None,
    prompt_tokens: Optional[int] = None,
    cached_tokens: Optional[int] = None,
    response_tokens: Optional[int] = None,
    status: str = 'success',
    traduction_fiable: bool = False,
) -> None:
    """Insère un enregistrement de log d'appel API dans la BDD (protégé contre injection)."""
    try:
        now = datetime.now().isoformat(timespec='seconds')
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute(
                'INSERT INTO api_logs '
                '(timestamp, provenance, tokens, ip, response_time_ms, '
                'prompt_tokens, cached_tokens, response_tokens, status, traduction_fiable) '
                'VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
                (
                    now, provenance or 'autre', tokens, ip, response_time_ms,
                    prompt_tokens, cached_tokens, response_tokens, status,
                    int(traduction_fiable),
                ),
            )
            conn.commit()
    except Exception as exc:
        logger.debug(f'Erreur insert_api_log: {exc}')


def require_admin(fn):
    """Décorateur simple pour protéger les routes admin."""
    from functools import wraps

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get('admin_authenticated'):
            return redirect(url_for('admin'))
        return fn(*args, **kwargs)

    return wrapper


def sauvegarder_exercice(phrase, reponse, note, commentaire):
    """Enregistre une correction d'exercice pour l'utilisateur de la session."""
    timestamp = datetime.now().isoformat(timespec='seconds')
    correction = f'{note}/10'
    with sqlite3.connect(DB_FILE) as conn:
        conn.execute(
            '''INSERT INTO exercices_historique
               (user_uuid, intitule_exercice, reponse_utilisateur, correction, note, feedback, timestamp)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (session['user_uuid'], phrase, reponse, correction, note, commentaire, timestamp),
        )
        conn.commit()


def get_admin_password() -> str:
    """Retourne le mot de passe partagé par la page admin et les actions protégées."""
    return os.getenv('ADMIN_PASSWORD', 'admin123')


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Page d'administration principale (affiche login si non authentifié)."""
    admin_password = get_admin_password()

    if request.method == 'POST' and not session.get('admin_authenticated'):
        form_pw = request.form.get('admin_password', '')
        if form_pw and form_pw == admin_password:
            session['admin_authenticated'] = True
            return redirect(url_for('admin'))
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
            cached_flag = (row[0] == '1') if row else CACHED_CONTEXTS_ACTIVATION
            cur.execute('SELECT value FROM app_config WHERE key = ?', ('POOL_API_KEYS_ACTIVATION',))
            row = cur.fetchone()
            pool_flag = (row[0] == '1') if row else POOL_API_KEYS_ACTIVATION
            cur.execute('SELECT value FROM app_config WHERE key = ?', ('PAIEMENT_ACTIVE',))
            row = cur.fetchone()
            paiement_active = (row[0] == '1') if row else PAIEMENT_ACTIVE
            cur.execute('SELECT value FROM app_config WHERE key = ?', ('PRINT_GLOBAL_PROMPT',))
            row = cur.fetchone()
            print_global_prompt = (row[0] == '1') if row else PRINT_GLOBAL_PROMPT

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
            paiement_active=PAIEMENT_ACTIVE,
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


@app.route('/admin/toggle_config', methods=['POST'])
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
        globals()[key] = (v == '1')

        if key in ('PAIEMENT_ACTIVE', 'CACHED_CONTEXTS_ACTIVATION', 'PRINT_GLOBAL_PROMPT'):
            reset_gemini_runtime_state()
            warmup_gemini()

        return jsonify({'success': True, 'key': key, 'value': globals()[key]}), 200
    except Exception as exc:
        return jsonify({'success': False, 'error': str(exc)}), 500


@app.route('/admin/shutdown', methods=['POST'])
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


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin'))


@app.route('/historique')
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

@app.route('/', methods=['GET', 'POST'])
def index():
    """
    Page d'accueil utilisant le traducteur local (dictionnaire).
    Aucun enregistrement dans traductions.json ici : cette route n'utilise
    pas l'API Gemini, seulement le module modules.traducteur.traduire.
    """
    return render_template('index.html')

@app.route('/cours')
def cours():
    cours = load_cours()
    return render_template('cours.html', cours=cours)

@app.route('/grammaire')
def grammaire():
    return render_template('grammaire.html')

@app.route('/grammaire_2')
def grammaire_2():
    return render_template('grammaire_2.html')

@app.route('/grammaire_3')
def grammaire_3():
    return render_template('grammaire_3.html')

@app.route('/ia-trad')
def ia_trad():
    return render_template('IA-trad.html')

@app.route('/scenario')
def scenario():
    return render_template('scenario.html')

@app.route('/commentaires', methods=['GET', 'POST'])
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
        return redirect(url_for('commentaires'))

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

@app.route('/api/like_comment/<int:comment_id>', methods=['POST'])
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


@app.route('/api/delete_comment/<int:comment_id>', methods=['POST'])
def delete_comment(comment_id):
    """Supprime un commentaire après vérification du mot de passe admin."""
    payload = request.get_json(silent=True) or request.form
    password = str(payload.get('password', ''))
    if not hmac.compare_digest(password, get_admin_password()):
        return jsonify({'success': False, 'error': 'Code incorrect'}), 403

    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.execute('DELETE FROM feedback WHERE id = ?', (comment_id,))
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'error': 'Commentaire introuvable'}), 404
        conn.commit()
    return jsonify({'success': True})



@app.route('/exercice', methods=['GET', 'POST'])
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

@app.route('/traduire', methods=['POST'])
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

        return jsonify({
            'success': True,
            'traduction': traduction,
            'commentaire': commentaire,
        }), 200

    except Exception as exc:
        logger.error(f'Erreur non gérée dans /traduire: {exc}')
        return jsonify({
            'success': False,
            'erreur': f'Erreur serveur : {str(exc)}',
        }), 500

@app.route('/stats/optimisation', methods=['GET'])
def stats_optimisation():
    """Retourne les statistiques de compression, d'optimisation et l'état du cache Gemini."""
    try:
        stats = {
            'prompt_sizes': {role: len(load_prompt(role)) for role in PROMPT_FILES},
            'total_context_size': sum(len(load_prompt(role)) for role in PROMPT_FILES),
            'api_keys_pool_size': len(API_KEYS_POOL),
            'active_key_index': CURRENT_KEY_INDEX if API_KEYS_POOL else None,
            'active_caches': len(GEMINI_CACHES),
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
# GESTIONNAIRES D'ERREURS
# =============================

@app.errorhandler(404)
def not_found(error):
    """Gère les routes non trouvées."""
    return jsonify({
        'success': False,
        'erreur': 'Route non trouvée',
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Gère les erreurs serveur."""
    logger.error(f'Erreur interne: {error}')
    return jsonify({
        'success': False,
        'erreur': 'Erreur interne du serveur',
    }), 500



# =============================
# POINT D'ENTRÉE
# =============================

load_files_at_startup()

if __name__ == "__main__":
    app.run()