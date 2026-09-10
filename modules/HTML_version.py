# -*- coding: utf-8 -*-
import os
import re
import sys
import subprocess

# 1. Vérification et installation automatique des bibliothèques requises
REQUIRED_PACKAGES = {
    "markdown": "markdown",
    "bs4": "beautifulsoup4"
}

for module_name, package_name in REQUIRED_PACKAGES.items():
    try:
        __import__(module_name)
    except ImportError:
        print(f"La bibliothèque '{package_name}' est manquante. Installation en cours...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            print(f"'{package_name}' installé avec succès !")
        except Exception as e:
            print(f"Erreur lors de l'installation de {package_name} : {e}")
            sys.exit(1)

import markdown
from bs4 import BeautifulSoup
from modules.utils import get_path


def proteger_asterisques_dans_brackets(texte):
    """
    Parcourt le texte et remplace l'astérisque '*' par 'AENORASTERISK'
    UNIQUEMENT lorsqu'il se trouve à l'intérieur de doubles crochets [[...]].
    """
    def repl(match):
        contenu_interne = match.group(1)
        # On remplace l'astérisque seulement dans cette zone
        contenu_protege = contenu_interne.replace("*", "AENORASTERISK")
        return f"[[{contenu_protege}]]"

    return re.sub(r'\[\[(.*?)\]\]', repl, texte)


def formater_aenor(html_content):
    """
    Étape 3 : Détection, conversion en HTML de l'Aënor et restauration des astérisques.
    """
    try:
        if "[[" in html_content:
            html_content = re.sub(r'\[\[(.*?)\]\]', r'<b class="exemple-grammaire">\1</b>', html_content)
        
        # Restaure les astérisques uniquement là où ils ont été protégés
        html_content = html_content.replace("AENORASTERISK", "*")
        
    except Exception as e:
        print(f"[Attention] Échec du formatage Aënor : {e}")
    return html_content


def generer_template_flask(fichier_md=None, fichier_html=None):
    fichier_md = fichier_md or str(get_path('|rootPATH|grammaire_aenor'))
    fichier_html = fichier_html or str(get_path('|htmlPATH|grammaire_3'))
    if not os.path.exists(fichier_md):
        print(f"Erreur : Le fichier '{fichier_md}' est introuvable.")
        return

    print(f"Lecture de '{fichier_md}'...")
    with open(fichier_md, "r", encoding="utf-8") as f:
        texte_markdown = f.read()

    # --- ÉTAPE 0 : SUPPRESSION DES SYMBOLES £$ ---
    print("Suppression des symboles £$...")
    texte_markdown = texte_markdown.replace("£$", "")

    # --- ÉTAPE A : PROTECTION CIBLÉE ---
    print("Protection ciblée des astérisques dans les exemples [[...]]...")
    texte_markdown_protege = proteger_asterisques_dans_brackets(texte_markdown)

    # --- ÉTAPE B : CONVERSION EN HTML ---
    print("Conversion du Markdown...")
    extensions_md = ['extra', 'sane_lists', 'nl2br']
    corps_html = markdown.markdown(texte_markdown_protege, extensions=extensions_md)

    # --- ÉTAPE C : FORMATAGE ET RESTAURATION ---
    print("Formatage de l'Aënor et restauration des astérisques...")
    corps_html = formater_aenor(corps_html)

    # --- ÉTAPE D : STRUCTURATION VISUELLE ---
    print("Mise en forme visuelle du code HTML...")
    try:
        soup = BeautifulSoup(corps_html, "html.parser")
        html_structure = soup.prettify()

        # Nettoyage des lignes vides générées par le parser
        lignes_propres = [ligne for ligne in html_structure.splitlines() if ligne.strip()]

        # Indentation de 4 espaces pour s'aligner dans la balise <div>
        html_indente = "\n".join("    " + ligne for ligne in lignes_propres)
    except Exception as e:
        print(f"[Attention] Impossible de structurer l'HTML : {e}. Utilisation du code brut.")
        html_indente = "\n    " + corps_html.replace("\n", "\n    ")

    # Étape 4 : Structuration pour Jinja2 / Flask
    template_flask = f"""{{% extends 'base.html' %}}

{{% block content %}}
<div class="conlang-documentation">
{html_indente}
</div>
{{% endblock %}}"""

    # Création du dossier de destination s'il n'existe pas
    dossier_destination = os.path.dirname(fichier_html)
    if dossier_destination and not os.path.exists(dossier_destination):
        os.makedirs(dossier_destination)

    print(f"Écriture du template Flask dans '{fichier_html}'...")
    with open(fichier_html, "w", encoding="utf-8") as f:
        f.write(template_flask)

    print("\nSuccès ! Le template Flask structuré a été généré proprement.")


if __name__ == "__main__":
    generer_template_flask()