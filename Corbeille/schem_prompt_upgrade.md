# Architecture de gestion des prompts

## Fichiers sources et génération

```text
data/grammaire_aenor.md       source éditoriale de la grammaire
        |
        +--> modules/IA_version.py
        |        nettoie les éléments nécessaires à la version IA
        |        |
        |        v
        +--> data/grammaire_aenor-IA.md

data/aenor_lexique.json -------+----------------------------------+
                               |                                  |
                               v                                  v
                     modules/conlang-update.py             validation JSON
                               |
       +-----------------------+------------------------+
       |                       |                        |
       v                       v                        v
prompt_trad_fr2ae.txt  prompt_trad_ae2fr.txt   prompt_exercice.txt
```

Chaque fichier final est assemblé strictement dans cet ordre :

1. instruction de rôle ;
2. contenu complet de `grammaire_aenor-IA.md` ;
3. lexique JSON sérialisé avec `ensure_ascii=False` et `separators=(',', ':')`.

`modules/conlang-update.py` doit être exécuté depuis n'importe quel dossier. Ses chemins sont calculés depuis la racine du projet et la grammaire est régénérée avant l'assemblage des prompts.

## Flux d'une requête Gemini

```text
Route Flask
   |
   +--> traduire_avec_gemini(texte, fr2aenor|aenor2fr)
   |       |
   |       +--> lecture data/prompt_trad_*.txt
   |       +--> détection de modification et invalidation du cache local
   |       +--> cache actif ?
   |              | oui : CachedContent = prompt complet
   |              |       Gemini reçoit uniquement le texte utilisateur
   |              |
   |              | non : Gemini reçoit prompt complet + texte utilisateur
   |
   +--> evaluer_avec_gemini(phrase, réponse)
           |
           +--> lecture data/prompt_exercice.txt
           +--> cache actif : Gemini reçoit uniquement les données de l'exercice
           +--> mode standard : prompt complet + données de l'exercice
```

Les caches locaux sont indexés par clé API, rôle de prompt et modèle. Une modification du contenu d'un fichier prompt invalide les caches du rôle concerné. Le changement de mode payant réinitialise également les clients et caches.

## Débogage et administration

`PRINT_GLOBAL_PROMPT` est une configuration globale persistée dans `data/traductions.db`, table `app_config`. Le toggle de `templates/admin_data.html` permet de la modifier. Lorsqu'elle vaut `True`, chaque appel affiche le nom du fichier et le prompt logique complet, y compris l'entrée utilisateur.

## Nettoyage après migration

Ces anciens fichiers ne sont plus lus par `app.py` et peuvent être supprimés après vérification :

- `data/Prompt systeme.txt`
- `data/Prompt systeme aenor2fr.txt`

À conserver :

- `data/grammaire_aenor.md`, source de documentation affichée ;
- `data/grammaire_aenor-IA.md`, source incluse dans les prompts ;
- `data/aenor_lexique.json`, source du lexique ;
- les trois nouveaux fichiers `prompt_*.txt`, produits par `conlang-update.py`.

## Faut-il minifier davantage la grammaire ?

Pas dans l'immédiat. La minification du lexique est sans ambiguïté : elle retire uniquement les espaces syntaxiques du JSON et conserve exactement les données. La grammaire, elle, contient des exemples, des séparateurs et une mise en forme qui peuvent aider le modèle à distinguer les règles et les contre-exemples.

Une minification légère pourrait économiser quelques tokens, mais le gain sera probablement inférieur à celui du lexique et le risque de fusionner des consignes ou de dégrader la lisibilité est réel. Il serait préférable de mesurer d'abord le nombre de tokens avec le tokenizer du modèle utilisé, puis de tester un jeu de traductions de référence avant toute compression destructive.
