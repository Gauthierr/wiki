# 01 — Vue d'ensemble

## Le problème

Tu as **un seul VPS Hostinger** qui héberge déjà **Nextcloud** dans Docker. Tu veux y ajouter
**plusieurs petits projets** (React + PostgreSQL, ou similaire), dont le code est sur **GitHub**,
et pouvoir **déclencher un déploiement en committant depuis Claude Code** (même depuis ton
téléphone), sans devoir te connecter en SSH à chaque fois.

Les contraintes qui en découlent :

- **Un seul port 80/443** pour plusieurs applications → il faut un *reverse proxy* qui aiguille
  selon le nom de domaine.
- **HTTPS** sur chacune sans gérer les certificats à la main → Let's Encrypt automatique.
- **Isolation** : un projet qui plante ne doit pas casser les autres ni Nextcloud.
- **Reproductibilité** : ajouter un projet doit être une recette mécanique (copier un template),
  pas un bricolage unique — c'est ce qui rend la gestion par Claude Code fiable.

## Les principes de l'architecture

### 1. Un reverse proxy unique : Traefik

[Traefik](https://traefik.io/) est le seul conteneur qui écoute sur les ports **80** et **443**.
Il lit les **labels Docker** de chaque conteneur pour savoir quel domaine route vers quoi, et
obtient/renouvelle automatiquement les certificats HTTPS via **Let's Encrypt**.

Avantage clé : **chaque projet décrit lui-même son routage** dans son `docker-compose.yml`. Pas
de configuration centrale à éditer à chaque ajout → idéal pour de l'« infra-as-code » générée
par Claude Code.

### 2. Un projet = un dossier = une stack Docker Compose

Chaque projet est autonome :

```
/opt/stacks/projet1/
├── docker-compose.yml      # app + postgres + labels Traefik
├── .env                    # secrets (PAS dans git)
└── (code du repo GitHub)
```

Il contient son **app** et sa **base PostgreSQL dédiée**. La base n'est **jamais exposée** sur
Internet ; elle n'est joignable que par l'app, sur un réseau Docker interne au projet.

### 3. Un réseau Docker partagé `web`

Un réseau externe `web` relie Traefik à la partie « front » de chaque projet. La base de données
reste sur le réseau **par défaut** (interne) de la stack du projet, invisible depuis l'extérieur.

```
réseau "web" (partagé) ── Traefik ── app projet1 ── (réseau interne) ── postgres projet1
                                   ── app projet2 ── (réseau interne) ── postgres projet2
```

### 4. Déploiement déclenché par un push GitHub

```
1. Tu codes avec Claude Code (mobile/web) et tu pushes sur la branche main du repo du projet.
2. GitHub Actions démarre un workflow.
3. Le workflow se connecte en SSH au VPS (clé de déploiement dédiée).
4. Sur le VPS : git pull && docker compose up -d --build dans le dossier du projet.
5. Traefik route automatiquement le nouveau conteneur.
```

Tu n'as **jamais besoin d'ouvrir un terminal SSH** pour un déploiement courant. Le SSH manuel
reste disponible pour l'administration (logs, debug, sauvegardes).

## Schéma global

```
                          Internet
                             │
                     ┌───────┴────────┐
                     │  VPS Hostinger  │
                     │   ufw: 22/80/443 │
                     └───────┬────────┘
                             │ :80 / :443
                       ┌─────┴──────┐
                       │  Traefik    │  (Let's Encrypt, dashboard)
                       └─────┬──────┘
            ┌────────────────┼─────────────────┐
   projet1.mondomaine.com   projet2.mondo…   cloud.mondomaine.com
            │                │                 │
        ┌───┴───┐        ┌───┴───┐         ┌───┴────┐
        │ app 1 │        │ app 2 │         │Nextcloud│ (existant)
        └───┬───┘        └───┬───┘         └────────┘
        ┌───┴────┐       ┌───┴────┐
        │postgres│       │postgres│   (non exposées, réseaux internes)
        └────────┘       └────────┘
```

## Prérequis

- **VPS** avec Docker + Docker Compose v2 installés (déjà le cas puisque Nextcloud tourne).
  Vérifie : `docker --version` et `docker compose version`.
- **Accès SSH** au VPS (tu l'as).
- **Un nom de domaine** dont tu contrôles le DNS (sous-domaines + wildcard). Si tu n'en as pas
  encore, voir [doc 08 — Annexes](08-annexes.md#sans-nom-de-domaine).
- **Comptes GitHub** pour les repos des projets.

## Ordre de mise en place (une seule fois)

1. [Configurer le DNS et déployer Traefik](02-installation-traefik.md).
2. [Préparer la clé SSH de déploiement et les secrets GitHub](04-deploiement-github-actions.md).

Puis, **pour chaque projet** : [suivre la checklist du doc 03](03-ajouter-un-projet.md).

## Dimensionnement

Un petit projet React (statique) + PostgreSQL consomme typiquement **~150–300 Mo de RAM**
(surtout Postgres). Sur un VPS Hostinger d'entrée de gamme (souvent 4–8 Go), tu peux héberger
**plusieurs** projets sans souci, à condition de :

- mettre des **limites mémoire** par conteneur (voir [doc 06](06-securite-et-exploitation.md)),
- envisager un **Postgres partagé** si tu multiplies les petits projets
  (voir [doc 05](05-base-de-donnees-et-sauvegardes.md)).
