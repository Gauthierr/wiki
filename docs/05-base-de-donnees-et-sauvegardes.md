# 05 — Base de données & sauvegardes

## Deux modèles possibles

### Modèle A — Un PostgreSQL dédié par projet (par défaut)

Chaque projet embarque son propre conteneur Postgres dans son `docker-compose.yml`.

```
projet1/  →  app + postgres (volume projet1_db)
projet2/  →  app + postgres (volume projet2_db)
```

**Avantages** : isolation totale, versions de Postgres indépendantes, projet portable et
auto-suffisant, suppression propre (on supprime le dossier + le volume).
**Inconvénient** : chaque instance Postgres consomme ~80–150 Mo de RAM au repos.

C'est le bon choix tant que tu as **quelques projets** et de la RAM disponible. C'est ce que fait
le template.

### Modèle B — Un PostgreSQL partagé, une base par projet

Une seule instance Postgres pour tout le VPS ; chaque projet a sa **base** et son **utilisateur**
dédiés.

```
postgres partagé  →  base projet1 (user projet1)
                  →  base projet2 (user projet2)
```

**Avantages** : une seule instance à administrer/sauvegarder, économie de RAM nette si tu
multiplies les petits projets.
**Inconvénients** : couplage (une montée de version impacte tout le monde), isolation plus faible,
il faut créer base + user à chaque projet.

Bascule vers ce modèle quand le nombre de projets fait grimper la RAM. Mise en place :

```bash
# Stack postgres partagée dans /opt/stacks/postgres/ (sur le réseau "web" ou un réseau "db")
docker compose up -d

# Pour chaque nouveau projet, créer base + utilisateur :
docker compose exec postgres psql -U postgres -c "CREATE USER projet1 WITH PASSWORD 'xxx';"
docker compose exec postgres psql -U postgres -c "CREATE DATABASE projet1 OWNER projet1;"
```

Dans ce cas, l'app du projet pointe vers l'hôte `postgres` (nom du service partagé) au lieu d'un
Postgres local, et le service `postgres` disparaît du `docker-compose.yml` du projet.

> **Recommandation** : commence en **modèle A** (simple, isolé). Passe en **modèle B** seulement
> si la RAM devient un sujet.

## Sécurité de la base

- La base **n'est jamais exposée** sur Internet : pas de `ports:` publiant `5432` dans le compose.
  Seule l'app y accède, via le réseau Docker interne.
- Mot de passe fort généré aléatoirement (`openssl rand -base64 24`), stocké dans `.env` (hors git).
- Volume Docker **nommé** pour la persistance (les données survivent à `docker compose down`).

## Sauvegardes (`pg_dump` par cron)

Un petit script + une tâche cron suffisent. Exemple de script `/opt/stacks/backup-db.sh` :

```bash
#!/usr/bin/env bash
set -euo pipefail
BACKUP_DIR=/opt/backups
RETENTION_DAYS=14
mkdir -p "$BACKUP_DIR"

# Sauvegarde chaque projet ayant un service "postgres"
for dir in /opt/stacks/*/; do
  name=$(basename "$dir")
  if docker compose -f "$dir/docker-compose.yml" ps --services 2>/dev/null | grep -qx postgres; then
    ts=$(date +%Y%m%d-%H%M%S)
    docker compose -f "$dir/docker-compose.yml" exec -T postgres \
      pg_dumpall -U postgres | gzip > "$BACKUP_DIR/${name}-${ts}.sql.gz"
  fi
done

# Purge des sauvegardes plus vieilles que RETENTION_DAYS
find "$BACKUP_DIR" -name '*.sql.gz' -mtime +$RETENTION_DAYS -delete
```

Rends-le exécutable et programme-le :

```bash
chmod +x /opt/stacks/backup-db.sh
sudo crontab -e
# Sauvegarde quotidienne à 3h du matin :
0 3 * * * /opt/stacks/backup-db.sh >> /var/log/db-backup.log 2>&1
```

> 💡 **Sauvegarde hors-site** : tu as déjà Nextcloud ! Tu peux copier `/opt/backups` vers un
> dossier Nextcloud (ou utiliser le client `nextcloudcmd`) pour disposer d'une copie répliquée et
> versionnée hors du VPS.

## Restauration

```bash
cd /opt/stacks/projet1
gunzip < /opt/backups/projet1-20260627-030000.sql.gz | \
  docker compose exec -T postgres psql -U postgres
```

## Migrations de schéma

Les migrations applicatives (Prisma, Drizzle, node-pg-migrate, Flyway…) doivent tourner **au
démarrage de l'app** ou via une commande déclenchée par le déploiement. Ajoute l'étape dans le
`Dockerfile`/entrypoint ou dans le `script:` du workflow de déploiement, selon ton outil.

Suite : [06 — Sécurité & exploitation](06-securite-et-exploitation.md).
