@workspace Tu es un expert en développement web (HTML/CSS, JavaScript/Chart.js), Flask et SQLite.

Je souhaite créer une nouvelle page publique pour l'application Aënor dédiée aux retours et commentaires des utilisateurs, en conservant strictement la charte graphique et le design des autres pages existantes.

Voici les spécifications techniques et fonctionnelles à mettre en œuvre :

---

### 1. STRUCTURE ET BASE DE DONNÉES (SQLite)
- Créer une nouvelle table dans SQLite (ex: `feedback` ou `comments`) pour stocker :
  - `id` (INTEGER PRIMARY KEY)
  - `target_element` (TEXT) : le nom de l'élément concerné.
  - `content` (TEXT) : le texte du commentaire.
  - `created_at` (DATETIME) : la date et l'heure de soumission.
  - `likes_count` (INTEGER DEFAULT 0) : le nombre de mentions "J'aime".
- Définir une liste fixe d'éléments sélectionnables (ex: "Grammaire", "Lexique", "Traducteur", "Interface", "Exercices", "Problèmes techniques", "Autre").

---

### 2. INTERFACE UTILISATEUR & DISPOSITION (HTML/CSS)
- **Zone Centrale** : Un formulaire clair et intuitif permettant à l'utilisateur de sélectionner un élément dans la liste déroulante et de rédiger son commentaire.
- **Disposition des commentaires ("Flottants")** :
  - Disposer les cartes de commentaires autour du formulaire central sous forme de bulles ou cartes interactives.
  - Aperçu réduit par défaut : affichage du nom de l'élément, d'un extrait du texte, de la date et du bouton "Like".
  - **Interaction** : Au clic sur une carte, ouvrir un modale ou agrandir la carte pour afficher le contenu complet du commentaire.

---

### 3. FILTRES, TRI ET INTERACTIONS (JavaScript / Flask)
- Implémenter une barre d'outils dynamique (filtres et tri) permettant de :
  - **Filtrer** par élément concerné (afficher un élément spécifique ou "Tous").
  - **Trier** par :
    - Date (plus récents / plus anciens)
    - Popularité (nombre de likes)
    - Longueur du texte (taille du commentaire)
- **Système de Like** : Ajouter une route Flask (ex: `/api/like_comment/<id>`) permettant d'incrémenter les likes en AJAX sans recharger la page.

---

### 4. RESPECT DU DESIGN SYSTEM
- Réutiliser la structure de mise en page globale (`base.html` ou équivalent) pour garantir une parfaite cohérence visuelle.
- Appliquer les styles CSS existants pour la typographie, les boutons et les couleurs, avec des classes dédiées si besoin d'isoler les styles spécifiques aux cartes flottantes.

---

### DIRECTIVES AGENTIQUES :
1. **Inspection** : Analyse la structure de la base de données SQLite et les templates Jinja2 existants pour s'aligner sur la charte graphique (Lit tous les fichiers CSS) et l'architecture du projet.
2. **Implémentation Backend** : Crée les routes Flask nécessaires (affichage de la page, soumission du commentaire, filtrage/tri et API pour les likes).
3. **Implémentation Frontend** : Rédige le template HTML, le CSS dédié aux cartes/animations et le JS pour les filtres et les interactions AJAX.
4. **Validation** : Vérifie l'intégration du responsive design et présente la liste des fichiers créés/modifiés.