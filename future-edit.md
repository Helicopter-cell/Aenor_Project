@workspace Tu es un expert en déploiement web, Flask et infrastructure PythonAnywhere.

Je souhaite préparer l'application Flask pour qu'elle puisse être déployée publiquement sur la plateforme PythonAnywhere avec le protocole sécurisé HTTPS et une persistance complète de la base SQLite.

Voici les spécifications et configurations requises :

---

### 1. CONFIGURATION DU FICHIER WSGI PYTHONANYWHERE
- Créer un fichier de configuration WSGI adapté à PythonAnywhere (ex: `pythonanywhere_wsgi.py` ou bloc de code pour leur onglet Web).
- Ce fichier doit importer la variable d'application Flask (`app`) à partir du module principal (`app.py`), définir les chemins absolus (`sys.path`) vers le dossier du projet et charger l'environnement virtuel si nécessaire.

---

### 2. SÉCURISATION HTTPS ET SESSION FLASK
- Configurer Flask pour gérer correctement les requêtes passant par le reverse proxy HTTPS de PythonAnywhere (utilisation du middleware `ProxyFix` de `werkzeug.middleware.proxy_fix`).
- S'assurer que les redirections générées par `url_for` respectent le protocole HTTPS.
- Configurer la sécurité des cookies de session dans `app.py` :
  - `SESSION_COOKIE_SECURE = True`
  - `SESSION_COOKIE_HTTPONLY = True`
  - `SESSION_COOKIE_SAMESITE = 'Lax'`

---

### 3. VARIABLES D'ENVIRONNEMENT & BASE DE DONNÉES SQLITE
- Remplacer tout `SECRET_KEY` hardcodé par la lecture d'une variable d'environnement (`os.environ.get('SECRET_KEY')`) tout en prévoyant une valeur de secours locale pour le mode dev.
- S'assurer que le mode debug (`DEBUG = False`) est bien désactivé en production.
- Vérifier que les chemins d'accès à la base SQLite (`SQLite.db`) utilisent des chemins absolus (`Path(__file__).resolve().parent`) afin d'éviter toute erreur de fichier introuvable sur les serveurs de PythonAnywhere.
- Générer ou mettre à jour le fichier `requirements.txt` avec les dépendances actuelles du projet.

---

### DIRECTIVES AGENTIQUES :
1. **Inspection** : Analyse la structure de `app.py`, la gestion des chemins de `SQLite.db` et les dépendances.
2. **Modifications** : Applique les ajustements dans `app.py` pour `ProxyFix`, la sécurisation des sessions et les variables d'environnement.
3. **Configuration WSGI** : Fournis le code exact à insérer dans le fichier WSGI de PythonAnywhere.
4. **Guide de Déploiement** : Rédige un mini-guide étape par étape pour PythonAnywhere (cloner le repo Git via Bash, créer le venv, installer `requirements.txt`, configurer la section "Web" et activer l'option "Force HTTPS").