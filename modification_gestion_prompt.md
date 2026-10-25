# Gestion des prompts Gemini après refonte

## Architecture des données envoyées

Le service sépare désormais les références stables des consignes et de la phrase
à traiter. Les noms de fichiers sont résolus via `paths_index.json`, au moyen de
`modules/utils.py:get_path`.

| Fichier source | Rôle | Destination Gemini |
|---|---|---|
| `Global_Manual_V2.md` (`|rootPATH|grammaire_aenor`) | Manuel complet V2 : grammaire et règles immuables | `system_instruction` |
| `data/Lexique_ae_V2.json` (`|dataPATH|aenor_lexique`) | Lexique structuré français–aënor | Bloc de données de référence dans `contents`, ou dans `cached_content.contents` |
| `data/prompt_trad_fr2ae.txt` et `data/prompt_trad_ae2fr.txt` | Consignes ciblées selon le sens de traduction | Partie consigne de `contents` |
| `data/prompt_trad_fr2ae_comment.txt` et `data/prompt_trad_ae2fr_comment.txt` | Consignes ciblées avec format pédagogique | Partie consigne de `contents` |
| Phrase fournie à la traduction | Entrée dynamique de l'utilisateur | Partie demande de `contents` |
| `data/prompt_revision_traduction.txt` | Consigne de vérification du mode fiable | Consigne du second appel, dans `contents` |
| `data/prompt_exercice.txt` | Consignes ciblées d'évaluation | Partie consigne de `contents` |

Le manuel n'est donc jamais ajouté au texte utilisateur. Le lexique est sérialisé
en JSON compact, puis explicitement introduit comme **donnée de référence**, sans
le mélanger à la consigne. Le contenu dynamique comporte la consigne de rôle et
la phrase (ou les éléments d'évaluation/révision), pas une copie du manuel.

## Parcours dans le code

1. `paths_index.json` associe les alias de fichiers à leurs chemins. `get_path`
   dans `modules/utils.py` résout ces alias depuis la racine du projet.
2. `services/gemini_service.py:load_prompt` lit le prompt de rôle. Pour assurer
   la compatibilité avec les anciens fichiers déjà assemblés, il coupe leur
   partie grammaire/lexique dès l'ancienne sentinelle `---`.
3. `_load_reference_resources` lit `Global_Manual_V2.md` comme instruction
   système et charge/valide `data/Lexique_ae_V2.json` comme structure JSON.
   Une ressource manquante ou un JSON invalide produit une erreur explicite.
4. `_compose_request_contents` assemble les données de référence puis les
   consignes et la demande lorsque le cache n'est pas disponible. Si le cache
   est utilisé, `contents` ne contient que la consigne et la demande.
5. `traduire_avec_gemini`, `reviser_traduction_avec_gemini` et
   `evaluer_avec_gemini` utilisent cette séparation pour le SDK Gemini officiel,
   comme pour le fallback `google.generativeai`.
6. `modules/conlang-update.py:assembler_prompts` ne génère désormais que les
   consignes de rôle dans les fichiers `prompt_*.txt`. Le manuel et le lexique
   restent leurs propres sources et ne sont pas recopiés dans ces prompts.

## Context Caching

Lorsque `CACHED_CONTEXTS_ACTIVATION` est activé, le cache est créé avec le manuel
dans `system_instruction` et le bloc JSON du lexique dans `contents`. Le prompt
et la phrase ne sont pas mis en cache. La clé locale du cache inclut l'empreinte
du manuel et du lexique : une modification de ces références entraîne la création
d'un cache correspondant aux nouvelles données. Si la création du cache échoue
ou si le cache est désactivé, le manuel reste en `system_instruction` et le
lexique est ajouté au bloc de référence de la requête normale.

## Traduction fiable

Le mode fiable conserve son fonctionnement en deux étapes : premier appel de
traduction, puis appel de révision avec le texte source et la proposition. Le
second appel reçoit à nouveau le manuel V2 en `system_instruction` et le lexique
comme référence; sa consigne de révision et les deux textes sont envoyés dans
`contents`. L'extraction du commentaire pédagogique, le traitement des nombres
en base 12, la journalisation et la sauvegarde continuent après la vérification.

## Diagnostic des contenus transmis

Quand `PRINT_GLOBAL_PROMPT` est activé, `_print_global_prompt` affiche le nom
des fichiers et leur destination (par exemple
`Global_Manual_V2.md -> system_instruction`), puis les données effectivement
transmises et la demande dynamique. Le lexique et le manuel pouvant être
volumineux, cet affichage reste derrière le flag d'administration.

## Vérification

Les tests ciblés de `tests/test_gemini_service.py` vérifient l'assemblage en
mode sans cache, l'utilisation du cache et le maintien des deux appels en mode
fiable, sans dépendre d'une clé API distante.
