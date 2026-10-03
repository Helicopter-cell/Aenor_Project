"""
Ce fichier n'est éxécuté nul part. Il ne sert qu'a l'administrateur, et ce
fichier exécuté sur une autre machine ne servirait à rien. Ainsi, ce fichier
ne sert qu'a aider l'administrateur a récupérer les clé très facilement et rapidement.
"""

import os

def describe_key(name):
    value = os.getenv(name)
    if value:
        print(f"{name}: {value}")

for name in (
    "€GEMINI_API_KEY_1",
    "€GEMINI_API_KEY_2",
    "€GEMINI_API_KEY_3",
    "€GEMINI_API_KEY",
    "€GOOGLE_API_KEY",
    "GEMINI_API_KEY_1",
    "GEMINI_API_KEY_2",
    "GEMINI_API_KEY_3",
    "GEMINI_API_KEY",
    "GOOGLE_API_KEY",
):
    describe_key(name)