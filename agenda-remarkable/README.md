# agenda-remarkable

Automatisation qui, **chaque jour**, récupère tes agendas **Outlook**, **Gmail** et
**Infomaniak**, génère un **PDF lisible** des 7 prochains jours, et le publie sur ton
**cloud reMarkable** pour le lire sur la tablette.

```
URLs iCal (.ics)  ──►  fusion + tri  ──►  PDF (A5, lisible e-ink)  ──►  cloud reMarkable
   Outlook / Gmail / Infomaniak                                          (via rmapi)
```

L'exécution quotidienne est assurée par **GitHub Actions** (cron) : aucune machine à
laisser allumée. Les identifiants restent dans **GitHub Secrets**.

---

## 1. Comment ça marche

- **Lecture des agendas** : chaque service publie ton calendrier sous forme d'une URL
  iCal (`.ics`) secrète. Le script lit ces URLs (lecture seule, aucune app OAuth à
  enregistrer), développe les événements récurrents, et fusionne le tout.
- **Génération du PDF** : mise en page A5 portrait, optimisée pour l'écran e-ink, avec
  une couleur par source d'agenda et un regroupement par jour (en français).
- **Publication reMarkable** : via l'outil [`rmapi`](https://github.com/ddvk/rmapi).
  Le PDF est déposé dans le dossier `/Agenda` sous le nom `Agenda AAAA-MM-JJ.pdf`.
  Les anciens documents au-delà de `keep_last` sont supprimés automatiquement.

---

## 2. Récupérer les URLs iCal secrètes

> ⚠️ Ces URLs donnent accès en lecture à ton agenda : garde-les secrètes, mets-les
> uniquement dans GitHub Secrets.

- **Outlook / Microsoft 365** : Outlook Web → *Paramètres* → *Calendrier* →
  *Calendriers partagés* → *Publier un calendrier* → publie et copie le lien **ICS**.
- **Google Agenda (Gmail)** : agenda.google.com → *Paramètres* du calendrier →
  *Intégrer l'agenda* → **Adresse secrète au format iCal**.
- **Infomaniak** : Calendar Infomaniak → paramètres du calendrier → lien de
  partage/abonnement **iCal (.ics)** (ou l'URL CalDAV publique `.ics`).

Tu peux n'en configurer qu'un seul pour commencer : les sources non renseignées sont
simplement ignorées.

---

## 3. Configurer reMarkable (`rmapi`)

`rmapi` a besoin d'un jeton d'appairage généré **une seule fois** :

1. Installe rmapi en local (`go install github.com/ddvk/rmapi@latest`, ou un binaire
   depuis les *releases*).
2. Lance `rmapi`. Il demande un **code à usage unique** : récupère-le sur
   <https://my.remarkable.com/device/desktop/connect>.
3. Une fois connecté, le fichier `~/.config/rmapi/rmapi.conf` contient tes jetons.
4. Copie **tout le contenu** de ce fichier dans le secret GitHub `RMAPI_CONF` (étape 5).

---

## 4. Créer le dépôt et pousser le code

Depuis le dossier `agenda-remarkable/` :

```bash
# Crée un dépôt privé sous ton compte et pousse le code (nécessite la CLI `gh`)
gh repo create agenda-remarkable --private --source=. --remote=origin --push
```

> Sans `gh` : crée un dépôt vide `agenda-remarkable` sur github.com, puis
> `git init && git add . && git commit -m "Init" && git branch -M main`
> `&& git remote add origin git@github.com:<toi>/agenda-remarkable.git && git push -u origin main`

---

## 5. Configurer les secrets GitHub

Dépôt → *Settings* → *Secrets and variables* → *Actions* → *New repository secret* :

| Secret            | Contenu                                                        |
| ----------------- | ------------------------------------------------------------- |
| `ICS_OUTLOOK`     | URL iCal Outlook (optionnel)                                   |
| `ICS_GMAIL`       | URL iCal Google Agenda (optionnel)                            |
| `ICS_INFOMANIAK`  | URL iCal Infomaniak (optionnel)                              |
| `RMAPI_CONF`      | Contenu complet de `~/.config/rmapi/rmapi.conf`              |

L'automatisation tourne ensuite tous les jours. Tu peux la déclencher à la main :
onglet **Actions** → *Agenda quotidien -> reMarkable* → **Run workflow**.

---

## 6. Test en local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

cp config.example.yaml config.yaml          # optionnel (les défauts suffisent)
export ICS_GMAIL="https://calendar.google.com/.../basic.ics"

# Génère seulement le PDF, sans publier sur reMarkable :
python -m src.main --no-upload
open out/Agenda*.pdf    # macOS (ou xdg-open sous Linux)
```

Pour tester la publication reMarkable en local (rmapi configuré) : retire `--no-upload`.

---

## 7. Personnalisation

`config.yaml` (voir `config.example.yaml`) :

- `days_ahead` : nombre de jours affichés (défaut 7).
- `timezone` : fuseau d'affichage (défaut `Europe/Paris`).
- `remarkable_folder` : dossier cible sur la tablette (défaut `/Agenda`).
- `keep_last` : nombre de PDF conservés sur reMarkable (`0` = ne jamais supprimer).
- `calendars` : liste des sources (nom + variable d'environnement de l'URL).

L'heure d'exécution se règle dans `.github/workflows/daily.yml` (champ `cron`, en UTC).

---

## Structure

```
agenda-remarkable/
├── src/
│   ├── config.py       # chargement config + secrets
│   ├── calendars.py    # récupération/fusion des .ics
│   ├── render.py       # génération du PDF
│   ├── remarkable.py   # publication via rmapi
│   └── main.py         # orchestration
├── .github/workflows/daily.yml
├── config.example.yaml
└── requirements.txt
```
