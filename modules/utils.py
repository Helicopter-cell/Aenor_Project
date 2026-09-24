# =============================
# modules/utils.py
# =============================

# Importation du module natif pour manipuler les fichiers et données au format JSON
import json
from pathlib import Path

# Importation du module d'expressions régulières (RegEx) pour rechercher et remplacer des motifs de texte
import re

# Importation des fonctions de sécurité Flask/Jinja2 : 
# - Markup : indique à Jinja2 que le HTML généré est sûr et peut être affiché sans être échappé
# - escape : convertit les caractères spéciaux HTML (<, >, &, etc.) en texte sécurisé pour éviter les failles XSS
from markupsafe import Markup, escape


PROJECT_ROOT = Path(__file__).resolve().parent.parent
PATHS_INDEX = PROJECT_ROOT / 'paths_index.json'


def _load_paths_index():
    """Charge l'index unique des fichiers du projet."""
    with PATHS_INDEX.open(encoding='utf-8') as file_handle:
        return json.load(file_handle)


def get_path(alias):
    """Retourne le chemin absolu associé à un alias de paths_index.json."""
    try:
        relative_path = _load_paths_index()[alias]
    except KeyError as exc:
        raise KeyError(f'Alias de chemin inconnu: {alias}') from exc
    return PROJECT_ROOT / relative_path


def static_path(alias):
    """Retourne le chemin relatif attendu par l'endpoint Flask static."""
    relative_path = get_path(alias).relative_to(PROJECT_ROOT / 'static')
    return relative_path.as_posix()


# Constantes d'espacement pour le rendu HTML
MARGIN_GRANDE_CATEGORIE = '3em'
MARGIN_SOUS_CATEGORIE = '2.5em'
INDENTATION_PAR_NIVEAU = 2
ESPACEMENT_ELEMENT_JSON = '0.25em'


AENOR_LATIN_MAP = str.maketrans({
    '§': 'š',
    '/': 'r',
    'µ': "m'",
    '=': "l'",
    ';': 'e',
    '*': 'ou',
    '²': '',
})

AENOR_PHONETIC_MAP = {
    'a': 'a',
    'b': 'b',
    'c': 'k',
    'd': 'd',
    'e': 'e',
    'f': 'f',
    'g': 'g',
    'h': 'h',
    'i': 'i',
    'j': 'ʒ',
    'k': 'k',
    'l': 'l',
    'm': 'm',
    'n': 'n',
    'o': 'ɔ',
    'p': 'p',
    'q': 'k',
    'r': 'ʁ',
    's': 's',
    't': 't',
    'u': 'y',
    'v': 'v',
    'w': 'w',
    'x': 'ks',
    'y': 'j',
    'z': 'z',
    'à': 'a',
    'â': 'ɑ',
    'ä': 'a',
    'é': 'e',
    'è': 'ɛ',
    'ê': 'ɛ',
    'ë': 'ə',
    'î': 'i',
    'ï': 'i',
    'ô': 'ɔ',
    'ö': 'ɔ',
    'ù': 'y',
    'û': 'y',
    'ü': 'y',
    '§': 'ʃ',
    '/': 'ɾ',
    'µ': 'm',
    '=': 'l',
    ';': 'ə',
    '*': 'u',
    '²': '',
}


def convert_aenor_to_latin(mot_aenor):
    """Convertit les caractères typographiques Aënor en alphabet occidental."""
    if not isinstance(mot_aenor, str):
        return mot_aenor
    return mot_aenor.translate(AENOR_LATIN_MAP)


def convert_aenor_to_phonetic(mot_aenor):
    """Retourne la transcription IPA d'un mot Aënor, entre crochets."""
    if not isinstance(mot_aenor, str):
        return mot_aenor
    transcription = ''.join(
        AENOR_PHONETIC_MAP.get(character, character)
        for character in mot_aenor
    )
    return f'[{transcription}]'


def enrich_lexicon_entry(traduction_francaise, mot_aenor):
    """Construit une entrée complète sans modifier la donnée source."""
    return {
        'french': traduction_francaise,
        'aenor': mot_aenor,
        'latin': convert_aenor_to_latin(mot_aenor),
        'phonetic': convert_aenor_to_phonetic(mot_aenor),
    }


def enrich_lexicon(value):
    """Transforme récursivement les paires feuille du lexique en entrées enrichies."""
    if isinstance(value, dict):
        enriched = {}
        for key, val in value.items():
            if not isinstance(val, (dict, list)) and clean_text(key) and clean_text(val):
                enriched[key] = enrich_lexicon_entry(key, val)
            else:
                enriched[key] = enrich_lexicon(val)
        return enriched
    if isinstance(value, list):
        return [enrich_lexicon(item) for item in value]
    return value


# Définition de la fonction chargée de charger le fichier JSON du lexique
def load_cours():
    # Ouverture du lexique avec un encodage UTF-8 (pour gérer les accents)
    with get_path('|dataPATH|aenor_lexique').open(encoding='utf-8') as f:
        # Analyse (parse) du contenu JSON du fichier et renvoi sous forme de dictionnaire ou liste Python
        return enrich_lexicon(json.load(f))


# Définition de la fonction de nettoyage du texte brut du JSON
def clean_text(text):
    """Supprime les commentaires $...$ et remplace les underscores par des espaces."""
    # Vérification : si la donnée passée n'est pas une chaîne de caractères (ex: un nombre ou None)
    if not isinstance(text, str):
        # On retourne la valeur telle quelle sans tenter d'appliquer des fonctions de texte
        return text

    # Utilisation d'une RegEx pour supprimer tout le texte situé entre deux symboles '$' (inclus)
    cleaned = re.sub(r'\$[^$]*\$', '', text)

    # Remplacement de tous les underscores '_' par des espaces ' ', puis suppression des espaces inutiles en début et fin de chaîne (.strip())
    cleaned = cleaned.replace('_', ' ').strip()

    # Renvoi du texte propre
    return cleaned


# Définition de la fonction récursive générant le code HTML dynamiquement selon la profondeur du JSON
def render_cours_value(value, level=0):
    """Convertit récursivement une structure JSON en HTML propre.

    - Les dictionnaires deviennent des blocs espacés.
    - Les valeurs de la langue inventée sont entourées de la classe HTML.
    - Les sous-catégories sont bien séparées par une marge supérieure.
    """
    # Calcul de l'indentation visuelle (en 'em') basée sur le niveau de profondeur actuel dans l'arbre JSON
    indent = level * INDENTATION_PAR_NIVEAU

    # CAS 1 : Si la valeur à traiter est un dictionnaire (ex: des catégories ou paires clé:valeur)
    if isinstance(value, dict):
        # Initialisation d'une liste vide pour stocker les éléments HTML générés à ce niveau
        html_parts = []

        # Parcours de chaque paire (clé, valeur) contenue dans le dictionnaire
        for key, val in value.items():
            # Nettoyage de la clé (nom de la catégorie/mot) puis protection contre les failles HTML
            key_html = escape(clean_text(key))

            # Une feuille enrichie représente une entrée du lexique avec ses quatre champs.
            if isinstance(val, dict) and set(val) == {'french', 'aenor', 'latin', 'phonetic'}:
                html_parts.append(
                    f'<div class="lexique-entry" style="margin-top:{ESPACEMENT_ELEMENT_JSON}; margin-left:{indent}em;">'
                    f'<span class="lexique-aenor">{escape(clean_text(val["aenor"]))}</span>'
                    f'<span class="lexique-latin">({escape(clean_text(val["latin"]))})</span>'
                    f'<span class="lexique-phonetic">{escape(clean_text(val["phonetic"]))}</span>'
                    f'<span class="lexique-separator" aria-hidden="true">:</span>'
                    f'<strong class="lexique-french">{escape(clean_text(val["french"]))}</strong>'
                    f'</div>'
                )
                continue

            # Si la valeur associée est elle-même un dictionnaire ou une liste (sous-catégorie)
            if isinstance(val, (dict, list)):
                # Appel récursif de la fonction sur cette sous-structure en augmentant le niveau de profondeur (+1)
                nested = render_cours_value(val, level + 1)

                margin_top = MARGIN_GRANDE_CATEGORIE if level == 0 else MARGIN_SOUS_CATEGORIE

                html_parts.append(
                    f'<details class="cours-accordion" style="margin-top:{margin_top}; margin-left:{indent}em;">'
                    f'<summary class="cours-summary">'
                    f'<span class="cours-chevron" aria-hidden="true">▶</span>'
                    f'<span class="cours-summary-text">{key_html}</span>'
                    f'</summary>'
                    f'<div class="cours-content">{nested}</div>'
                    f'</details>'
                )
            
            # Sinon, si la valeur est une donnée simple (ex: la traduction d'un mot)
            else:
                # Nettoyage et sécurisation HTML de la valeur (traduction)
                val_html = escape(clean_text(val))
                
                # CORRECTION : On applique directement l'espacement des petits éléments
                margin_top = ESPACEMENT_ELEMENT_JSON

                html_parts.append(
                    f'<div style="margin-top:{margin_top}; margin-left:{indent}em;">'
                    f'<strong>{key_html}</strong> : '
                    f'<span class="exemple-grammaire">{val_html}</span></div>'
                )

        # Assemblage de tous les morceaux HTML en une seule chaîne, marquée comme sûre pour Jinja2
        return Markup(''.join(html_parts))

    # CAS 2 : Si la valeur à traiter est une liste JSON ([...])
    if isinstance(value, list):
        # Génération d'éléments de liste HTML <li> pour chaque item, en appelant récursivement la fonction pour chacun
        margin_top = MARGIN_GRANDE_CATEGORIE if level == 0 else MARGIN_SOUS_CATEGORIE
        items = ''.join(
            f'<li style="margin-top:{ESPACEMENT_ELEMENT_JSON};">{render_cours_value(item, level + 1)}</li>'
            for item in value
        )

        # Encapsulation de la liste dans une balise <ul> avec l'indentation appropriée, marquée comme sûre pour Jinja2
        return Markup(
            f'<ul style="margin:{margin_top} 0 0 {indent + INDENTATION_PAR_NIVEAU}em; padding-left:1em;">{items}</ul>'
        )

    # CAS 3 : Si la valeur est un texte/nombre simple isolé (ni dict, ni list)
    # Nettoyage, sécurisation, et encapsulation directe dans un <span> avec la classe "exemple-grammaire"
    return Markup(f'<span class="exemple-grammaire">{escape(clean_text(value))}</span>')