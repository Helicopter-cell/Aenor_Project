import re
from pathlib import Path
from modules.utils import get_path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def nettoyer_fichier():
    """
    Lit le fichier source spécifié :
    - supprime les doubles crochets '[[' et ']]'
    - supprime tout le contenu encadré par '£$'
    Puis sauvegarde le résultat dans le fichier de destination.
    """
    fichier_source = get_path('|rootPATH|grammaire_aenor')
    fichier_destination = get_path('|dataPATH|grammaire_aenor-IA')

    try:
        # Lecture du fichier source (en UTF-8 pour les accents)
        with open(fichier_source, 'r', encoding='utf-8') as f_source:
            contenu = f_source.read()

        # 1. Suppression des balises £$...£$ (et de tout ce qui se trouve à l'intérieur)
        # re.DOTALL permet de capturer également les retours à la ligne entre les symboles
        contenu_nettoye = re.sub(r'£\$(.*?)£\$', '', contenu, flags=re.DOTALL)

        # 2. Suppression des doubles crochets
        contenu_nettoye = re.sub(r'\[\[|\]\]', '', contenu_nettoye)

        # Écriture du contenu nettoyé dans le fichier de destination
        with open(fichier_destination, 'w', encoding='utf-8') as f_dest:
            f_dest.write(contenu_nettoye)

        print(f"\nSucces : le fichier a ete nettoye et copie dans : {fichier_destination}")

    except FileNotFoundError:
        print(f"\nErreur : le fichier source '{fichier_source}' est introuvable. Verifie le chemin.")
    except Exception as e:
        print(f"\nErreur : une erreur est survenue : {e}")

# Exécution du script
if __name__ == "__main__":
    nettoyer_fichier()