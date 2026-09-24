# -*- coding: utf-8 -*-
import os
import re
import sys
import subprocess


import markdown
from bs4 import BeautifulSoup
from modules.utils import get_path

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


def construire_accordeons(html_content):
    """Transforme les titres Markdown en sections HTML imbriquees."""
    soup = BeautifulSoup(html_content, "html.parser")
    nodes = list(soup.contents)

    def niveau_titre(node):
        if node.name and re.fullmatch(r"h[1-6]", node.name):
            return int(node.name[1])
        return None

    def construire_sections(position, niveau_parent):
        resultat = []
        while position < len(nodes):
            niveau = niveau_titre(nodes[position])
            if niveau is not None and niveau <= niveau_parent:
                break

            if niveau is None:
                resultat.append(nodes[position])
                position += 1
                continue

            titre = nodes[position]
            position += 1
            contenu = soup.new_tag("div", attrs={"class": "cours-content"})
            titre_texte = titre.get_text(" ", strip=True)
            summary = soup.new_tag("summary", attrs={"class": "cours-summary"})
            chevron = soup.new_tag("span", attrs={"class": "cours-chevron", "aria-hidden": "true"})
            chevron.string = "▶"
            texte = soup.new_tag("span", attrs={"class": "cours-summary-text"})
            texte.string = titre_texte
            summary.extend([chevron, texte])

            while position < len(nodes):
                prochain_niveau = niveau_titre(nodes[position])
                if prochain_niveau is not None and prochain_niveau <= niveau:
                    break
                if prochain_niveau is not None:
                    sous_sections, position = construire_sections(position, niveau)
                    for sous_section in sous_sections:
                        contenu.append(sous_section)
                else:
                    contenu.append(nodes[position])
                    position += 1

            section = soup.new_tag("details", attrs={"class": "cours-accordion"})
            section.extend([summary, contenu])
            resultat.append(section)

        return resultat, position

    sections, position = construire_sections(0, 0)
    resultat = BeautifulSoup("", "html.parser")
    while sections:
        resultat.append(sections.pop(0))
    if position < len(nodes):
        for node in nodes[position:]:
            resultat.append(node)
    return str(resultat)


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

    # --- ÉTAPE D : STRUCTURATION DES SECTIONS ---
    print("Transformation des titres en accordéons imbriqués...")
    corps_html = construire_accordeons(corps_html)

    # --- ÉTAPE E : STRUCTURATION VISUELLE ---
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
<script>
    document.addEventListener('DOMContentLoaded', function () {{
        document.querySelectorAll('.cours-accordion').forEach(function (details) {{
            details.open = false;
            const summary = details.querySelector(':scope > .cours-summary');
            const chevron = details.querySelector(':scope > .cours-summary .cours-chevron');

            if (summary) {{
                summary.addEventListener('click', function (event) {{
                    event.preventDefault();
                    details.open = !details.open;
                }});
            }}

            const syncState = function () {{
                const isOpen = details.open;
                details.setAttribute('aria-expanded', String(isOpen));
                if (chevron) {{
                    chevron.textContent = isOpen ? '▼' : '▶';
                }}
            }};

            details.addEventListener('toggle', syncState);
            syncState();
        }});
    }});
</script>
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