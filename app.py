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
import logging
import os
import re
import time
import warnings
import sqlite3
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import subprocess
import sys
from threading import Timer

# --- Bibliothèques tierces ---
from tenacity import retry, stop_after_attempt, wait_random_exponential
from flask import Flask, jsonify, render_template, request, session, redirect, url_for
from google import genai
from google.genai import types

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
app.jinja_env.filters['render_cours_value'] = render_cours_value
app.jinja_env.filters['clean_text'] = clean_text
app.jinja_env.globals['static_path'] = static_path
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Contenus statiques chargés au démarrage ---
PROMPT_FILES = {
    'fr2aenor': '|dataPATH|prompt_trad_fr2ae',
    'aenor2fr': '|dataPATH|prompt_trad_ae2fr',
    'exercice': '|dataPATH|prompt_exercice',
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
CACHE_REFRESH_MARGIN_SECONDS = 120  # Marge avant expiration pour tenter une prolongation (caches.update) plutôt qu'une recréation


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
DB_FILE = str(get_path('|dataPATH|SQLite'))

PRINT_GLOBAL_PROMPT = False


# =============================
# FONCTIONS UTILITAIRES
# =============================

def prompt_path(role: str) -> str:
    """Retourne le chemin absolu du prompt associé à un rôle Gemini."""
    filename = PROMPT_FILES.get(role)
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
        logger.info(f'{CYAN}ℹ Prompt modifié, cache invalidé: {PROMPT_FILES[role]}{RESET}')
    PROMPT_SIGNATURES[role] = signature
    PROMPT_CONTENTS[role] = content
    return content


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
    os.makedirs("data", exist_ok=True)
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
                ip TEXT
            )
        ''')

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

def _log_token_usage(response) -> None:
    """Affiche dans les logs la consommation de tokens (prompt / cache / réponse) d'un appel Gemini."""
    usage = getattr(response, 'usage_metadata', None)
    if not usage:
        return

    cached_tokens = getattr(usage, 'cached_content_token_count', 0) or 0
    logger.info(f'{JAUNE}+----------------------------+----------+-------------+{RESET}')
    logger.info(
        f'{JAUNE}|📊 TOKENS -> Prompt: {BOLD}{ORANGE}{usage.prompt_token_count} {RESET} '
        f'{JAUNE}| Cache: {RESET}{ROUGE}{BOLD}{cached_tokens}{RESET} '
        f'{JAUNE}| Réponse: {BOLD}{usage.candidates_token_count} |{RESET}')

    logger.info(f'{JAUNE}+----------------------------+----------+-------------+{RESET}')


def _print_global_prompt(role: str, prompt: str) -> None:
    """Affiche le fichier source et le prompt logique complet si demandé par l'admin."""
    if not PRINT_GLOBAL_PROMPT:
        return
    print(f'\n===== PROMPT GEMINI: {PROMPT_FILES[role]} =====')


# =============================
# FONCTION DE TRADUCTION AVEC GEMINI
# =============================

def traduire_avec_gemini(texte_utilisateur: str, direction: str = 'fr2aenor', provenance: str = 'autre') -> str:
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
    context = load_prompt(direction)
    if not context:
        return "Erreur : le contexte de traduction n'a pas pu être construit."

    if not API_KEYS_POOL:
        return (
            "Erreur : aucune clé API Gemini n'a été configurée. "
            "Définissez GEMINI_API_KEY_1/2/3, GEMINI_API_KEY ou GOOGLE_API_KEY."
        )

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
            cache = get_or_create_cache(client, api_key, direction, context)

            if cache is not None and getattr(cache, 'name', None):
                response = client.models.generate_content(
                    model=get_current_models()[0],
                    contents=texte_utilisateur,
                    config=types.GenerateContentConfig(cached_content=cache.name),
                )
            else:
                response = client.models.generate_content(
                    model=get_current_models()[0],
                    contents=prompt_fallback,
                )


            # On récupère le texte brut de Gemini
            traduction_brute = getattr(response, 'text', str(response))
            
            # --- APPLICATION DU FILTRE BASE 12 ICI ---
            traduction = process_aenor_numbers(traduction_brute)
            # -----------------------------------------
            
            _log_token_usage(response)
            try:
                usage = getattr(response, 'usage_metadata', None)
                tokens = None
                if usage:
                    cached_tokens = getattr(usage, 'cached_content_token_count', 0) or 0
                    prompt_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                    resp_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                    tokens = int((prompt_tokens - cached_tokens) + resp_tokens)
            except Exception:
                tokens = None
            try:
                ip = request.remote_addr if request else None
            except Exception:
                ip = None
            insert_api_log(provenance, tokens, ip)
            enregistrer_mots_non_traduits(traduction)
            # Sauvegarde en fonction du sens : sauvegarder_traduction(francais, aenor)
            if direction == 'aenor2fr':
                sauvegarder_traduction(traduction, texte_utilisateur)
            else:
                sauvegarder_traduction(texte_utilisateur, traduction)
            return traduction


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
            response = model.generate_content(prompt_fallback)
            
            # On récupère le texte brut de Gemini
            traduction_brute = getattr(response, 'text', str(response))
            
            # --- APPLICATION DU FILTRE BASE 12 ICI ---
            traduction = process_aenor_numbers(traduction_brute)
            # -----------------------------------------
            
            # Le fallback legacy n'utilise pas de cache (aucun cached_content transmis),
            # mais on journalise quand même prompt/réponse pour garder une visibilité complète.
            _log_token_usage(response)
            try:
                usage = getattr(response, 'usage_metadata', None)
                tokens = None
                if usage:
                    cached_tokens = getattr(usage, 'cached_content_token_count', 0) or 0
                    prompt_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                    resp_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                    tokens = int((prompt_tokens - cached_tokens) + resp_tokens)
            except Exception:
                tokens = None
            try:
                ip = request.remote_addr if request else None
            except Exception:
                ip = None
            insert_api_log(provenance, tokens, ip)
            enregistrer_mots_non_traduits(traduction)
            if direction == 'aenor2fr':
                sauvegarder_traduction(traduction, texte_utilisateur)
            else:
                sauvegarder_traduction(texte_utilisateur, traduction)
            return traduction
        
        except Exception as exc:
            erreurs_rencontrees.append(str(exc))
            logger.error(f'❌ Échec du fallback legacy: {exc}')

    logger.error(f'❌ Toutes les tentatives de traduction ont échoué: {erreurs_rencontrees}')
    detail = '; '.join(erreurs_rencontrees) or 'raison inconnue'
    return f'Erreur : Impossible de générer la traduction. ({detail})'

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


def sauvegarder_traduction(francais, aenor):
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
                response = client.models.generate_content(
                    model=get_current_models()[0],
                    contents=prompt_evaluation,
                    config=types.GenerateContentConfig(cached_content=cache.name),
                )
            else:
                response = client.models.generate_content(
                    model=get_current_models()[0],
                    contents=prompt_full,
                )

            reponse_brute = getattr(response, 'text', str(response))
            _log_token_usage(response)
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
                # log API
                try:
                    usage = getattr(response, 'usage_metadata', None)
                    tokens = None
                    if usage:
                        cached_tokens = getattr(usage, 'cached_content_token_count', 0) or 0
                        prompt_tokens = getattr(usage, 'prompt_token_count', 0) or 0
                        resp_tokens = getattr(usage, 'candidates_token_count', 0) or 0
                        tokens = int((prompt_tokens - cached_tokens) + resp_tokens)
                except Exception:
                    tokens = None
                try:
                    ip = request.remote_addr if request else None
                except Exception:
                    ip = None
                insert_api_log('exercice', tokens, ip)
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
            response = model.generate_content(prompt_full)
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
                insert_api_log('exercice', None, request.remote_addr if request else None)
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


def insert_api_log(provenance: str, tokens: Optional[int], ip: Optional[str]) -> None:
    """Insère un enregistrement de log d'appel API dans la BDD (protégé contre injection)."""
    try:
        now = datetime.now().isoformat(timespec='seconds')
        with sqlite3.connect(DB_FILE) as conn:
            cur = conn.cursor()
            cur.execute('INSERT INTO api_logs (timestamp, provenance, tokens, ip) VALUES (?, ?, ?, ?)',
                        (now, provenance or 'autre', tokens, ip))
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


@app.route('/admin', methods=['GET', 'POST'])
def admin():
    """Page d'administration principale (affiche login si non authentifié)."""
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')

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

            # Translations pagination (first page)
            page = int(request.args.get('page', 1)) if request.args.get('page') else 1
            per_page = 20
            offset = (page - 1) * per_page
            cur.execute('SELECT id, input, output, date FROM traductions ORDER BY date DESC LIMIT ? OFFSET ?', (per_page, offset))
            translations = cur.fetchall()

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
        page=page,
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




@app.route('/exercice', methods=['GET', 'POST'])
def exercice():
    if request.method == 'POST':
        user = request.form['answer']
        phrase = request.form['phrase']

        # Évaluer la traduction de l'élève via Gemini (professeur virtuel)
        evaluation = evaluer_avec_gemini(phrase, user)
        note = evaluation.get('note', 0)
        commentaire = evaluation.get('commentaire', '')

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

        if not all(load_prompt(role) for role in ('fr2aenor', 'aenor2fr')):
            logger.error('Contexte manquant pour la traduction')
            return jsonify({
                'success': False,
                'erreur': 'Erreur système : contexte de configuration manquant',
            }), 500

        traduction = traduire_avec_gemini(texte, direction=direction, provenance='traduction')

        return jsonify({
            'success': True,
            'traduction': traduction,
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