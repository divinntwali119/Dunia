# Dunia — Installation locale et déploiement sur Render

Ce guide s'adresse à toute l'équipe. Il explique comment installer le projet sur Windows, macOS ou Linux, utiliser le fichier `.env` transmis par Moustapha, lancer Django et vérifier son fonctionnement. La seconde partie décrit les modifications et les étapes nécessaires pour le déployer sur Render.

> Les étapes locales correspondent au code actuel. Les adaptations Render présentées ci-dessous sont **à appliquer avant le déploiement** : ce guide ne les ajoute pas automatiquement au projet.

- [Installation locale](#installation-locale)
- [Tester le projet](#tester-le-projet)
- [Reprendre le travail au quotidien](#reprendre-le-travail-au-quotidien)
- [Déployer sur Render](#deployer-sur-render)
- [Résoudre les problèmes fréquents](#resoudre-les-problemes-frequents)

<a id="installation-locale"></a>
## Installation locale

### 1. Installer les outils

Prévoir une connexion Internet, Git et **Python 3.13 de préférence**. Les dépendances actuellement installées exigent au minimum Python 3.12. L'environnement du projet a été vérifié avec Python 3.13 ; conserver la même version mineure dans l'équipe évite les différences inutiles.

Le projet utilise Django, `django-environ`, Unfold, Pillow et WhiteNoise. Leurs versions sont fixées dans `requirements.txt` : installer ce fichier, sans remplacer ses versions individuellement.

**Windows**

Installer Python 3.13 depuis [Python.org](https://www.python.org/downloads/) et Git depuis [Git](https://git-scm.com/downloads). Si l'installateur Python propose **Add Python to PATH**, cocher cette option. Fermer puis rouvrir PowerShell et vérifier :

```powershell
py -3.13 --version
git --version
```

**macOS**

Installer Python 3.13 depuis [Python.org](https://www.python.org/downloads/). Dans le Terminal :

```bash
python3.13 --version
git --version
```

Si macOS propose d'installer les outils de ligne de commande Apple pour Git, terminer cette installation.

**Linux**

Sur Ubuntu/Debian :

```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip git
python3 --version
git --version
```

Sur Fedora :

```bash
sudo dnf install python3 python3-pip git
python3 --version
git --version
```

Si `python3 --version` indique une version antérieure à 3.12, installer Python 3.13 avec la méthode adaptée à votre distribution avant de continuer. Si l'exécutable installé s'appelle `python3.13`, utiliser ce nom à la place de `python3` pour créer l'environnement ci-dessous. Sur Debian/Ubuntu, le module `venv` doit correspondre à la version de Python choisie.

### 2. Récupérer le projet

Cloner le dépôt avec l'URL fournie par l'équipe. Remplacer `URL_DU_DEPOT` par cette URL :

```bash
git clone URL_DU_DEPOT Dunia
cd Dunia
```

Si le projet est déjà téléchargé ou cloné, ouvrir un terminal dans son dossier. Toutes les commandes suivantes se lancent depuis la **racine du projet**, là où se trouvent `manage.py` et `requirements.txt`, et non depuis le sous-dossier `Dunia/` contenant `settings.py`.

```text
Dunia/                     ← ouvrir le terminal ici
├── manage.py
├── requirements.txt
├── .env                   ← fichier reçu de Moustapha
├── Dunia/
│   ├── settings.py
│   └── wsgi.py
├── home/
├── formations/
├── news/
├── static/
└── templates/
```

### 3. Placer le fichier `.env`

Copier le fichier reçu de Moustapha **à côté de `manage.py`**. Son nom doit être exactement `.env`, sans extension `.txt`. Sur Windows, afficher les extensions dans l'Explorateur pour le vérifier.

Le code actuel lit deux variables obligatoires :

| Variable | Rôle en local |
| --- | --- |
| `SECRET_KEY` | Clé Django fournie dans le fichier reçu. |
| `DEBUG` | Mettre `True` sur votre machine de développement. |

Vérifier cette ligne dans votre copie locale :

```dotenv
DEBUG=True
```

Conserver la clé reçue. Ne pas publier le `.env` dans Git, un ticket ou une capture d'écran : il est déjà exclu par `.gitignore`. Django le charge automatiquement grâce à `django-environ` ; aucune commande `source .env` n'est nécessaire.

Le fichier `.env` est un fichier de configuration. Le dossier `.venv`, créé à l'étape suivante, contient Python et les packages propres au projet : ce sont deux éléments différents.

### 4. Créer et activer l'environnement virtuel

Chaque personne crée son propre environnement sur son ordinateur. Ne pas copier celui d'un collègue et ne pas le versionner.

**Windows — PowerShell**

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Si PowerShell refuse l'activation parce que l'exécution des scripts est désactivée, autoriser les scripts pour ce terminal uniquement, puis réessayer :

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\.venv\Scripts\Activate.ps1
```

Si la politique de votre entreprise interdit cette modification, utiliser l'invite de commandes `cmd` :

```bat
py -3.13 -m venv .venv
.venv\Scripts\activate.bat
```

**macOS — Terminal**

```bash
python3.13 -m venv .venv
source .venv/bin/activate
```

**Linux — Bash ou Zsh**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Le terminal affiche généralement `(.venv)`. Pour confirmer que le bon Python est utilisé :

```bash
python --version
python -c "import sys; print(sys.executable)"
```

Le chemin affiché doit contenir le dossier `.venv` du projet. **Après activation, utiliser `python` dans toutes les commandes**, quel que soit le système.

### 5. Installer les packages

Dans le terminal où l'environnement est actif :

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pip check
```

La dernière commande doit indiquer `No broken requirements found.`. Ne pas poursuivre si l'installation a échoué. Ne pas utiliser `sudo pip` : les packages doivent rester dans `.venv`.

### 6. Initialiser la base de données

Le projet utilise **SQLite en local**. Aucun serveur PostgreSQL ou MySQL n'est nécessaire pour cette partie.

```bash
python manage.py check
python manage.py migrate
```

`check` vérifie la configuration. `migrate` crée le fichier `db.sqlite3` si nécessaire et applique les migrations déjà présentes dans le dépôt. Il n'est pas nécessaire de lancer `makemigrations` pour installer le projet.

Le fichier `db.sqlite3` est exclu de Git : un nouveau clone commence avec une base vide. Le `.env` ne contient ni formations, ni actualités, ni utilisateurs. Les images éventuellement présentes dans `media/` ne créent pas à elles seules les enregistrements correspondants.

Créer son propre compte administrateur local :

```bash
python manage.py createsuperuser
```

Saisir le nom d'utilisateur, l'adresse e-mail et le mot de passe demandés. Le mot de passe ne s'affiche pas pendant la saisie, c'est normal.

### 7. Lancer le serveur

```bash
python manage.py runserver
```

Garder ce terminal ouvert, puis visiter **http://127.0.0.1:8000/** dans le navigateur. Le terminal doit annoncer le démarrage du serveur à cette adresse. `http://localhost:8000/` fonctionne également.

Pour arrêter le serveur : **Ctrl+C** dans le terminal. Pour utiliser un autre port :

```bash
python manage.py runserver 8001
```

Dans ce cas, ouvrir `http://127.0.0.1:8001/`. `runserver` sert au développement ; le déploiement Render utilisera Gunicorn.

<a id="tester-le-projet"></a>
## Tester le projet

### Vérification dans le navigateur

| Adresse locale | Résultat attendu |
| --- | --- |
| `http://127.0.0.1:8000/` | Page d'accueil Dunia. |
| `http://127.0.0.1:8000/formations/` | Catalogue, éventuellement vide au premier lancement. |
| `http://127.0.0.1:8000/news/` | Actualités, éventuellement vides au premier lancement. |
| `http://127.0.0.1:8000/admin/` | Connexion à l'administration. |

Se connecter avec le compte créé, ajouter une formation et une actualité de test, puis vérifier leur affichage sur le site. Ajouter aussi une image pour vérifier les téléversements. En local avec `DEBUG=True`, Django sert les fichiers de `media/`.

### Tests automatiques

Arrêter le serveur avec Ctrl+C, ou ouvrir un second terminal et y réactiver `.venv`, puis lancer :

```bash
python manage.py check
python manage.py test
```

Résultats attendus : aucune erreur de configuration et `OK` à la fin des tests. Lors de la rédaction de ce guide, **11 tests passent** : pages publiques, contenus, liens, fichiers statiques et publication depuis l'administration.

Les tests Django créent une base de test distincte puis la détruisent. Ils ne remplissent pas votre catalogue local. Cette commande vérifie le comportement automatisé ; la vérification dans le navigateur reste utile pour l'affichage et les images.

<a id="reprendre-le-travail-au-quotidien"></a>
## Reprendre le travail au quotidien

À chaque nouveau terminal, revenir dans le dossier du projet et réactiver l'environnement :

| Terminal | Activation |
| --- | --- |
| PowerShell | `.\.venv\Scripts\Activate.ps1` |
| Invite de commandes Windows | `.venv\Scripts\activate.bat` |
| macOS / Linux, Bash ou Zsh | `source .venv/bin/activate` |

Puis :

```bash
python manage.py runserver
```

Après avoir sauvegardé vos changements et récupéré une mise à jour du dépôt avec `git pull`, synchroniser les dépendances et la base :

```bash
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py test
python manage.py runserver
```

Ne pas recréer `.venv`, le `.env` ou le superutilisateur à chaque démarrage. Pour quitter l'environnement, arrêter le serveur puis taper `deactivate`.

<a id="deployer-sur-render"></a>
## Déployer sur Render

Cette partie est destinée à la personne chargée du déploiement. Elle suppose un dépôt Git accessible à Render et un compte Render. Les modifications de code se font une fois, sont testées puis partagées dans le dépôt.

L'application est un **Web Service Python**. Le point d'entrée est **`Dunia.wsgi:application`**, avec un `D` majuscule. Le code actuel contient déjà WhiteNoise, son middleware, `STATIC_ROOT` et le stockage des fichiers statiques ; il manque notamment Gunicorn, PostgreSQL et les paramètres de domaine. [Guide Django de Render](https://render.com/docs/deploy-django).

### 1. Ajouter les dépendances de production

Depuis un environnement virtuel contenant les dépendances du projet :

```bash
python -m pip install gunicorn "psycopg[binary]"
```

Gunicorn exécute Django sur Render ; Psycopg permet de se connecter à PostgreSQL. `django-environ`, déjà installé, sait lire `DATABASE_URL` : aucun ajout de `dj-database-url` n'est nécessaire. [API de django-environ](https://django-environ.readthedocs.io/en/latest/api.html#environ.Env.db).

Après avoir installé également le package de stockage si vous suivez l'étape 3, enregistrer les versions résolues dans `requirements.txt`. La commande suivante écrit en UTF-8 sur tous les systèmes, y compris Windows PowerShell :

```bash
python -c "from pathlib import Path; import subprocess, sys; Path('requirements.txt').write_text(subprocess.check_output([sys.executable, '-m', 'pip', 'freeze'], text=True), encoding='utf-8')"
```

Faire cette opération dans l'environnement du projet, puis vérifier le diff pour ne pas ajouter les packages d'autres projets. Gunicorn sera lancé sur Linux chez Render ; continuer à utiliser `runserver` pour le développement Windows.

### 2. Adapter `Dunia/settings.py`

Conserver le chargement existant du `.env` et `SECRET_KEY = env.str('SECRET_KEY')`.

**Remplacer** les affectations actuelles de `DEBUG` et `ALLOWED_HOSTS` par :

```python
DEBUG = env.bool('DEBUG', default=False)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['localhost', '127.0.0.1', '[::1]'])
CSRF_TRUSTED_ORIGINS = env.list('CSRF_TRUSTED_ORIGINS', default=[])

render_hostname = env.str('RENDER_EXTERNAL_HOSTNAME', default='')
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)
    CSRF_TRUSTED_ORIGINS.append(f'https://{render_hostname}')

if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

Render fournit `RENDER_EXTERNAL_HOSTNAME`. Les paramètres HTTPS ci-dessus concernent l'application derrière son proxy. Pour un domaine personnalisé, fournir aussi son nom dans `ALLOWED_HOSTS` et son origine HTTPS dans `CSRF_TRUSTED_ORIGINS`. Les hôtes n'ont ni protocole ni chemin ; les origines incluent `https://`. [Guide Render](https://render.com/docs/deploy-django), [paramètres Django du proxy HTTPS](https://docs.djangoproject.com/en/6.0/ref/settings/#secure-proxy-ssl-header).

**Remplacer** le bloc `DATABASES` actuel par :

```python
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    DATABASES = {'default': env.db('DATABASE_URL')}
    DATABASES['default']['CONN_MAX_AGE'] = 60
    DATABASES['default']['CONN_HEALTH_CHECKS'] = True
```

Ainsi, `DEBUG=True` conserve SQLite pour l'équipe et `DEBUG=False` exige une URL de base de production. Ne pas garder un second bloc `DATABASES` plus bas qui écraserait celui-ci.

### 3. Prévoir le stockage des images téléversées

Il faut distinguer deux catégories :

- **`static/`** : ressources du dépôt, collectées au déploiement et servies par WhiteNoise.
- **`media/`** : images ajoutées dans l'administration. Le code actuel ne les sert que lorsque `DEBUG=True`. WhiteNoise ne prend pas en charge ces téléversements en production. [Documentation WhiteNoise](https://whitenoise.readthedocs.io/en/stable/django.html#serving-media-files).

Le disque ordinaire d'un service Render est éphémère : les nouvelles images et une base SQLite locale peuvent disparaître au redémarrage ou au redéploiement. Utiliser PostgreSQL pour les données et un stockage externe pour les images. Un disque persistant nécessite une offre compatible et ne résout pas, à lui seul, la manière de servir les médias. [Limites du stockage Render](https://render.com/docs/free#local-files-lost-on-redeploy).

**Exemple utilisable avec Amazon S3**, à configurer avant de publier des contenus avec images :

1. Préparer un bucket S3 privé et des identifiants applicatifs autorisés à lister ce bucket, lire, écrire et supprimer ses objets. Garder ces accès limités au bucket du projet.
2. Installer le backend, puis réexécuter la commande d'enregistrement de `requirements.txt` de l'étape 1 :

```bash
python -m pip install "django-storages[s3]"
```

3. Ajouter ce bloc **après le bloc `STORAGES` existant**, en conservant son entrée `staticfiles` :

```python
if env.bool('USE_S3', default=False):
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': env.str('AWS_STORAGE_BUCKET_NAME'),
            'region_name': env.str('AWS_S3_REGION_NAME'),
            'access_key': env.str('AWS_ACCESS_KEY_ID'),
            'secret_key': env.str('AWS_SECRET_ACCESS_KEY'),
            'default_acl': None,
            'querystring_auth': True,
            'file_overwrite': False,
            'location': 'media',
        },
    }
```

Ce backend génère des URL signées pour les images. Les templates du projet utilisent déjà `.image.url`. Laisser `USE_S3` absent en local pour conserver les fichiers locaux. Les fichiers existants ne sont pas transférés automatiquement : les importer sous le préfixe `media/` en préservant leurs chemins, ou les téléverser de nouveau. [Configuration et permissions S3](https://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html).

Pour une simple démonstration sans images téléversées, cette configuration externe peut être différée : les images statiques de remplacement restent disponibles. Ne pas considérer les téléversements locaux comme opérationnels en production sans avoir configuré ce stockage.

### 4. Préparer le build

Créer **`.python-version`** à la racine, avec cette seule ligne :

```text
3.13
```

Render accepte une version mineure dans ce fichier et choisit le correctif correspondant disponible. Si vous utilisez plutôt la variable `PYTHON_VERSION`, elle exige une version complète et prend priorité sur le fichier. [Version Python sur Render](https://render.com/docs/python-version).

Créer **`build.sh`** à côté de `manage.py` :

```bash
#!/usr/bin/env bash
set -o errexit

python -m pip install -r requirements.txt
python manage.py collectstatic --noinput
```

Enregistrer ce script avec des fins de ligne **LF**, notamment sur Windows. Render l'appellera avec `bash build.sh`, donc aucune commande `chmod` n'est nécessaire.

Le dossier généré `staticfiles/` ne doit pas être ajouté au dépôt. Corriger la ligne actuelle `staticfiles/k` de `.gitignore` en :

```gitignore
staticfiles/
```

WhiteNoise et `STORAGES['staticfiles']` sont déjà configurés dans le projet : les conserver. `collectstatic` prépare les ressources pour la production ; il ne transfère pas les médias. [Configuration WhiteNoise](https://whitenoise.readthedocs.io/en/stable/django.html).

Avec le `.env` local et `DEBUG=True`, vérifier les modifications avant de les partager :

```bash
python -m pip check
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
git diff
git status --short
```

Enregistrer ensuite les fichiers concernés dans Git et pousser la branche à déployer. Le `.env`, `.venv/`, `db.sqlite3` et les fichiers générés ne doivent pas figurer dans ce commit.

### 5. Créer la base PostgreSQL sur Render

Dans le [tableau de bord Render](https://dashboard.render.com/) :

1. Choisir **New → Postgres** et créer la base du projet.
2. Choisir la même région pour la base et le futur service web.
3. Copier son **Internal Database URL** : elle deviendra `DATABASE_URL` dans le service web. Garder cette URL secrète.

La base Render est indépendante de `db.sqlite3`. `migrate` créera les tables ; il ne copiera pas vos formations, actualités ou comptes locaux. Pour un premier déploiement, créer le compte de production puis saisir les contenus. La reprise de données existantes nécessite un export/import séparé. [Connexions Render Postgres](https://render.com/docs/postgresql-creating-connecting).

### 6. Créer le service web

Choisir **New → Web Service**, connecter le fournisseur Git et sélectionner le dépôt et la branche voulus.

| Champ | Valeur |
| --- | --- |
| Language / Runtime | Python 3 |
| Root Directory | Laisser vide si `manage.py` est à la racine du dépôt. |
| Region | Même région que PostgreSQL. |
| Build Command | `bash build.sh` |
| Pre-Deploy Command, si disponible | `python manage.py migrate --noinput` |
| Start Command | `python -m gunicorn Dunia.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -` |
| Health Check Path | `/` |

`$PORT` est fourni par Render. Conserver cette expression dans la commande du tableau de bord, même si votre ordinateur est sous Windows. [Ports des services web](https://render.com/docs/web-services#port-binding).

La commande **Pre-Deploy** est disponible sur les services web payants. Sur une offre sans cette option, ajouter `python manage.py migrate --noinput` à la fin de `build.sh`. Cette variante applique les migrations pendant le build, même si une étape ultérieure du déploiement échoue : prévoir des migrations compatibles avec la version encore en service. [Étapes d'un déploiement Render](https://render.com/docs/deploys#pre-deploy-command).

### 7. Ajouter les variables d'environnement

Dans **Environment**, renseigner les variables avant de lancer le déploiement :

| Variable | Valeur sur Render |
| --- | --- |
| `SECRET_KEY` | Nouvelle clé aléatoire de production, différente de la clé locale. Utiliser le générateur Render. |
| `DEBUG` | `False` |
| `DATABASE_URL` | Internal Database URL copiée depuis PostgreSQL. |
| `ALLOWED_HOSTS` | Domaine du service, par exemple `dunia-equipe.onrender.com`. Ajouter les domaines personnalisés séparés par des virgules. |
| `CSRF_TRUSTED_ORIGINS` | Origine correspondante, par exemple `https://dunia-equipe.onrender.com`. Séparer plusieurs origines par des virgules. |

Remplacer les domaines d'exemple par ceux du service. Après l'adaptation de `settings.py`, l'hôte `.onrender.com` est aussi ajouté automatiquement grâce à `RENDER_EXTERNAL_HOSTNAME` ; cette variable est fournie par Render.

Pour le stockage S3 de l'étape 3, ajouter également :

| Variable | Valeur |
| --- | --- |
| `USE_S3` | `True` |
| `AWS_STORAGE_BUCKET_NAME` | Nom du bucket. |
| `AWS_S3_REGION_NAME` | Région réelle du bucket. |
| `AWS_ACCESS_KEY_ID` | Identifiant d'accès de l'application. |
| `AWS_SECRET_ACCESS_KEY` | Secret correspondant. |

Saisir les valeurs directement, sans ajouter de guillemets autour. Render propose aussi **Add from .env**, mais il faut alors remplacer les valeurs de développement, notamment la clé et `DEBUG`. Le fichier `.env` local n'a pas besoin d'être envoyé dans Git : les variables Render sont lues par `django-environ`. [Variables et secrets sur Render](https://render.com/docs/configure-environment-variables).

Enregistrer puis lancer le déploiement. Vérifier les logs : installation des dépendances, collecte des statiques, migrations et démarrage de Gunicorn.

### 8. Créer le compte administrateur de production

Si l'offre donne accès au **Shell** du service Render, lancer :

```bash
python manage.py createsuperuser
```

Ce compte est indépendant du compte local. Le shell n'est pas disponible sur un service web gratuit. [Restrictions des offres gratuites](https://render.com/docs/free#other-limitations).

**Variante sans Shell :** ajouter temporairement dans Render les variables `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` et `DJANGO_SUPERUSER_PASSWORD`, avec les valeurs souhaitées, puis utiliser pour un seul déploiement cette Start Command :

```bash
python manage.py createsuperuser --noinput && python -m gunicorn Dunia.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -
```

Les migrations doivent déjà avoir été appliquées. Après la réussite de la création et la vérification de la connexion, rétablir immédiatement la Start Command de l'étape 6, supprimer les trois variables temporaires et redéployer. Si le compte existe déjà, la commande de création échoue : retirer la création de la Start Command au lieu de la relancer. Ne pas laisser le mot de passe dans un script versionné. [Commande Django `createsuperuser`](https://docs.djangoproject.com/en/6.0/ref/django-admin/#createsuperuser).

### 9. Vérifier le site déployé

Ouvrir l'URL **HTTPS** du service et vérifier :

1. L'accueil, `/formations/` et `/news/` répondent sans erreur.
2. `/admin/` accepte la connexion et l'enregistrement d'une formation ou d'une actualité, sans erreur CSRF.
3. Les styles, le logo et les autres fichiers statiques s'affichent.
4. Si S3 est configuré, une image ajoutée depuis l'administration s'affiche et reste accessible après un redéploiement.
5. Les enregistrements et le compte administrateur restent présents après ce redéploiement.

Depuis le Shell Render, si disponible, exécuter aussi :

```bash
python manage.py check --deploy
```

Examiner les avertissements selon la configuration réelle ; les paramètres HTTPS proposés ne règlent pas automatiquement tous les points, notamment HSTS. Cette commande ne remplace pas les tests fonctionnels. [Vérifications Django avant production](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/).

Après les mises à jour, Render peut redéployer automatiquement la branche liée si l'option est activée, ou via **Manual Deploy**. Consulter les logs lorsqu'un déploiement échoue.

### Choisir l'offre

Pour une démonstration, l'offre gratuite peut suffire, avec ses limites : mise en veille après 15 minutes d'inactivité, absence de shell et de disque persistant, et expiration de PostgreSQL gratuit après 30 jours. Pour un site utilisé durablement, choisir des services et une base adaptés avec sauvegardes. Vérifier les conditions au moment de créer les ressources ; elles peuvent évoluer. [Limites actuelles de Render Free](https://render.com/docs/free).

<a id="resoudre-les-problemes-frequents"></a>
## Résoudre les problèmes fréquents

| Problème | Vérification / solution |
| --- | --- |
| `python`, `python3.13` ou `py` introuvable | Vérifier l'installation de Python, rouvrir le terminal et utiliser la commande prévue pour votre système. |
| Création de `.venv` impossible sur Linux | Installer le module `venv` correspondant à votre version de Python ; sur Ubuntu/Debian avec Python système, installer `python3-venv`. |
| Activation PowerShell bloquée | Voir la commande `Set-ExecutionPolicy -Scope Process` ou utiliser `cmd` et `activate.bat`. |
| `No module named django` ou `environ` | Activer `.venv`, vérifier `sys.executable`, puis relancer `python -m pip install -r requirements.txt`. |
| `No matching distribution found` | Vérifier Python : au moins 3.12, de préférence 3.13. Mettre pip à jour, contrôler l'accès au registre de packages et la version demandée. Faire corriger les versions avec l'équipe si nécessaire ; ne pas les modifier au hasard. |
| `Set the SECRET_KEY environment variable` ou erreur sur `DEBUG` | Vérifier le nom `.env`, son emplacement à côté de `manage.py` et les deux variables obligatoires. |
| Le `.env` semble ignoré | Une variable déjà définie dans le terminal a priorité sur le fichier. Vérifier notamment `DEBUG`, puis ouvrir un terminal propre et réactiver `.venv`. |
| `You must set settings.ALLOWED_HOSTS` en local | Avec le code initial, utiliser `DEBUG=True` pour le développement. Pour Render, appliquer les adaptations et déclarer les domaines. |
| `DisallowedHost` / HTTP 400 sur Render | Vérifier le domaine réel dans `ALLOWED_HOSTS`, sans `https://`, et la présence du bloc utilisant `RENDER_EXTERNAL_HOSTNAME`. |
| Erreur CSRF / HTTP 403 lors d'un formulaire sur Render | Vérifier l'origine HTTPS exacte dans `CSRF_TRUSTED_ORIGINS`, les paramètres du proxy et l'usage de HTTPS. |
| `no such table` ou `relation does not exist` | Exécuter les migrations sur la base concernée ; sur Render vérifier que l'étape de migration a réussi. |
| Port 8000 déjà utilisé | Arrêter l'ancien serveur avec Ctrl+C, ou lancer `python manage.py runserver 8001`. |
| Pages sans formations ni actualités | Une base neuve est vide. Ajouter des contenus depuis `/admin/`. |
| Styles absents / erreur de manifeste statique | Vérifier la réussite de `collectstatic`, conserver la configuration WhiteNoise et corriger le fichier manquant indiqué dans les logs. |
| Images de contenus absentes sur Render | Vérifier le stockage des médias et le transfert des fichiers existants ; `collectstatic` et la base PostgreSQL ne stockent pas ces images. |
| Erreur `gunicorn` ou `psycopg` introuvable | Vérifier leur présence dans le `requirements.txt` commité et relancer le déploiement. |
| Connexion PostgreSQL impossible | Vérifier `DATABASE_URL`, la disponibilité de la base et la région commune. L'URL interne est destinée aux services Render. |
| HTTP 500, 502 ou redémarrages | Lire les logs Render et corriger la première erreur : variable manquante, migration, dépendance ou Start Command. Garder `DEBUG=False` sur le site public. |

Pour demander de l'aide à l'équipe, transmettre le système utilisé, la version de Python, la commande exécutée et le message d'erreur, en masquant les secrets et URL de connexion.
