@workspace Tu es un expert en développement web et architecture CSS.

Je souhaite refactoriser mon fichier CSS unique en le découpant en plusieurs feuilles de style plus petites, modularisées et maintenables (architecture de type ITCSS ou 7-1 pattern adapté).

Voici les tâches à accomplir :

1. **Analyse et Proposition d'Architecture** :
   - Analyse la structure actuelle de mon CSS.
   - Propose un découpage logique sous forme d'arborescence de dossiers/fichiers (ex: `base/`, `components/`, `layout/`, `pages/`, etc.).
   - Explique brièvement le rôle de chaque fichier proposé.

2. **Refactorisation du Code** :
   - Répartis le code existant dans ces nouveaux fichiers modulaires.
   - Crée un fichier principal d'importation (`main.css` ou `index.css`) qui regroupe tous les sous-fichiers via `@import` ou selon la méthode recommandée pour notre stack.

3. **Validation et Non-Régression** :
   - Assure-toi qu'aucune règle CSS n'est perdue ou dupliquée.
   - Conserve l'ordre de priorité des sélecteurs pour ne pas casser le rendu visuel actuel de l'application.

Propose d'abord ton plan de découpage avec la liste des fichiers à créer avant d'effectuer les modifications dans le workspace.