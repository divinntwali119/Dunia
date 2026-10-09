# Héberger Dunia sur Render — guide pas à pas

Ce guide décrit le déploiement **de ce projet Django** depuis un nouveau compte Render jusqu'à l'ouverture du site en HTTPS. Il utilise le Blueprint déjà présent dans le dépôt : une application Django sur Render, une base PostgreSQL Render dans la même région et un stockage durable Cloudflare R2 pour les images. Il ne faut ni installer Neon ni modifier le code pour suivre ce parcours.

> **À lire avant de commencer — limites du gratuit.** Render Free convient à une démonstration ou à des essais, pas à des données de production à conserver. Au 9 octobre 2026, la documentation Render indique que le service Web gratuit s'endort après 15 minutes sans trafic, que son disque est éphémère, et que la base PostgreSQL gratuite est limitée à 1 Go, expire 30 jours après sa création puis est supprimée après 14 jours de grâce si elle n'est pas mise à niveau. Elle n'a pas de sauvegardes. Une seule base PostgreSQL gratuite peut être active par workspace. Vérifier les règles et prix actuels avant de commencer : [limites Render Free](https://render.com/docs/free). Pour des comptes, paiements ou données importantes, prévoir un plan payant et des sauvegardes avant la mise en ligne.

## 1. Ce qui est déjà préparé dans Dunia

Le dépôt GitHub contient déjà les éléments de déploiement. Le Blueprint [render.yaml](render.yaml) prévoit un service Web et PostgreSQL gratuits en région Frankfurt. Le script [build.sh](build.sh) installe les dépendances, collecte les fichiers statiques puis applique les migrations. La version Python est fixée par [.python-version](.python-version). L'application démarre avec Gunicorn sur `Dunia.wsgi:application`.

En production, les réglages de [Dunia/settings.py](Dunia/settings.py) exigent PostgreSQL et un stockage objet durable pour les médias. WhiteNoise sert les fichiers statiques du dépôt. Les images téléversées dans l'administration doivent aller dans un bucket privé S3-compatible : le disque d'un service gratuit Render ne les conserverait pas après un redémarrage ou un redéploiement.

Le Blueprint demande le nom du bucket, sa région et ses deux clés secrètes, mais ne demande pas l'endpoint S3. Pour Cloudflare R2, il faudra donc ajouter `AWS_S3_ENDPOINT_URL` manuellement dans l'environnement Render après la création du service.

## 2. Préparer les comptes et les données

1. Connectez-vous au **nouveau compte Render** avec la nouvelle adresse Gmail et vérifiez l'adresse e-mail.
2. Dans Render, vérifiez le workspace sélectionné en haut du tableau de bord. Pour créer sa propre base gratuite, utilisez un workspace qui n'a pas déjà une base PostgreSQL gratuite active. Si Render refuse la création de la base, ne touchez pas à `lubrix-biphar-db` ni aux autres ressources d'un ancien compte : passez au workspace vide du nouveau compte.
3. Le code doit être accessible dans GitHub. Le dépôt Dunia existant est `divinntwali119/Dunia`, et la branche de déploiement est `main`. Le nouveau compte Render devra autoriser l'application GitHub Render à accéder à ce dépôt. Il n'est pas nécessaire de créer un deuxième dépôt si le premier est toujours celui que vous souhaitez déployer.
4. Décidez si vous repartez avec une base vide. Une base créée par ce guide contient les tables après les migrations, mais **ne copie pas** les comptes, formations, actualités, abonnements ni paiements de SQLite local. Si vous voulez conserver des données, faites d'abord une exportation et planifiez une migration distincte. Ne supprimez pas votre base locale.
5. Ne mettez jamais le fichier local `.env`, `db.sqlite3`, les mots de passe, les clés VAPID privées ou les identifiants R2 dans GitHub. Le fichier `.env` de votre ordinateur et les variables Render sont deux configurations différentes.

## 3. Créer le stockage durable des images (Cloudflare R2)

Cette étape doit être terminée **avant** d'appliquer le Blueprint, car Render demande les valeurs de stockage pendant la création initiale.

1. Connectez-vous à [Cloudflare](https://dash.cloudflare.com/) et ouvrez **R2 Object Storage**.
2. Créez un bucket nommé par exemple `  `. Le nom ne doit contenir que des lettres minuscules, chiffres et tirets. Laissez le bucket **privé** ; ne configurez pas d'accès public.
3. Dans **Manage R2 API Tokens**, créez un jeton **Object Read & Write** limité uniquement au bucket `dunia-media`. Ne choisissez pas un jeton administrateur portant sur tout le compte.
4. Copiez tout de suite l'**Access Key ID** et le **Secret Access Key** dans un gestionnaire de mots de passe. Cloudflare n'affiche pas de nouveau le secret après cette étape. Ne les envoyez pas dans le chat, ne les collez pas dans le dépôt et ne les mettez pas dans une capture d'écran.
5. Notez l'identifiant de compte Cloudflare et composez l'endpoint R2 : `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`. La région S3 de R2 est `auto`.

Le niveau gratuit publié de R2 comprend actuellement 10 Go-mois de stockage Standard, 1 million d'opérations Class A et 10 millions d'opérations Class B par mois ; le transfert sortant est gratuit. Les dépassements et autres conditions peuvent évoluer : vérifiez les [tarifs R2](https://developers.cloudflare.com/r2/pricing/). La création et l'usage d'un compte R2 peuvent nécessiter des étapes de facturation Cloudflare selon les règles du compte.

## 4. Vérifier et envoyer le dépôt GitHub

Dans un terminal ouvert à la racine du projet, vérifiez que vous êtes sur `main` et que le dépôt ne contient pas de secrets :

```bash
git status --short --branch
git diff --check
git ls-files .env db.sqlite3
```

La dernière commande ne doit rien afficher. Si elle affiche `.env` ou `db.sqlite3`, **ne poussez pas** : retirez ces fichiers de l'index Git sans effacer vos fichiers locaux, puis vérifiez de nouveau. Ne faites jamais `git add .env`.

Si vous avez modifié du code depuis le dernier envoi, vérifiez-le avec l'environnement virtuel du projet :

```bash
source .venv/bin/activate
python -m pip check
python manage.py check
python manage.py test
python manage.py collectstatic --noinput
git diff
```

Examinez les erreurs de tests et les changements de `git diff` avant de poursuivre. Si vous avez réellement modifié le projet, ajoutez **uniquement les chemins concernés**, vérifiez l'index avec `git diff --cached`, puis créez et poussez le commit sur `main`. Ne faites pas d'ajout global si des fichiers locaux ou secrets apparaissent dans `git status`.

```bash
git diff --cached
git commit -m "Préparer le déploiement Dunia"
git push origin main
```

Le dépôt actuellement préparé est déjà poussé sur `main`, donc cette étape n'est nécessaire que si vous avez de nouveaux changements. Render peut également accéder au guide et au code existants sans que vous ne modifiiez quoi que ce soit.

## 5. Créer les ressources Render avec le Blueprint

1. Ouvrez le [tableau de bord Render](https://dashboard.render.com/) et vérifiez une dernière fois que le nouveau compte et le bon workspace sont sélectionnés.
2. Cliquez sur **New + → Blueprint** ou **Blueprints → New Blueprint Instance**.
3. Autorisez Render à accéder au dépôt GitHub Dunia. Choisissez le dépôt `divinntwali119/Dunia`, la branche `main` et le fichier Blueprint `render.yaml` situé à la racine.
4. Avant de confirmer, vérifiez que Render annonce bien ces deux nouvelles ressources :
   - le service Web `dunia-web`, plan **Free**, région **Frankfurt** ;
   - la base `dunia-postgres`, plan **Free**, région **Frankfurt**.
5. Au formulaire des variables `sync: false`, saisissez les vraies valeurs R2 :
   - `AWS_STORAGE_BUCKET_NAME` : `dunia-media` (ou le nom exact choisi) ;
   - `AWS_S3_REGION_NAME` : `auto` ;
   - `AWS_ACCESS_KEY_ID` : Access Key ID R2 ;
   - `AWS_SECRET_ACCESS_KEY` : Secret Access Key R2.
6. Confirmez **Apply**. Le Blueprint génère la clé Django de production, configure `DEBUG=False` et relie automatiquement `DATABASE_URL` à la chaîne de connexion de sa propre base PostgreSQL.

**Sécurité :** si Render propose d'utiliser ou modifier une ressource déjà existante au lieu de créer `dunia-postgres`, arrêtez-vous et vérifiez le workspace. Ne choisissez pas une base d'une autre application, et ne supprimez pas celle de l'ancien compte. Le Blueprint Dunia doit créer ses ressources dans le nouveau workspace isolé.

### Si le Blueprint ne peut pas créer la base gratuite

Render autorise une seule base PostgreSQL Free active par workspace. Vérifiez d'abord le workspace du nouveau compte. Si une autre base Free y est déjà active, choisissez un workspace neuf (sans base existante) ou un plan PostgreSQL payant. Ne supprimez pas une base qui contient des données pour libérer le quota.

## 6. Ajouter l'endpoint R2 dans Render

Le [render.yaml](render.yaml) actuel ne contient pas `AWS_S3_ENDPOINT_URL`. Après la création du service :

1. Ouvrez la page du service `dunia-web`, puis **Environment**.
2. Ajoutez une variable :
   - **Key** : `AWS_S3_ENDPOINT_URL`
   - **Value** : `https://<ACCOUNT_ID>.r2.cloudflarestorage.com`, en remplaçant `<ACCOUNT_ID>` par l'identifiant réel de votre compte Cloudflare.
3. Enregistrez les changements et laissez Render redéployer le service.

La variable doit s'appeler exactement `AWS_S3_ENDPOINT_URL`. Si vous utilisez AWS S3 au lieu de R2, cet endpoint personnalisé n'est généralement pas nécessaire ; dans ce cas renseignez la vraie région AWS et adaptez les valeurs de stockage dans Render.

Dans l'onglet **Environment**, vérifiez également la présence des variables suivantes. N'affichez ni ne copiez leurs valeurs dans un message public :

| Variable | Valeur attendue |
| --- | --- |
| `SECRET_KEY` | Générée automatiquement par le Blueprint ; ne pas la remplacer par la clé locale. |
| `DEBUG` | `False`. |
| `DATABASE_URL` | Référence Render à la base `dunia-postgres` ; laisser le Blueprint la gérer. |
| `USE_S3` | `True`. |
| `AWS_STORAGE_BUCKET_NAME` | Nom exact du bucket R2. |
| `AWS_S3_REGION_NAME` | `auto` pour R2. |
| `AWS_S3_ENDPOINT_URL` | Endpoint R2 indiqué ci-dessus. |
| `AWS_ACCESS_KEY_ID` | Clé R2 limitée au bucket Dunia. |
| `AWS_SECRET_ACCESS_KEY` | Secret de cette clé R2. |

Render fournit aussi `RENDER_EXTERNAL_HOSTNAME`. Dunia l'utilise pour autoriser son domaine `.onrender.com`, construire l'adresse du site et accepter les formulaires HTTPS. Ne définissez `ALLOWED_HOSTS` et `CSRF_TRUSTED_ORIGINS` manuellement que si vous ajoutez un domaine personnalisé ou avez une configuration particulière.

Le `.env` local n'est pas envoyé à Render. Il n'est pas nécessaire d'y mettre l'URL de production ni les clés Cloudflare pour que l'hébergement fonctionne. Si vous décidez de les ajouter pour un usage local, gardez le fichier ignoré par Git et ne remplacez pas ses valeurs locales existantes.

## 7. Suivre le premier déploiement

Dans le service `dunia-web`, ouvrez **Events** ou **Logs** et attendez un état **Live**. Le build doit exécuter, dans cet ordre :

1. installation de `requirements.txt` avec Python 3.14 ;
2. `collectstatic` — les statiques du site sont préparées pour WhiteNoise ;
3. `migrate --noinput` — les tables sont créées dans PostgreSQL ;
4. démarrage de Gunicorn sur le port `$PORT` fourni par Render.

Le chemin de contrôle de santé est `/`. Si un déploiement échoue, lisez la **première erreur réelle** dans les logs avant de relancer. Vérifiez notamment l'accès GitHub, la création PostgreSQL, la présence des quatre valeurs R2 demandées et l'endpoint `AWS_S3_ENDPOINT_URL`. Ne mettez jamais `DEBUG=True` sur le site public pour masquer une erreur.

## 8. Créer le compte administrateur Django

La base Render étant neuve, le compte administrateur local n'y existe pas.

- Si votre plan Render donne accès au **Shell**, ouvrez le Shell du service et exécutez `python manage.py createsuperuser`, puis suivez les questions.
- Sur le plan Free, Render ne fournit pas de Shell. Pour le premier déploiement seulement :
  1. Dans **Environment**, ajoutez temporairement `DJANGO_SUPERUSER_USERNAME`, `DJANGO_SUPERUSER_EMAIL` et `DJANGO_SUPERUSER_PASSWORD`. Utilisez un mot de passe unique et fort.
  2. Dans les réglages du service, remplacez temporairement la Start Command par :

     ```bash
     python manage.py createsuperuser --noinput && python -m gunicorn Dunia.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -
     ```

  3. Déployez et attendez que le service passe à **Live**. Vérifiez la connexion sur `/admin/`.
  4. **Immédiatement après la création**, remettez la Start Command d'origine du Blueprint :

     ```bash
     python -m gunicorn Dunia.wsgi:application --bind 0.0.0.0:$PORT --access-logfile - --error-logfile -
     ```

  5. Supprimez les trois variables `DJANGO_SUPERUSER_*`, enregistrez et redéployez. Ne laissez pas la commande de création active : elle échouera si Render redémarre le service après la création du compte. Ne mettez jamais le mot de passe dans Git ou dans un fichier du dépôt.

## 9. Remettre les médias en place

Les images téléversées dans l'administration sont enregistrées dans le bucket privé. Les nouveaux téléversements seront conservés sous le préfixe `media/`. Les ressources de cours privées utilisent le stockage privé de Django ; ne rendez pas le bucket public.

Les fichiers déjà présents dans le dossier `media/` du dépôt ne sont pas transférés automatiquement dans R2. Si vous repartez avec une base vide, recréez le contenu depuis `/admin/` et téléversez de nouveau les images utiles. Si vous importez une base dont les champs d'image contiennent déjà des chemins, copiez aussi les objets correspondants avant de tester le site. Avec AWS CLI installé et le profil R2 configuré localement, la copie du dossier public du projet peut se faire ainsi :

```bash
aws s3 sync media/ s3://dunia-media/media/ \
  --endpoint-url "https://<ACCOUNT_ID>.r2.cloudflarestorage.com" \
  --region auto
```

Remplacez le bucket et l'identifiant de compte. Configurez les clés localement dans un profil AWS CLI sécurisé ; ne les ajoutez pas à cette commande, à un script du dépôt ou à l'historique Git. Cette commande copie les objets sous `media/` en gardant leur arborescence, mais ne migre ni les enregistrements Django ni les fichiers privés non présents dans ce dossier.

## 10. Vérifier le site en HTTPS

Render attribue au service un domaine du type `https://dunia-web.onrender.com` et active automatiquement TLS. Copiez le domaine exact depuis le tableau de bord, puis vérifiez :

- la page d'accueil `/` ;
- `/formations/` ;
- `/news/` ;
- `/admin/` et la connexion du compte administrateur ;
- le chargement du logo, des styles et des scripts ;
- la création d'une actualité ou d'une formation avec une image ;
- l'accès aux contenus privés selon les contrôles de connexion habituels ;
- la conservation d'une entrée PostgreSQL et d'une image après un redéploiement.

Testez aussi la déconnexion puis la reconnexion, et l'envoi d'un formulaire afin de repérer une erreur CSRF. Une base neuve est vide : l'absence de formations et d'actualités avant leur ajout dans `/admin/` est normale.

### Domaine personnalisé (optionnel)

Dans les réglages du service, ajoutez votre domaine dans **Custom Domains**, puis créez chez votre fournisseur DNS les enregistrements indiqués par Render. Attendez la vérification DNS et le certificat TLS Render. Ajoutez ensuite le nom de domaine à `ALLOWED_HOSTS` et son origine complète HTTPS à `CSRF_TRUSTED_ORIGINS` dans **Environment**. Après sauvegarde, redéployez et testez à nouveau les formulaires. Gardez le domaine `.onrender.com` jusqu'à ce que le domaine personnalisé fonctionne.

## 11. E-mails, notifications et paramètres facultatifs

Le site peut démarrer sans SMTP, mais les e-mails de bienvenue, newsletter et réinitialisation de mot de passe nécessitent un fournisseur e-mail configuré. Ajoutez uniquement les paramètres SMTP du fournisseur dans **Environment** (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `EMAIL_USE_TLS` ou `EMAIL_USE_SSL`). Les services Web Render gratuits bloquent les ports sortants 25, 465 et 587 : vérifiez la documentation Render et utilisez un fournisseur et un port compatibles. Ne testez pas avec des identifiants personnels en clair.

Les notifications Web Push sont facultatives. Pour les activer, ajoutez à l'environnement Render les clés VAPID publique et privée et `WEBPUSH_ENABLED=True`. Gardez la clé privée secrète ; ne la mettez pas dans le dépôt et ne partagez jamais les valeurs dans une conversation. Si les notifications ne sont pas configurées, laissez-les désactivées.

## 12. Sauvegardes, coûts et entretien

1. Render PostgreSQL Free n'inclut pas de sauvegardes et expire au bout de 30 jours. Exportez régulièrement les données et testez la restauration, ou passez à un plan avec sauvegardes avant de dépendre du site.
2. Pour faire un export PostgreSQL depuis un ordinateur disposant de `pg_dump`, récupérez l'**External Database URL** depuis le menu **Connect** de la base Render et utilisez-la dans un terminal privé. Ne l'enregistrez pas dans Git, un ticket public ou une capture.
3. Conservez aussi une copie des médias R2 ; un bucket objet n'est pas, à lui seul, une sauvegarde versionnée.
4. Surveillez l'utilisation incluse du workspace, les minutes de build, le trafic sortant, le stockage et les opérations R2. Configurez des limites de dépenses/alertes quand elles sont disponibles.
5. Après chaque changement de code, poussez `main` vers GitHub et consultez le déploiement automatique et ses logs. Les changements de variables se font dans l'interface Render, pas dans le dépôt.

## 13. Pannes fréquentes

| Symptôme | Vérification |
| --- | --- |
| La base gratuite ne peut pas être créée | Workspace sélectionné : Render n'autorise qu'une base PostgreSQL Free active par workspace. Ne supprimez pas une base inconnue ; choisissez un workspace neuf ou un plan payant. |
| Le build échoue avant Gunicorn | Lire la première erreur. Vérifier la version Python, `requirements.txt`, l'accès GitHub et le résultat de `collectstatic`. |
| `DATABASE_URL is required` | Le Blueprint doit relier `DATABASE_URL` à `dunia-postgres`. Vérifier que la base et le service sont dans le même Blueprint/workspace et que la variable est présente. |
| `Set AWS_STORAGE_BUCKET_NAME...` ou configuration média manquante | Vérifier `USE_S3=True`, le nom du bucket, les deux clés et la région dans **Environment**. |
| Image impossible à charger ou téléverser | Vérifier `AWS_S3_ENDPOINT_URL`, `AWS_S3_REGION_NAME=auto`, l'orthographe du bucket et le jeton Object Read & Write limité au bon bucket. |
| `DisallowedHost` ou HTTP 400 | Vérifier le domaine Render automatique ou ajouter le domaine personnalisé sans protocole dans `ALLOWED_HOSTS`. |
| Erreur CSRF HTTP 403 | Utiliser HTTPS et vérifier que le domaine personnalisé exact, avec `https://`, figure dans `CSRF_TRUSTED_ORIGINS`. |
| `/admin/` ne permet pas de se connecter | Le superutilisateur doit être créé dans la base Render, séparément de SQLite local. Suivre l'étape 8. |
| Le site met du temps à s'ouvrir | Un service Free endormi redémarre à la première requête. Une attente pouvant approcher une minute est normale. |
| Les données ou médias disparaissent | Ne pas stocker des uploads sur le disque Render. Confirmer que PostgreSQL est utilisé et que `default` pointe vers le bucket R2. Le disque local du service est éphémère. |

## Liens officiels

- [Render Free](https://render.com/docs/free)
- [Référence des Blueprints et variables](https://render.com/docs/blueprint-spec)
- [Créer et connecter PostgreSQL Render](https://render.com/docs/postgresql-creating-connecting)
- [Variables d'environnement Render](https://render.com/docs/configure-environment-variables)
- [Dépanner un déploiement Render](https://render.com/docs/troubleshooting-deploys)
- [Créer des buckets Cloudflare R2](https://developers.cloudflare.com/r2/buckets/create-buckets/)
- [Clés S3 et permissions R2](https://developers.cloudflare.com/r2/api/s3/tokens/)
- [Tarifs Cloudflare R2](https://developers.cloudflare.com/r2/pricing/)
