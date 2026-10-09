# Dunia — Installation locale et déploiement sur Render

Ce guide s'adresse à toute l'équipe. Il explique comment installer le projet sur Windows, macOS ou Linux, utiliser le fichier `.env` transmis par Moustapha, lancer Django et vérifier son fonctionnement. La seconde partie décrit les modifications et les étapes nécessaires pour le déployer sur Render.

> La configuration de déploiement Render est préparée dans le dépôt. Les étapes ci-dessous décrivent son application dans le tableau de bord et les vérifications avant mise en ligne.

- [Installation locale](#installation-locale)
- [Fonctionnalités disponibles](#fonctionnalites)
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

Copier le fichier reçu de Moustapha **à côté de `manage.py`**. Son nom doit être exactement `.env`, sans extension `.txt`. Sur Windows, afficher les extensions dans l'Explorateur pour le vérifier. Si aucun fichier n'a été fourni, copier `.env.example` en `.env`, puis remplacer la clé d'exemple par une valeur aléatoire.

Le code actuel lit deux variables obligatoires :

| Variable | Rôle en local |
| --- | --- |
| `SECRET_KEY` | Clé Django fournie dans le fichier reçu ou générée localement. |
| `DEBUG` | Mettre `True` sur votre machine de développement. |

Vérifier cette ligne dans votre copie locale :

```dotenv
DEBUG=True
```

Conserver la clé reçue. Ne pas publier le `.env` dans Git, un ticket ou une capture d'écran : il est déjà exclu par `.gitignore`. Django le charge automatiquement grâce à `django-environ` ; aucune commande `source .env` n'est nécessaire.

Le fichier `.env` est un fichier de configuration. Le dossier `.venv`, créé à l'étape suivante, contient Python et les packages propres au projet : ce sont deux éléments différents.

En local, les e-mails sont simulés par Django et leur contenu (liens de confirmation newsletter et de réinitialisation) s'affiche dans le terminal du serveur. Pour envoyer de vrais e-mails en production, configurer le serveur SMTP et `DEFAULT_FROM_EMAIL`.

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

<a id="fonctionnalites"></a>
## Fonctionnalités disponibles

- **Formations** : catalogue et fiche de détail avec format, dates, niveau, durée, lieu, formateur, tarif et nombre de places. Les informations facultatives se gèrent dans `/admin/`.
- **Inscription** : créer un compte apprenant, fournir un téléphone/WhatsApp et accepter le contact de suivi. Les demandes et leur état sont consultables par l’équipe dans l’administration.
- **Places et liste d’attente** : une place est réservée pendant l’attente du paiement; si la session est complète, la demande rejoint une liste ordonnée. Annuler une inscription dans l’administration libère la place et propose automatiquement la prochaine place disponible.
- **Espace apprenant** : consulter les inscriptions, déclarer un paiement, accéder aux leçons et ressources après confirmation, suivre la progression et obtenir une attestation imprimable après avoir terminé toutes les leçons publiées.
- **Mobile Money** : le site enregistre l’opérateur, la référence et une preuve facultative. L’équipe vérifie puis approuve ou rejette la déclaration dans l’administration. **Aucun transfert n’est débité ou vérifié automatiquement** : avant production, renseigner les coordonnées officielles avec `MOBILE_MONEY_INSTRUCTIONS`. Une API opérateur nécessite le choix d’un prestataire et des identifiants marchands.
- **Newsletter** : formulaire avec consentement, confirmation d’adresse par e-mail, enregistrement en administration et désinscription par lien individuel. Les nouvelles formations et actualités publiées sont envoyées aux abonnés confirmés.
- **Notifications Push Web** : Dunia envoie les notifications directement depuis Django avec Web Push et VAPID. Configurer `WEBPUSH_VAPID_PUBLIC_KEY`, `WEBPUSH_VAPID_PRIVATE_KEY`, `WEBPUSH_CONTACT_EMAIL` et `WEBPUSH_ENABLED=True` dans l’environnement serveur. Générer une paire de clés avec `python manage.py generate_vapid_keys` et conserver la clé privée secrète. Les navigateurs exigent HTTPS (localhost est accepté pour le développement); chaque appareil doit autoriser les notifications. Sur iOS/iPadOS 16.4+, l’installation sur l’écran d’accueil est nécessaire.

Pour activer les e-mails réels et les push, définir `SITE_URL`, `DEFAULT_FROM_EMAIL`, les variables SMTP et les variables Web Push dans l’environnement du serveur. Ne jamais versionner les secrets. Les réglages commentés de [.env.example](.env.example) donnent la liste des options disponibles. Après le déploiement du code, exécuter `python manage.py migrate` pour créer les tables d’appareils et de campagnes push.

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

Résultats attendus : aucune erreur de configuration et `OK` à la fin des tests. La suite comprend actuellement **19 tests** couvrant pages publiques, inscriptions, paiements déclaratifs, cours, progression, attestations, newsletter, notifications et administration.

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

> **Important — offre gratuite :** elle convient à une démonstration, pas à la conservation de données de production. Le service web s'endort, son disque local est éphémère et la base PostgreSQL gratuite expire après 30 jours ; après une période de grâce de 14 jours, elle est supprimée et n'a pas de sauvegardes. Utiliser une base payante avec sauvegardes avant d'y enregistrer des comptes, paiements ou données durables. Vérifier les conditions dans [la documentation Render Free](https://render.com/docs/free).

L'application est un **Web Service Python** avec le point d'entrée **`Dunia.wsgi:application`**. Les réglages PostgreSQL, HTTPS, Gunicorn, stockage objet privé S3-compatible, collecte des statiques et migrations sont préparés dans le dépôt. Le fichier `render.yaml` propose un Blueprint Frankfurt gratuit pour une démonstration. Il faut lui fournir un bucket objet durable et remplacer le plan PostgreSQL gratuit pour un usage de production.

### 1. Dépendances et runtime

`requirements.txt` contient les dépendances verrouillées de l'application, notamment Gunicorn, Psycopg et `django-storages` pour S3. `.python-version` sélectionne Python 3.14. Render choisit le dernier correctif disponible de cette version mineure. Aucun `pip freeze` depuis un environnement global n'est nécessaire.

### 2. Configuration Django déjà préparée

`Dunia/settings.py` conserve SQLite en local avec `DEBUG=True`; en production (`DEBUG=False`), `DATABASE_URL` est obligatoire et configure PostgreSQL. Le domaine `.onrender.com` est ajouté automatiquement à `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` à partir de `RENDER_EXTERNAL_HOSTNAME`. HTTPS, proxy et cookies sécurisés sont activés pour `DEBUG=False`. Le Blueprint génère une clé secrète de production, distincte de la clé locale.

### 3. Prévoir le stockage des images téléversées

Il faut distinguer deux catégories :

- **`static/`** : ressources du dépôt, collectées au déploiement et servies par WhiteNoise.
- **`media/`** : images téléversées dans l'administration. Elles sont stockées dans un bucket objet privé S3-compatible ; les URL générées sont signées. Les ressources pédagogiques privées et preuves de paiement utilisent un préfixe privé séparé et restent servies par les vues Django avec vérification d'accès. WhiteNoise ne prend pas en charge les téléversements.

Le disque d'un service web Render gratuit est éphémère ; ne pas y conserver SQLite ou des téléversements. Le stockage objet est séparé de Render et peut avoir ses propres limites ou coûts. Garder le bucket privé et limiter ses identifiants au bucket de l'application.

Configurer un bucket S3 ou compatible avant le premier déploiement :

1. Créer un bucket **privé** et des identifiants à permissions minimales de lecture, écriture, suppression et listage sur ce bucket.
2. Dans Render, renseigner `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY`. Le Blueprint demande ces valeurs sans les enregistrer dans Git. Pour un fournisseur compatible nécessitant une URL, ajouter `AWS_S3_ENDPOINT_URL`. Pour Cloudflare R2, la région est généralement `auto`; utiliser l'endpoint indiqué par Cloudflare. Ne pas rendre le bucket public : les URL des médias sont signées.
3. Les fichiers existants de `media/` ne sont pas envoyés automatiquement au bucket. Si les contenus locaux sont importés, copier les fichiers en conservant le préfixe `media/` et leurs chemins relatifs, ou les téléverser de nouveau. Les comptes, contenus de la base locale et médias ne sont pas transférés par le déploiement.

Le stockage objet doit être configuré avant le premier déploiement avec des uploads. En production, l'application refuse de démarrer si ce stockage durable n'est pas activé.

### 4. Préparer le build

`.python-version` et `build.sh` sont déjà présents. Render exécute `bash build.sh` : le script installe les packages, lance `collectstatic` puis `migrate --noinput`. Cette migration au build évite d'exiger une commande Pre-Deploy, réservée aux plans payants. Les migrations ne copient pas les données locales. WhiteNoise sert les statiques; `.gitignore` exclut déjà `staticfiles/`, `private_media/`, `.env` et SQLite.

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

### 5. Créer les ressources Render

Méthode recommandée : dans le [tableau de bord Render](https://dashboard.render.com/), ouvrir **Blueprints → New Blueprint Instance**, connecter le dépôt GitHub contenant `render.yaml`, puis appliquer le Blueprint. Il crée le Web Service et PostgreSQL dans la région Frankfurt. Saisir les identifiants du bucket privé demandés à la création ; les secrets ne sont pas enregistrés dans Git. Ne pas lancer le service avec des valeurs S3 factices.

La base créée par le Blueprint est indépendante de `db.sqlite3`. `migrate` crée les tables, mais ne copie ni comptes, ni formations, ni actualités. Huit images sont actuellement versionnées sous `media/`; elles doivent aussi être copiées dans le bucket sous le préfixe `media/` si elles sont référencées par des données importées. La reprise des données locales nécessite un export/import séparé. [Connexions Render Postgres](https://render.com/docs/postgresql-creating-connecting).

Le Blueprint utilise PostgreSQL gratuit uniquement pour une démonstration. Pour des données durables, créer/choisir une base payante avec sauvegardes et l'associer au service à la place.

Pour une création manuelle, commencer par **New → Postgres**, choisir la région du service, puis ajouter son **Internal Database URL** comme variable secrète `DATABASE_URL` au Web Service. Garder cette URL confidentielle.

### 6. Configuration du service (si création manuelle)

Si vous avez appliqué le Blueprint de l'étape précédente, passez à l'étape 7.

Choisir **New → Web Service**, connecter le fournisseur Git et sélectionner le dépôt et la branche voulus.

| Champ | Valeur |
| --- | --- |
| Language / Runtime | Python 3 |
| Root Directory | Laisser vide si `manage.py` est à la racine du dépôt. |
| Region | Même région que PostgreSQL. |
| Build Command | `bash build.sh` |
| Pre-Deploy Command | Laisser vide : `build.sh` lance déjà les migrations pour le plan gratuit. |
| Start Command | `python -m gunicorn Dunia.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -` |
| Health Check Path | `/` |

`$PORT` est fourni par Render. Conserver cette expression dans la commande du tableau de bord, même si votre ordinateur est sous Windows. [Ports des services web](https://render.com/docs/web-services#port-binding).

Le Blueprint utilise le plan gratuit, sans commande Pre-Deploy. Pour un service payant, déplacer `python manage.py migrate --noinput` du script de build vers le champ **Pre-Deploy Command** si disponible. Les migrations exécutées pendant le build peuvent être appliquées même si une étape ultérieure échoue ; garder les changements de schéma compatibles avec la version encore en service.

### 7. Ajouter les variables d'environnement

Dans **Environment**, le Blueprint configure `SECRET_KEY`, `DEBUG`, `DATABASE_URL` et `USE_S3`. Il demande les informations du bucket. Pour une création manuelle, renseigner les variables avant de lancer le déploiement :

| Variable | Valeur sur Render |
| --- | --- |
| `SECRET_KEY` | Nouvelle clé aléatoire de production, différente de la clé locale. Utiliser le générateur Render. |
| `DEBUG` | `False` |
| `DATABASE_URL` | Internal Database URL copiée depuis PostgreSQL. |
| `ALLOWED_HOSTS` | Le domaine `.onrender.com` est ajouté automatiquement. Ajouter les hôtes personnalisés sans protocole. |
| `CSRF_TRUSTED_ORIGINS` | L'origine `.onrender.com` est ajoutée automatiquement. Ajouter les origines personnalisées avec `https://`. |

Le Blueprint active le stockage objet et demande les variables suivantes :

| Variable | Valeur |
| --- | --- |
| `USE_S3` | `True` |
| `AWS_STORAGE_BUCKET_NAME` | Nom du bucket. |
| `AWS_S3_REGION_NAME` | Région réelle du bucket. |
| `AWS_ACCESS_KEY_ID` | Identifiant d'accès de l'application. |
| `AWS_SECRET_ACCESS_KEY` | Secret correspondant. |
| `AWS_S3_ENDPOINT_URL` | Endpoint du fournisseur si le service n'est pas AWS S3 (par exemple R2). |

Pour un fournisseur S3-compatible, ajouter `AWS_S3_ENDPOINT_URL` si nécessaire. Le stockage doit être disponible au premier lancement. Le domaine `.onrender.com` est ajouté automatiquement à `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS`; pour un domaine personnalisé, ajouter son nom et son origine HTTPS. `SITE_URL` utilise par défaut le nom d'hôte Render ; le remplacer pour un domaine personnalisé.

Pour les notifications Web Push, ajouter une paire VAPID correspondante à l'environnement Render :

| Variable | Valeur |
| --- | --- |
| `WEBPUSH_VAPID_PUBLIC_KEY` | Clé publique issue de `python manage.py generate_vapid_keys`. |
| `WEBPUSH_VAPID_PRIVATE_KEY` | Clé privée correspondante ; la saisir directement dans Render et ne jamais la versionner ni la partager. |
| `WEBPUSH_ENABLED` | `True` ; l'application garde néanmoins le push désactivé tant que les deux clés ne sont pas présentes. |
| `WEBPUSH_CONTACT_EMAIL` | Adresse de contact VAPID, facultative si la valeur par défaut convient. |

Conserver la même paire de clés après l'activation. Une paire différente oblige les appareils à se réabonner. Le panneau **Alertes** reste désactivé tant que Render ne reçoit pas les deux clés.

Pour les e-mails, ajouter les paramètres SMTP d'un fournisseur externe si les e-mails de bienvenue et de réinitialisation sont nécessaires. Les services Render gratuits bloquent les ports SMTP 25, 465 et 587 ; utiliser un fournisseur et un port autorisés.

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
4. Une image ajoutée depuis l'administration s'affiche et reste accessible après un redéploiement du service.
5. Les enregistrements et le compte administrateur restent présents après ce redéploiement.

Vérifier localement le comportement de configuration de production avec les variables d'environnement Render, et exécuter `python manage.py check --deploy`. Utiliser une vraie clé secrète longue et aléatoire pour ce contrôle ; ne pas conserver les valeurs temporaires d'exemple. La configuration préparée doit au minimum fournir `DEBUG=False`, une `DATABASE_URL`, l'hôte Render et la configuration du bucket. Examiner les avertissements selon la politique de domaine réelle ; cette commande ne remplace pas les tests fonctionnels. [Vérifications Django avant production](https://docs.djangoproject.com/en/6.0/howto/deployment/checklist/).

Depuis le Shell Render, si disponible, exécuter aussi :

```bash
python manage.py check --deploy
```

Examiner les avertissements selon la configuration réelle ; les paramètres HTTPS ne règlent pas automatiquement tous les points, notamment la politique HSTS. Cette commande ne remplace pas les tests fonctionnels.

Après les mises à jour, Render peut redéployer automatiquement la branche liée si l'option est activée, ou via **Manual Deploy**. Consulter les logs lorsqu'un déploiement échoue.

### Choisir l'offre

Le gratuit convient à une démonstration seulement : le service s'endort après 15 minutes d'inactivité, n'a ni Shell ni disque persistant, et PostgreSQL expire après 30 jours. Render le supprime après 14 jours supplémentaires et ne fournit pas de sauvegardes pour ce plan. Pour un site durable, choisir une base payante avec sauvegardes et vérifier les tarifs avant création. [Limites actuelles de Render Free](https://render.com/docs/free).

<a id="resoudre-les-problemes-frequents"></a>
## Résoudre les problèmes fréquents

| Problème | Vérification / solution |
| --- | --- |
| `python`, `python3.14` ou `py` introuvable | Vérifier l'installation de Python, rouvrir le terminal et utiliser la commande prévue pour votre système. |
| Création de `.venv` impossible sur Linux | Installer le module `venv` correspondant à votre version de Python ; sur Ubuntu/Debian avec Python système, installer `python3-venv`. |
| Activation PowerShell bloquée | Voir la commande `Set-ExecutionPolicy -Scope Process` ou utiliser `cmd` et `activate.bat`. |
| `No module named django` ou `environ` | Activer `.venv`, vérifier `sys.executable`, puis relancer `python -m pip install -r requirements.txt`. |
| `No matching distribution found` | Render utilise Python 3.14 via `.python-version`. Contrôler l'accès au registre et la version demandée ; ne pas modifier les dépendances au hasard. |
| `Set the SECRET_KEY environment variable` ou erreur sur `DEBUG` | Vérifier le nom `.env`, son emplacement à côté de `manage.py` et les deux variables obligatoires. |
| Le `.env` semble ignoré | Une variable déjà définie dans le terminal a priorité sur le fichier. Vérifier notamment `DEBUG`, puis ouvrir un terminal propre et réactiver `.venv`. |
| `You must set settings.ALLOWED_HOSTS` en local | Vérifier `DEBUG=True` dans le `.env` de développement. Sur Render, `RENDER_EXTERNAL_HOSTNAME` est ajouté automatiquement ; ajouter manuellement les domaines personnalisés. |
| `DisallowedHost` / HTTP 400 sur Render | Vérifier le domaine personnalisé dans `ALLOWED_HOSTS`, sans `https://`. |
| Erreur CSRF / HTTP 403 lors d'un formulaire sur Render | Vérifier l'origine HTTPS exacte dans `CSRF_TRUSTED_ORIGINS`, les paramètres du proxy et l'usage de HTTPS. |
| `no such table` ou `relation does not exist` | Exécuter les migrations sur la base concernée ; sur Render vérifier que l'étape de migration a réussi. |
| Port 8000 déjà utilisé | Arrêter l'ancien serveur avec Ctrl+C, ou lancer `python manage.py runserver 8001`. |
| Pages sans formations ni actualités | Une base neuve est vide. Ajouter des contenus depuis `/admin/`. |
| Styles absents / erreur de manifeste statique | Vérifier la réussite de `collectstatic`, conserver la configuration WhiteNoise et corriger le fichier manquant indiqué dans les logs. |
| Images de contenus absentes sur Render | Vérifier le bucket, les identifiants et l'endpoint S3 ; `collectstatic` et PostgreSQL ne stockent pas ces images. Importer les fichiers existants sous `media/` en préservant leurs chemins. |
| Erreur `gunicorn` ou `psycopg` introuvable | Vérifier leur présence dans le `requirements.txt` commité et relancer le déploiement. |
| Connexion PostgreSQL impossible | Vérifier `DATABASE_URL`, la disponibilité de la base et la région commune. L'URL interne est destinée aux services Render. |
| HTTP 500, 502 ou redémarrages | Lire les logs Render et corriger la première erreur : variable manquante, migration, dépendance ou Start Command. Garder `DEBUG=False` sur le site public. |

Pour demander de l'aide à l'équipe, transmettre le système utilisé, la version de Python, la commande exécutée et le message d'erreur, en masquant les secrets et URL de connexion.
