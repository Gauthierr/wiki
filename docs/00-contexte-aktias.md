# 00 — Contexte réel (aktias.be)

Pense-bête partagé entre les sessions Claude Code (web et sur le VPS). Contient les valeurs
**réelles** de l'installation, pour remplacer les placeholders des templates (`mondomaine.com`,
`PROJET`, etc.).

> Ces informations sont déjà publiques (présentes dans le DNS de `aktias.be`). Aucun secret ici :
> les mots de passe et clés restent dans `.env` (sur le VPS) et dans les GitHub Actions Secrets.

## Infrastructure

| Élément | Valeur |
|---|---|
| Domaine | `aktias.be` |
| IP du VPS | `72.62.28.136` |
| Hébergeur | Hostinger (VPS) |
| Conteneur existant | Nextcloud, sur `nextcloud.aktias.be` |
| Serveurs de noms | `ns1.dns-parking.com` / `ns2.dns-parking.com` (DNS géré chez Hostinger) |

## DNS — état au 27/06/2026

### ✅ Déjà en place et utile pour l'architecture

- **`A * (wildcard) → 72.62.28.136`** : tout sous-domaine non explicite pointe sur le VPS.
  Vérifié en live : `projet-test-claude.aktias.be` résout bien vers `72.62.28.136`.
  → **Aucun ajout DNS nécessaire pour créer un nouveau projet** : `projet1.aktias.be`,
  `projet2.aktias.be`… arrivent automatiquement sur le VPS, où Traefik les route.
- **`A nextcloud → 72.62.28.136`** : Nextcloud est exposé sur `nextcloud.aktias.be`.

### ⛔ À NE PAS modifier (sinon casse email ou services tiers)

| Type | Nom | Contenu | Rôle |
|------|-----|---------|------|
| MX | `@` | `mx1.hostinger.com` (5), `mx2.hostinger.com` (10) | réception email |
| TXT | `@` | `v=spf1 include:_spf.mail.hostinger.com ~all` | SPF email |
| TXT | `_dmarc` | `v=DMARC1; p=none` | DMARC email |
| CNAME | `hostingermail-a/b/c._domainkey` | `…dkim.mail.hostinger.com` | DKIM email |
| CNAME | `autoconfig` | `autoconfig.mail.hostinger.com` | config client mail |
| CNAME | `autodiscover` | `autodiscover.mail.hostinger.com` | config client mail |
| CNAME | `www` | `aktias.odoo.com` | site Odoo (résout vers `51.83.88.58`) |
| CNAME | `grussens` | `grussens-test.lovable.app` | app de test Lovable |
| A | `ftp` | `145.14.153.200` | autre serveur Hostinger |

> Les CNAME explicites ci-dessus (`www`, `grussens`, etc.) ont la priorité sur le wildcard :
> ils continueront de pointer vers leurs cibles, le wildcard ne les affecte pas.

## Conséquences pour la mise en place

- **Certificats HTTPS** : on utilise le challenge **HTTP-01** (cf. `templates/traefik/traefik.yml`).
  Le wildcard DNS déjà présent suffit ; chaque `projetX.aktias.be` obtient son certificat
  Let's Encrypt automatiquement. Pas besoin de certificat wildcard ni de challenge DNS-01.
- **Sous-domaine Nextcloud réel** = `nextcloud.aktias.be` (et non `cloud.mondomaine.com` comme
  dans les exemples génériques des autres docs).
- **Remplacements de placeholders** dans les templates :
  - `mondomaine.com` → `aktias.be`
  - `projet1.mondomaine.com` → `projet1.aktias.be`
  - `traefik.mondomaine.com` → `traefik.aktias.be`

## Point à vérifier sur le VPS (première action de l'instance Claude locale)

- **Qui occupe les ports 80/443 ?** (`sudo ss -tlnp | grep -E ':80|:443'` et `docker ps`).
  Nextcloud les occupe probablement → il faudra le faire passer derrière Traefik
  (voir [`docs/07`](07-nextcloud-coexistence.md)), **après sauvegarde de Nextcloud**.
- Confirmer la version de Docker / Docker Compose et l'emplacement de la stack Nextcloud.
