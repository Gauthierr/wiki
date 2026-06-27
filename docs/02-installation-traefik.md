# 02 — Installation de Traefik (reverse proxy + HTTPS)

Cette étape se fait **une seule fois**. Ensuite, chaque projet se branche tout seul.

## 1. Configurer le DNS

Tu veux que `*.mondomaine.com` pointe vers l'IP publique de ton VPS.

Dans le panneau DNS de ton registrar (Hostinger ou autre), crée :

| Type | Nom | Valeur | Note |
|------|-----|--------|------|
| `A` | `@` | `IP_DU_VPS` | domaine racine (optionnel) |
| `A` | `*` | `IP_DU_VPS` | **wildcard** : tous les sous-domaines |

> Le wildcard `*` t'évite de créer un enregistrement par projet. `projet1.mondomaine.com`,
> `projet2.mondomaine.com`, `traefik.mondomaine.com`… résoudront tous vers le VPS.

Vérifie la propagation depuis ton poste :

```bash
dig +short projet-test.mondomaine.com   # doit renvoyer l'IP du VPS
```

> Pas encore de domaine ? Voir [doc 08 — Sans nom de domaine](08-annexes.md#sans-nom-de-domaine).

## 2. Ouvrir le firewall

Sur le VPS (voir [doc 06](06-securite-et-exploitation.md) pour le détail) :

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP (redirigé vers HTTPS)
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## 3. Créer le réseau Docker partagé

Ce réseau `web` relie Traefik aux applications. Il est créé une fois et réutilisé par tous les
projets.

```bash
docker network create web
```

## 4. Déployer la stack Traefik

Sur le VPS :

```bash
sudo mkdir -p /opt/stacks/traefik
cd /opt/stacks/traefik
```

Copie-y les deux fichiers du template
[`templates/traefik/`](../templates/traefik/) : `docker-compose.yml` et `traefik.yml`.

Prépare le fichier qui stockera les certificats (permissions strictes obligatoires) :

```bash
touch acme.json
chmod 600 acme.json
```

Édite `traefik.yml` et remplace l'email Let's Encrypt :

```yaml
certificatesResolvers:
  letsencrypt:
    acme:
      email: TON_EMAIL@exemple.com    # ← reçoit les alertes d'expiration de certificat
```

Démarre :

```bash
docker compose up -d
docker compose logs -f   # vérifie qu'il n'y a pas d'erreur ACME
```

## 5. Vérifier

- Le dashboard Traefik est protégé et accessible (selon le template) sur
  `https://traefik.mondomaine.com` — voir la note ci-dessous sur l'authentification.
- Au premier accès à un service, Traefik demande un certificat à Let's Encrypt ; il apparaît
  dans `acme.json` au bout de quelques secondes.

> ⚠️ **Limite de débit Let's Encrypt** : pendant tes tests, utilise le serveur *staging*
> (décommente la ligne `caServer` dans `traefik.yml`) pour éviter d'atteindre les quotas. Une
> fois que tout marche, repasse en production et **supprime le contenu d'`acme.json`** (`echo
> '{}' > acme.json`) pour forcer l'émission de vrais certificats.

## 6. Sécuriser le dashboard Traefik

Le template active le dashboard derrière une authentification *basic auth*. Génère un couple
identifiant/mot de passe :

```bash
# Génère la ligne user:hash (htpasswd fait partie de apache2-utils)
htpasswd -nb admin 'ton-mot-de-passe'
```

Place le résultat dans le label `traefik.http.middlewares.auth.basicauth.users` du
`docker-compose.yml` de Traefik (**double les `$` en `$$`** dans un fichier compose).

> Tu peux aussi simplement **ne pas exposer le dashboard** (commenter les labels du service
> Traefik) et le consulter via un tunnel SSH si besoin.

## Comment ça marche, concrètement

Quand un projet déclare ces labels dans son `docker-compose.yml` :

```yaml
labels:
  - "traefik.enable=true"
  - "traefik.http.routers.projet1.rule=Host(`projet1.mondomaine.com`)"
  - "traefik.http.routers.projet1.entrypoints=websecure"
  - "traefik.http.routers.projet1.tls.certresolver=letsencrypt"
  - "traefik.http.services.projet1.loadbalancer.server.port=80"
```

Traefik détecte le conteneur sur le réseau `web`, crée la route, obtient le certificat et sert le
projet en HTTPS — **sans que tu touches à la config de Traefik**. C'est tout l'intérêt.

Suite : [03 — Ajouter un projet](03-ajouter-un-projet.md).
