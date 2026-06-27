# 03 — Ajouter un projet (checklist)

Procédure mécanique pour mettre en ligne un nouveau projet. Une fois Traefik en place
([doc 02](02-installation-traefik.md)), chaque projet suit exactement ces étapes.

On suppose un projet nommé `projet1`, accessible sur `projet1.mondomaine.com`.

---

## Étape 1 — Créer le repo GitHub depuis le template

Pars du modèle [`templates/projet-react-postgres/`](../templates/projet-react-postgres/). Il
contient :

```
docker-compose.yml          # app + postgres + labels Traefik
Dockerfile                  # build React → servi en statique par nginx
.env.example                # variables à renseigner (copier en .env)
.gitignore                  # exclut .env
.github/workflows/deploy.yml  # déploiement SSH au push
```

Copie ces fichiers à la racine de ton nouveau repo (ton code React vient s'ajouter à côté).

## Étape 2 — Adapter les fichiers

Remplace les placeholders. Le nom de projet sert partout (service, routeur Traefik, base) :

| Placeholder | Remplacer par | Où |
|-------------|---------------|-----|
| `PROJET` | `projet1` | `docker-compose.yml` (noms de services, routeur, volume) |
| `projet1.mondomaine.com` | ton vrai sous-domaine | label `Host(...)` dans `docker-compose.yml` |
| `mondomaine.com` | ton domaine | `.env.example` |

> ⚠️ Le **nom du routeur Traefik doit être unique** sur tout le VPS. En utilisant le nom du
> projet (`projet1`) partout, tu évites les collisions entre projets.

## Étape 3 — Renseigner les secrets de l'application

Sur le **VPS**, dans le dossier du projet, copie `.env.example` en `.env` et remplis-le :

```bash
cd /opt/stacks/projet1
cp .env.example .env
nano .env            # mots de passe DB, etc.
```

Le `.env` **n'est jamais commité** (il est dans `.gitignore`). Génère un mot de passe Postgres
solide :

```bash
openssl rand -base64 24
```

## Étape 4 — Configurer le déploiement automatique

Une seule fois par projet, ajoute les **secrets GitHub Actions** au repo (le détail complet est
dans [doc 04](04-deploiement-github-actions.md)) :

| Secret | Valeur |
|--------|--------|
| `SSH_HOST` | IP du VPS |
| `SSH_USER` | utilisateur SSH de déploiement |
| `SSH_KEY` | clé privée de déploiement |
| `PROJECT_PATH` | `/opt/stacks/projet1` |

## Étape 5 — Premier déploiement (manuel, une fois)

Le tout premier clone se fait à la main sur le VPS (les déploiements suivants seront
automatiques) :

```bash
cd /opt/stacks
git clone git@github.com:TON_COMPTE/projet1.git projet1
cd projet1
cp .env.example .env && nano .env    # si pas déjà fait à l'étape 3
docker compose up -d --build
```

Vérifie :

```bash
docker compose ps                       # les conteneurs sont "Up"
docker compose logs -f app              # pas d'erreur
curl -I https://projet1.mondomaine.com  # 200 OK en HTTPS
```

## Étape 6 — Les déploiements suivants sont automatiques

À partir de maintenant, **un simple push sur `main`** (depuis Claude Code, mobile ou web)
déclenche le workflow qui fait `git pull && docker compose up -d --build` sur le VPS.

```
commit + push  ──▶  GitHub Action  ──▶  VPS redéployé  ──▶  en ligne
```

---

## Checklist récapitulative

- [ ] Repo GitHub créé à partir du template
- [ ] Placeholders `PROJET` / domaine remplacés
- [ ] DNS `projet1.mondomaine.com` résout vers le VPS (couvert par le wildcard)
- [ ] `.env` rempli sur le VPS (hors git)
- [ ] Secrets GitHub Actions configurés (`SSH_HOST`, `SSH_USER`, `SSH_KEY`, `PROJECT_PATH`)
- [ ] Premier `git clone` + `docker compose up -d --build` sur le VPS
- [ ] `https://projet1.mondomaine.com` répond en HTTPS
- [ ] Un push de test déclenche bien le redéploiement automatique

Détails du déploiement : [04 — Déploiement GitHub Actions](04-deploiement-github-actions.md).
Détails base de données : [05 — Base de données & sauvegardes](05-base-de-donnees-et-sauvegardes.md).
