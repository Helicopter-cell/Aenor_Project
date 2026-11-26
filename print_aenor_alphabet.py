import json

def extraire_lettres_aenor(chemin_fichier):
    """Parcourt récursivement le fichier JSON pour trouver tous les caractères uniques."""
    try:
        with open(chemin_fichier, 'r', encoding='utf-8') as f:
            lexique = json.load(f)
    except FileNotFoundError:
        print(f"Erreur : Le fichier introuvable au chemin : '{chemin_fichier}'")
        return []
    except json.JSONDecodeError:
        print("Erreur : Le fichier sélectionné n'est pas un format JSON valide.")
        return []
    
    caracteres_uniques = set()
    
    def explorer(element):
        if isinstance(element, dict):
            for val in element.values():
                explorer(val)
        elif isinstance(element, str):
            for char in element:
                caracteres_uniques.add(char)
                
    explorer(lexique)
    return sorted(list(caracteres_uniques))

# Demander à l'utilisateur de saisir le chemin d'accès directement dans la console
chemin = "data/Lexique_ae_V2.json"

lettres = extraire_lettres_aenor(chemin)

if lettres:
    print("\nCaractères uniques utilisés en Aënor :")
    print(lettres)
    print(f"\nTotal : {len(lettres)} caractères différents trouvés.")