# 08 — Annexes (alternatives & options)

## Alternative au reverse proxy : Nginx Proxy Manager (NPM)

[Nginx Proxy Manager](https://nginxproxymanager.com/) offre une **interface web** pour gérer les
domaines et certificats — pratique si tu préfères cliquer (y compris depuis ton téléphone) plutôt
que d'écrire des labels.

**Compromis vs Traefik :**

| | Traefik (retenu) | Nginx Proxy Manager |
|---|---|---|
| Config | labels dans chaque compose (infra-as-code) | interface web (clics) |
| Nouveau projet | automatique (auto-découverte) | étape manuelle dans la GUI à chaque fois |
| Reproductible / versionnable | ✅ (tout est dans git) | ❌ (état dans une base interne) |
| Gérable par Claude Code | ✅ | partiellement |
| Prise en main visuelle | moins | ✅ très simple |

> Pour un parc géré par Claude Code, **Traefik** reste préférable (chaque projet porte sa propre
> config). NPM est un bon choix si tu veux tout piloter à la souris.

## Variante de déploiement : Portainer + Watchtower

### Portainer

[Portainer](https://www.portainer.io/) = interface web pour gérer conteneurs, stacks, logs et
volumes depuis un navigateur (donc depuis mobile). Complémentaire de l'approche GitHub Actions :
tu déploies via Actions, tu **observes/dépannes** via Portainer.

### Watchtower

[Watchtower](https://containrrr.dev/watchtower/) surveille un registre et **met à jour
automatiquement** les conteneurs quand une nouvelle image est publiée. Utile **si** tu pré-construis
tes images dans le CI (voir ci-dessous). Sinon, avec le build sur le serveur, le workflow SSH
suffit.

## Variante : images pré-construites (GHCR)

Au lieu de builder sur le VPS, tu peux construire l'image dans GitHub Actions et la pousser sur
**GitHub Container Registry (GHCR)**, puis faire un simple `docker pull` côté VPS.

```
push main → Action: docker build + push ghcr.io/compte/projet1:sha
          → SSH VPS: docker compose pull && up -d   (ou Watchtower auto)
```

**Avantages** : VPS déchargé du build, rollback facile (tag d'image), démarrage plus rapide.
**Inconvénients** : plus de pièces (registre, auth GHCR, tags). À adopter si les builds deviennent
lourds ou si le VPS est juste en ressources.

## Sans nom de domaine

Si tu n'as pas (encore) de domaine :

- **Acheter un domaine** (Hostinger en propose, ou Namecheap, OVH, Porkbun…). C'est ~10 €/an et
  débloque sous-domaines propres + HTTPS Let's Encrypt. **Recommandé** dès que possible.
- **Solution temporaire `nip.io` / `sslip.io`** : ces services résolvent
  `projet1.203-0-113-10.nip.io` vers l'IP encodée dans le nom. Tu obtiens des sous-domaines
  utilisables avec Traefik + Let's Encrypt sans acheter de domaine, le temps de tester.
- **Accès par port (dernier recours)** : publier chaque app sur un port distinct
  (`8081`, `8082`…) sans HTTPS propre. À éviter au-delà du tout premier test.

## Outils d'administration via le web

Pratiques pour piloter le VPS depuis un mobile, sans terminal :

- **[Portainer](https://www.portainer.io/)** — gestion des conteneurs/stacks/volumes.
- **[Dozzle](https://dozzle.dev/)** — visualisation des logs Docker en temps réel dans le
  navigateur.
- **[Uptime Kuma](https://github.com/louislam/uptime-kuma)** — supervision/uptime de tes
  services avec alertes (et belle interface mobile).

Chacun se déploie comme un projet de plus, derrière Traefik, sur son sous-domaine protégé.

## Récapitulatif des choix par défaut de ce wiki

| Sujet | Choix par défaut | Alternative principale |
|-------|------------------|------------------------|
| Reverse proxy | **Traefik** (labels) | Nginx Proxy Manager (GUI) |
| Exposition | **Sous-domaines wildcard + HTTPS** | nip.io / ports (temporaire) |
| Déploiement | **GitHub Actions → SSH** (build sur VPS) | GHCR + Watchtower / Portainer |
| Base de données | **Postgres dédié par projet** | Postgres partagé (1 base/projet) |
| Administration | **SSH + Actions** | Portainer / Dozzle / Uptime Kuma |
