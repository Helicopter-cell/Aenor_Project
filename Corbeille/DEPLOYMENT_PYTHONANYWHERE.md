# Déploiement sur PythonAnywhere

## 1. Préparer le compte

Dans un terminal Bash PythonAnywhere, remplacer `USER` par le nom du compte :

```bash
cd ~
git clone https://github.com/USER/REPOSITORY.git aenor-app
cd ~/aenor-app
python3.12 -m venv ~/.virtualenvs/aenor-venv
source ~/.virtualenvs/aenor-venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Si la version Python choisie dans l'onglet **Web** est différente, utiliser cette même version pour créer le venv.

## 2. Variables d'environnement

Dans l'onglet **Web**, section **Environment variables**, ajouter au minimum :

```text
SECRET_KEY=<clé-secrète-aléatoire-et-longue>
GEMINI_API_KEY=<clé-api-gemini>
```

Ne pas publier ces valeurs dans Git. La base persistante est `~/aenor-app/data/SQLite.db`; elle doit rester dans le stockage PythonAnywhere, et non dans `/tmp`.

## 3. Configuration Web

Créer une application **Manual configuration** avec la même version Python que le venv. Dans **Virtualenv**, saisir :

```text
/home/USER/.virtualenvs/aenor-venv
```

Dans **WSGI configuration file**, remplacer le contenu par le code suivant, en adaptant `PROJECT_DIR` et `VENV_DIR` :

```python
import os
import sys

PROJECT_DIR = "/home/USER/aenor-app"
if PROJECT_DIR not in sys.path:
    sys.path.insert(0, PROJECT_DIR)

VENV_DIR = "/home/USER/.virtualenvs/aenor-venv"
activate_this = os.path.join(VENV_DIR, "bin", "activate_this.py")
if os.path.isfile(activate_this):
    with open(activate_this, encoding="utf-8") as file_handle:
        exec(compile(file_handle.read(), activate_this, "exec"), {"__file__": activate_this})

from app import app as application
```

Le fichier `pythonanywhere_wsgi.py` du dépôt contient la même logique et peut servir de référence; l'onglet WSGI attend toutefois une variable nommée `application`.

## 4. HTTPS et rechargement

Dans **Web**, cliquer sur **Reload**, puis activer **Force HTTPS**. Le middleware `ProxyFix` de l'application récupère le protocole HTTPS transmis par le reverse proxy PythonAnywhere. Les cookies de session sont Secure, HttpOnly et SameSite=Lax.

## 5. Vérification

Ouvrir l'URL HTTPS et vérifier une route qui utilise la session. En cas d'erreur, consulter le fichier **Error log** de l'onglet Web. Après une mise à jour Git :

```bash
cd ~/aenor-app
git pull
source ~/.virtualenvs/aenor-venv/bin/activate
pip install -r requirements.txt
```

Puis cliquer à nouveau sur **Reload**. Faire une sauvegarde de `data/SQLite.db` avant toute opération de maintenance.
