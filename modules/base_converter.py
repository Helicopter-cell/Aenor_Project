import re

def decimal_to_base12(n):
    """Convertit un entier (Base 10) en chaîne Base 12 (avec ° et ¤)."""
    try:
        n = int(n)
    except ValueError:
        return str(n) # Sécurité : retourne la chaîne brute si ce n'est pas un nombre

    if n == 0:
        return "0"

    # Les 12 chiffres, incluant tes symboles pour 10 et 11
    digits = "0123456789°¤"
    result = ""
    is_negative = n < 0
    n = abs(n)

    while n > 0:
        result = digits[n % 12] + result
        n //= 12

    return "-" + result if is_negative else result

def process_aenor_numbers(text):
    """
    Cherche les nombres entre %...% dans le texte, les convertit en base 12,
    et retire les % dans le texte final.
    """
    # Fonction locale appelée par re.sub pour chaque correspondance
    def replace_match(match):
        base10_str = match.group(1) # Extrait le nombre sans les %
        return decimal_to_base12(base10_str)

    # Regex : %(\d+)% 
    # Cherche un '%', suivi de 1 ou plusieurs chiffres (\d+), suivi d'un '%'
    return re.sub(r'%(\d+)%', replace_match, text)

# --- Zone de test (s'exécute uniquement si le fichier est lancé directement) ---
if __name__ == "__main__":
    texte_test = "Gemini a renvoyé %13% et aussi %15% pour finir avec %144%."
    texte_converti = process_aenor_numbers(texte_test)
    print("Test de conversion :")
    print(f"Original : {texte_test}")
    print(f"Converti : {texte_converti}") 
    # Résultat attendu: Gemini a renvoyé 9 et aussi ¤¤ pour finir avec 100.