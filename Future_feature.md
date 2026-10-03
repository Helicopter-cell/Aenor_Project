Le document `feature_backlog.md` est une analyse d'architecture et un backlog produit pour l'application **Aënor** (apprentissage et exploration d'une langue construite via Flask, SQLite, Obsidian et Gemini).

---

### 1. Diagnostic de l'existant & Risques clés

* **Dette monolithique** : La quasi-totalité de la logique (routes, requêtes SQLite, orchestration Gemini, administration) est concentrée dans `app.py`.


* **Sécurité & Robuste** : Administration protégée par un mot de passe partagé (avec fallback par défaut), absence de CSRF/rate-limiting sur les endpoints mutatifs et dépendance directe aux API Gemini sans *circuit breaker*.


* **Persistance & Données** : Multiplication des sources de vérité (SQLite, fichiers JSON, fichiers Markdown) avec des initialisations et migrations implicites au démarrage.



---

### 2. Fonctionnalités les plus prometteuses (Cœur Métier)

* **Moteur linguistique déterministe hybride** :


* *Principe* : Traiter les règles simples/reproductibles de manière locale (lexique, grammaire, base 12) et n'invoquer l'IA Gemini que pour les phrases complexes ou ambiguës.


* *Impact* : Réduction drastique des coûts d'API, réponse plus rapide et maîtrise de la norme linguistique.




* **Analyse morphologique & Génération de formes** :


* *Principe* : Décomposer un mot Aënor (racine, affixes, temps, mode) pour expliquer sa construction.




* **Parcours adaptatif & Répétition espacée (SRS)** :


* *Principe* : Proposer un système de cartes mémoire/exercices calibré selon les erreurs passées et les courbes d'oubli de l'utilisateur.




* **Workflow d'édition & Révision humaine des traductions IA** :


* *Principe* : Permettre à l'administrateur/linguiste de corriger ou valider les propositions de l'IA pour enrichir le lexique officiel.





---

### 3. Améliorations UX / UI Utiles

* **Tableau de bord personnalisé & Recherche globale** : Permettre de chercher un mot, une règle ou une note Obsidian depuis n'importe quel écran.


* **Résultat de traduction enrichi** : Ajout de la synthèse vocale/audio (via la phonétique déjà générée), option de mise en favoris et explication des doutes de traduction.


* **Carte Obsidian optimisée** : Ajout de filtres par dossier/type, mode plein écran et légende sur la vue du coffre.



---

### 4. Refactorisation Technique Prioritaire

1. **Architecture en Blueprints** : Découper `app.py` en modules/services distincts (API Gemini, routes, repositories).


2. **Gestion des accès & Securité** : Mise en place de jetons CSRF, limitation de débit (rate limiting) et stockage sécurisé des clés.


3. **Mise en cache & Indexation** : Mettre en cache le scan du coffre Obsidian et le lexique pour éviter de relire les fichiers à chaque requête HTTP.


4. **Tests automatisés** : Créer un dossier `tests/` pour valider la logique de conversion et la gestion des erreurs API.



---

### 5. Ordre de livraison recommandé

```
[Phase 1 : Sécurité & Stabilité] ──> [Phase 2 : Refactorisation app.py & Cache]
                                              │
                                              ▼
[Phase 4 : UI/UX & Obsidian]     <── [Phase 3 : Moteur Hybride & Exercices SRS]

```