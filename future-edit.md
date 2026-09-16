@workspace Tu es un expert en développement web (HTML/CSS, JavaScript).

Je souhaite améliorer la lisibilité de la page `cours.html` (qui affiche le lexique) en rendant les différentes catégories de mots pliables/dépliables dynamiquement.

Voici les spécifications techniques à mettre en œuvre :

---

### 1. INTERACTION ET ACCORDÉON (JavaScript)
- Rendre chaque section/catégorie de mots du lexique réductible : par défaut ou au clic, seule la ligne du titre de la catégorie doit être visible.
- Ajouter un indicateur visuel (ex: une flèche ou chevron `▶` / `▼`) situé immédiatement à gauche de chaque titre de catégorie.
- **Comportement** : Un clic sur la flèche (ou sur l'en-tête de la catégorie) doit masquer ou afficher la liste de mots correspondante de manière fluide.
- **Contrainte stricte** : L'ouverture/fermeture doit se faire 100 % en JavaScript côté client, sans aucun rechargement de page (pas d'appel serveur).

---

### 2. INTÉGRATION ET STYLE (HTML/CSS)
- **Respect du design** : Conserver strictement la charte graphique globale, les couleurs et la typographie existantes de `cours.html`.
- **Stylisation des flèches** : Ajouter une animation CSS légère (ex: rotation de 90° de la flèche) lors de l'ouverture d'une section.
- Utiliser idéalement les balises HTML sémantiques `<details>` et `<summary>` avec un style personnalisé, ou une structure personnalisée en JS léger (`classList.toggle`).

---

### DIRECTIVES AGENTIQUES :
1. **Inspection** : Analyse le fichier `cours.html` ainsi que le CSS et le JS associés pour comprendre la structure actuelle des catégories de mots.
2. **Implémentation** : Applique directement les modifications dans `cours.html` (et dans les fichiers CSS/JS dédiés si la logique y est séparée).
3. **Validation** : Vérifie que le style global est préservé, qu'aucune régression visuelle n'est présente sur mobile/desktop, et résume les fichiers modifiés.