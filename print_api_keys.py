import os

# Liste des suffixes de tes 6 clés (de 1 à 6)
key_indices = range(1, 7)

print("# --- Clés détectées au format os.environ ---")

for i in key_indices:
    # 1. Vérification du format classique : GEMINI_API_KEY_1, GEMINI_API_KEY_2, etc.
    standard_name = f"GEMINI_API_KEY_{i}"
    val_standard = os.getenv(standard_name)

    if val_standard:
        print(f"os.environ['{standard_name}'] = '{val_standard}'")

    # 2. Vérification du format avec préfixe € : €GEMINI_API_KEY_1, etc.
    euro_name = f"€GEMINI_API_KEY_{i}"
    val_euro = os.getenv(euro_name)

    if val_euro:
        print(f"os.environ['{euro_name}'] = '{val_euro}'")