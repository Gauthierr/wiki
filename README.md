# Wiki — Architecture VPS multi-projets

Guide d'architecture pour héberger **plusieurs petits projets** (type React + PostgreSQL)
sur un **VPS Hostinger** unique, à côté d'un Nextcloud existant, avec un déploiement
**automatique depuis un commit Claude Code** (y compris sur smartphone).

## Idée en une phrase

Un **reverse proxy Traefik** unique route chaque projet vers son **sous-domaine HTTPS**.
Chaque projet vit dans son propre dossier avec un `docker-compose.yml` autonome
(app + PostgreSQL dédié). Un **push sur GitHub** déclenche une **GitHub Action** qui se
connecte en SSH au VPS et redéploie. Aucune intervention SSH manuelle au quotidien.

```
Claude Code (mobile/web)  ──commit/push──▶  GitHub  ──Action SSH──▶  VPS
                                                                       │
   Internet ──▶ :443 Traefik ──▶ projet1.mondomaine.com ──▶ conteneur projet1
                             ──▶ projet2.mondomaine.com ──▶ conteneur projet2
                             ──▶ cloud.mondomaine.com   ──▶ Nextcloud (existant)
```

## Sommaire

| Doc | Contenu |
|-----|---------|
| [00 — Contexte réel (aktias.be)](docs/00-contexte-aktias.md) | Valeurs réelles : IP du VPS, DNS, ce qu'il ne faut pas toucher |
| [01 — Vue d'ensemble](docs/01-vue-ensemble.md) | Principes, schéma, flux de déploiement, prérequis |
| [02 — Installation de Traefik](docs/02-installation-traefik.md) | Reverse proxy, DNS wildcard, HTTPS automatique |
| [03 — Ajouter un projet](docs/03-ajouter-un-projet.md) | Procédure pas-à-pas (checklist) pour un nouveau projet |
| [04 — Déploiement GitHub Actions](docs/04-deploiement-github-actions.md) | Clé SSH de déploiement, secrets, workflow |
| [05 — Base de données & sauvegardes](docs/05-base-de-donnees-et-sauvegardes.md) | Postgres dédié vs partagé, `pg_dump`, restore |
| [06 — Sécurité & exploitation](docs/06-securite-et-exploitation.md) | `ufw`, `.env`, limites ressources, logs, mises à jour |
| [07 — Coexistence avec Nextcloud](docs/07-nextcloud-coexistence.md) | Raccorder l'existant sans rien casser |
| [08 — Annexes](docs/08-annexes.md) | Alternatives : Nginx Proxy Manager, Portainer/Watchtower, sans domaine |
| [09 — Claude Code sur le VPS](docs/09-claude-code-sur-le-vps.md) | Lancer Claude Code directement sur le serveur pour tout configurer + MCP Hostinger |
| [10 — Workflow Git multi-postes](docs/10-workflow-git-multi-postes.md) | Committer depuis partout, serveur toujours à jour (GitOps, branches, rollback) |

## Modèles prêts à l'emploi

Le dossier [`templates/`](templates/) contient des fichiers à copier :

- [`templates/traefik/`](templates/traefik/) — la stack Traefik (reverse proxy + Let's Encrypt)
- [`templates/projet-react-postgres/`](templates/projet-react-postgres/) — un projet type
  (app React + PostgreSQL + labels Traefik + workflow de déploiement)

## Démarrage rapide

1. Pointer un DNS wildcard `*.mondomaine.com` vers l'IP du VPS → [doc 02](docs/02-installation-traefik.md).
2. Déployer Traefik une fois → [doc 02](docs/02-installation-traefik.md).
3. Pour chaque nouveau projet : copier le template, adapter, configurer les secrets GitHub,
   pousser → [doc 03](docs/03-ajouter-un-projet.md) + [doc 04](docs/04-deploiement-github-actions.md).
