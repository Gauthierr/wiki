# 04 — Déploiement automatique via GitHub Actions (SSH)

Objectif : **un push sur `main` redéploie le projet sur le VPS**, sans action manuelle. C'est ce
qui te permet de déployer depuis Claude Code sur ton smartphone.

## Le principe (push-based)

```
git push (main)
   └─▶ GitHub Actions
          └─▶ se connecte en SSH au VPS avec une clé de déploiement dédiée
                 └─▶ cd /opt/stacks/projet1
                        └─▶ git pull
                        └─▶ docker compose up -d --build
```

Pourquoi cette approche plutôt que construire des images dans le CI ?

- **Simplicité** : pas de registre d'images à gérer ; le VPS build directement.
- **Adapté aux petits projets** : un build React est rapide et léger.
- Si tu préfères pré-construire les images (CI → GHCR → `docker pull`), voir
  [doc 08 — Annexes](08-annexes.md#variante-images-pré-construites-ghcr).

## 1. Créer une clé SSH de déploiement (une fois)

Crée une **paire de clés dédiée au déploiement** (ne réutilise pas ta clé personnelle). Sur ton
poste ou le VPS :

```bash
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/deploy_key -N ""
```

Cela génère `deploy_key` (privée) et `deploy_key.pub` (publique).

Autorise la clé publique sur le VPS, pour l'utilisateur de déploiement :

```bash
# sur le VPS, en tant qu'utilisateur de déploiement
cat deploy_key.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

> **Bonne pratique** : crée un utilisateur Unix dédié au déploiement (ex. `deployer`) membre du
> groupe `docker`, plutôt que d'utiliser `root`. Voir [doc 06](06-securite-et-exploitation.md).

## 2. Donner au VPS un accès en lecture au repo GitHub

Le `git pull` sur le VPS a besoin de lire le repo. Deux options :

- **Repo public** : rien à faire.
- **Repo privé** (recommandé) : ajoute une **deploy key GitHub** en lecture seule.
  Génère une clé sur le VPS (`ssh-keygen -t ed25519 -f ~/.ssh/projet1_repo`), ajoute la partie
  publique dans **GitHub → repo → Settings → Deploy keys**, et configure `~/.ssh/config` sur le
  VPS pour utiliser cette clé avec `github.com`.

## 3. Enregistrer les secrets dans GitHub

Dans le repo : **Settings → Secrets and variables → Actions → New repository secret**.

| Secret | Exemple | Rôle |
|--------|---------|------|
| `SSH_HOST` | `203.0.113.10` | IP (ou hostname) du VPS |
| `SSH_USER` | `deployer` | utilisateur SSH de déploiement |
| `SSH_KEY` | *(contenu de `deploy_key`)* | clé **privée** de déploiement |
| `PROJECT_PATH` | `/opt/stacks/projet1` | dossier du projet sur le VPS |

> ⚠️ `SSH_KEY` = le **contenu intégral** du fichier privé (`-----BEGIN ... END-----` compris).
> Ces valeurs sont chiffrées par GitHub et ne sont jamais affichées dans les logs.

## 4. Le workflow

Il est fourni dans le template :
[`templates/projet-react-postgres/.github/workflows/deploy.yml`](../templates/projet-react-postgres/.github/workflows/deploy.yml).
Extrait commenté :

```yaml
name: Deploy
on:
  push:
    branches: [main]          # tout push sur main déclenche le déploiement

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - name: Déploiement SSH
        uses: appleboy/ssh-action@v1.2.0
        with:
          host: ${{ secrets.SSH_HOST }}
          username: ${{ secrets.SSH_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd ${{ secrets.PROJECT_PATH }}
            git pull --ff-only
            docker compose up -d --build
            docker image prune -f      # nettoie les images orphelines
```

## 5. Vérifier

1. Fais un petit commit (ex. modifie un texte) et pousse sur `main`.
2. Onglet **Actions** du repo : le job `Deploy` doit passer au vert.
3. Recharge `https://projet1.mondomaine.com` : la modification est en ligne.

## Le flux complet depuis ton téléphone

```
Claude Code (mobile)  →  commit + push sur main  →  GitHub Actions  →  SSH  →  VPS à jour
```

Tu n'ouvres jamais de terminal. Le SSH manuel reste là pour l'admin (logs, sauvegardes, debug).

## Dépannage rapide

| Symptôme | Piste |
|----------|-------|
| `Permission denied (publickey)` | `SSH_KEY` incomplète, ou `.pub` pas dans `authorized_keys` du VPS |
| `git pull` échoue (repo privé) | deploy key GitHub absente / `~/.ssh/config` du VPS mal réglé |
| `docker: permission denied` | l'utilisateur de déploiement n'est pas dans le groupe `docker` |
| Action verte mais site inchangé | build mis en cache : vérifie `docker compose logs app` |

Suite : [05 — Base de données & sauvegardes](05-base-de-donnees-et-sauvegardes.md).
