# 07 — Coexistence avec Nextcloud

Ton Nextcloud existant tourne déjà. L'objectif est d'ajouter Traefik et les nouveaux projets
**sans rien casser**. Deux scénarios selon la façon dont Nextcloud est exposé aujourd'hui.

## Scénario 1 — Nextcloud occupe déjà les ports 80/443

C'est le cas le plus courant : ton conteneur Nextcloud (ou un nginx/apache devant lui) publie
directement `80:80` et `443:443`. **Traefik ne peut pas démarrer** tant que ces ports sont pris.

Tu as deux options :

### Option A — Faire passer Nextcloud derrière Traefik (recommandé, propre)

Tu unifies tout derrière Traefik. Nextcloud devient un service routé comme les autres.

1. Dans le `docker-compose.yml` de Nextcloud, **retire la publication des ports** `80`/`443`
   (supprime les lignes `ports:` correspondantes). Nextcloud n'écoute plus que sur le réseau
   Docker interne.
2. **Raccorde Nextcloud au réseau `web`** :

   ```yaml
   services:
     nextcloud:
       networks:
         - default      # réseau interne existant (DB, redis…)
         - web          # pour être joignable par Traefik
       labels:
         - "traefik.enable=true"
         - "traefik.http.routers.nextcloud.rule=Host(`cloud.mondomaine.com`)"
         - "traefik.http.routers.nextcloud.entrypoints=websecure"
         - "traefik.http.routers.nextcloud.tls.certresolver=letsencrypt"
         - "traefik.http.services.nextcloud.loadbalancer.server.port=80"
   networks:
     web:
       external: true
   ```

3. Ajoute le domaine de confiance dans la config Nextcloud (`config.php` →
   `trusted_domains` et `overwrite.cli.url` / `overwriteprotocol = https`) pour qu'il accepte
   les requêtes venant de Traefik en HTTPS.
4. `docker compose up -d` côté Nextcloud, puis démarre Traefik.

> ✅ Avantage : un seul point d'entrée, HTTPS géré uniformément par Traefik, certificats
> centralisés. C'est l'architecture cible.

### Option B — Laisser Nextcloud tel quel, Traefik sur d'autres ports

Si tu ne veux **pas toucher** à Nextcloud tout de suite, fais écouter Traefik sur des ports
alternatifs (ex. `8080`/`8443`) — mais c'est bancal (URLs avec port, HTTPS Let's Encrypt plus
compliqué). **À éviter** sauf en transition courte. Préfère l'option A.

## Scénario 2 — Nextcloud est derrière un proxy que tu peux remplacer

Si un nginx/Caddy/Apache fait déjà office de proxy devant Nextcloud, tu peux **le remplacer par
Traefik** et y rattacher Nextcloud (comme en option A) + tes nouveaux projets. Un seul reverse
proxy pour tout le VPS.

## Précautions avant de toucher à Nextcloud

- **Sauvegarde d'abord** : base de données Nextcloud + dossier `data` + `config.php`.
- **Note la config actuelle** : `docker compose config` et `docker inspect` pour garder une trace
  des ports, volumes et réseaux avant modification.
- **Fenêtre calme** : fais la bascule quand personne n'utilise activement Nextcloud (la coupure
  est de quelques secondes le temps du redémarrage).
- **Vérifie après** : connexion web, synchro client, et que le certificat HTTPS est bien émis par
  Let's Encrypt via Traefik.

## Résultat

```
:443 Traefik
   ├─ cloud.mondomaine.com    → Nextcloud
   ├─ projet1.mondomaine.com  → projet 1
   └─ projet2.mondomaine.com  → projet 2
```

Un seul reverse proxy, un seul mécanisme HTTPS, chaque service isolé dans sa stack.

Suite : [08 — Annexes](08-annexes.md).
