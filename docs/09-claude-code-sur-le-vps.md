# 09 — Lancer Claude Code directement sur le VPS (option 1)

L'idée : au lieu de me donner un accès SSH (impossible et risqué depuis la session web — le
réseau sortant SSH y est bloqué), tu **m'exécutes directement sur le VPS**, là où le SSH et
Docker existent déjà. Je suis alors « à l'intérieur » et je peux tout faire : installer Traefik,
écrire les `docker-compose.yml`, déployer, raccorder Nextcloud.

## Prérequis

- VPS sous **Ubuntu 20.04+ / Debian 10+** (cas standard Hostinger), avec Docker déjà présent.
- **4 Go de RAM minimum** (recommandation officielle de Claude Code). Vérifie avec `free -h`.
- Un compte **Claude Pro, Max, Team, Enterprise ou Console** (le plan gratuit ne donne pas accès
  à Claude Code). Comme tu utilises déjà Claude Code sur mobile, c'est bon.

## Étape 1 — Se connecter au VPS

Depuis ton téléphone ou ton poste :

```bash
ssh ton_utilisateur@IP_DU_VPS
```

> **N'utilise pas `root`** pour faire tourner Claude Code. Si tu n'as qu'un accès root, crée un
> utilisateur dédié, membre du groupe `docker` :
>
> ```bash
> sudo adduser deployer
> sudo usermod -aG docker deployer
> su - deployer          # bascule sur ce compte (reconnexion nécessaire pour le groupe docker)
> ```

## Étape 2 — Garder la session vivante (tmux)

Une session SSH se coupe si ta connexion mobile lâche. `tmux` permet de **détacher/rattacher**
la session sans interrompre Claude Code :

```bash
sudo apt update && sudo apt install -y tmux
tmux new -s claude          # ouvre une session nommée "claude"
# (plus tard) : tmux attach -t claude   pour la retrouver
```

> Dans tmux : `Ctrl-b` puis `d` pour détacher (Claude continue en arrière-plan).

## Étape 3 — Installer Claude Code

L'**installeur natif** est le plus simple sur un serveur (pas besoin de Node, mises à jour
automatiques) :

```bash
curl -fsSL https://claude.ai/install.sh | bash
```

Recharge ton shell puis vérifie :

```bash
exec $SHELL          # ou : source ~/.bashrc
claude --version
claude doctor        # diagnostic d'installation
```

> **Alternative npm** (si tu préfères, nécessite Node.js 18+) :
> `npm install -g @anthropic-ai/claude-code` — **jamais** avec `sudo`.

## Étape 4 — S'authentifier (headless, sans navigateur sur le serveur)

Lance Claude Code dans le dossier de travail :

```bash
mkdir -p /opt/stacks && cd /opt/stacks
claude
```

Au premier lancement, Claude Code démarre la **connexion** :

1. Il affiche une **URL** dans le terminal.
2. Ouvre cette URL **sur ton téléphone ou ton ordinateur** (n'importe quel navigateur).
3. Connecte-toi à ton compte et autorise.
4. Le site t'affiche un **code** : copie-le et **colle-le dans le terminal** du VPS.

C'est le flux prévu pour les machines sans interface graphique : aucun navigateur n'est requis
*sur le serveur*.

> **Si l'URL renvoie vers `localhost` et que le collage de code n'apparaît pas**, ouvre ton SSH
> avec un **port forwarding** pour que la redirection locale fonctionne :
> ```bash
> ssh -L 54545:localhost:54545 ton_utilisateur@IP_DU_VPS
> ```
> puis relance `claude` (le port exact est indiqué par Claude Code au moment du login).
>
> **Autre alternative (compte Console)** : exporter une clé API au lieu du login interactif :
> ```bash
> export ANTHROPIC_API_KEY="sk-ant-..."     # à mettre dans ~/.bashrc pour persister
> ```

## Étape 5 — Me mettre au travail

Une fois connecté, tu es dans une session Claude Code **sur le VPS**. Tu peux alors me demander,
en langage naturel, de dérouler l'architecture de ce wiki. Par exemple :

> « Clone le repo `gauthierr/wiki`, lis le dossier `docs/`, puis installe Traefik selon
> `docs/02`, en faisant d'abord une sauvegarde de Nextcloud avant de toucher aux ports 80/443. »

Je peux à ce moment-là :

- créer le réseau Docker `web` et déployer la stack Traefik (`templates/traefik/`),
- récupérer/raccorder Nextcloud derrière Traefik (`docs/07`),
- créer un premier projet à partir du template et le mettre en ligne (`docs/03`),
- configurer les sauvegardes et le firewall (`docs/05`, `docs/06`).

## Étape 6 — Reprendre la main plus tard

- Rattacher la session : `tmux attach -t claude`.
- Relancer Claude Code : `cd /opt/stacks && claude` (l'authentification est mémorisée).
- Quitter Claude Code : `Ctrl-c` deux fois, ou la commande `/exit`.

## Où brancher le MCP Hostinger (DNS / VPS)

Le serveur MCP de Hostinger pilote l'**API** (DNS, gestion du VPS) — utile pour créer
l'enregistrement wildcard `*.tondomaine.com`. Tu peux l'ajouter **à cette même instance de
Claude Code sur le VPS** pour que je gère aussi le DNS. Ajout d'un serveur MCP :

```bash
# Exemple (adapte au paquet/commande exacts du MCP Hostinger et à ta clé API) :
claude mcp add hostinger -- npx -y <paquet-mcp-hostinger>
# La clé API Hostinger se fournit via une variable d'environnement, jamais en clair dans le chat.
```

Vérifie ensuite avec `claude mcp list`. La partie « interne au serveur » (Docker, Traefik) reste
gérée par moi en local sur le VPS ; le MCP Hostinger ne sert que pour le DNS et la plateforme.

## Récapitulatif express

```bash
ssh utilisateur@IP_DU_VPS
sudo apt install -y tmux && tmux new -s claude
curl -fsSL https://claude.ai/install.sh | bash && exec $SHELL
mkdir -p /opt/stacks && cd /opt/stacks
claude            # puis login via URL ouverte sur le téléphone + code collé
```
