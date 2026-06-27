# 10 — Workflow Git : committer depuis partout, serveur toujours à jour

> « Comment font les pros pour committer depuis plusieurs endroits (session web, VS Code, mobile)
> et avoir un serveur qui tourne toujours la dernière version ? »

La réponse tient en une phrase : **GitHub est la seule source de vérité, et le serveur en est un
simple reflet automatique.** C'est le principe du **GitOps**.

## Le schéma

```
   Session web (Claude Code)  ┐
   VS Code sur le PC          ├──git push──▶  GitHub (branche main = LA vérité)
   Claude Code mobile         ┘                      │
                                                     │  GitHub Actions (au merge sur main)
                                                     ▼
                                            VPS  ──  reflète toujours main
```

- Aucun poste n'est « le bon » : ce sont tous des **clients** qui poussent vers GitHub.
- Le serveur ne décide de rien : un **push sur `main` déclenche le déploiement**, donc le serveur
  reflète automatiquement le dernier commit.

## Les 3 réflexes pour travailler depuis plusieurs machines

Git est *fait* pour ça. La discipline :

1. **Avant de coder** : récupérer le dernier état.
   ```bash
   git pull --rebase        # ou repartir d'une branche fraîche depuis main
   ```
2. **Travailler sur une branche**, jamais directement sur `main` :
   ```bash
   git checkout -b ma-feature
   # ... modifications ...
   git push -u origin ma-feature
   ```
3. **Fusionner via une Pull Request** sur GitHub → `main`. Le déploiement se déclenche tout seul.

Si deux postes modifient en parallèle, git **fusionne** automatiquement, ou signale un **conflit**
à résoudre. On ne perd jamais de travail, on n'écrase jamais celui de l'autre poste par accident.

> **En solo**, la PR peut sembler lourde, mais elle reste utile : elle fait tourner la CI (tests)
> *avant* que le code parte en production. Tu peux aussi pousser directement sur `main` pour aller
> vite — au prix de la sécurité d'un garde-fou.

## La règle d'or : ne jamais éditer sur le serveur

**On ne modifie JAMAIS les fichiers du projet directement sur le VPS en SSH.**

Dès qu'on édite à la main sur le serveur, il **diverge** de GitHub (« config drift ») : on ne sait
plus quelle est la vraie version, et le prochain `git pull` peut écraser ou entrer en conflit avec
ces changements.

- SSH = **observer** (logs, debug, sauvegardes, `docker compose ps`). En lecture.
- Changer quelque chose = **commit → push → déploiement auto**. Toujours.

Le `.env` (secrets) est la seule exception légitime qui vit sur le serveur et pas dans git — et il
ne change quasiment jamais.

## Comment le serveur récupère le code : deux modèles

### Modèle A — Build sur le serveur (simple, recommandé pour démarrer)

L'Action se connecte en SSH et lance `git pull && docker compose up -d --build`. C'est ce que
documente [doc 04](04-deploiement-github-actions.md). Zéro infrastructure en plus.

### Modèle B — Image pré-construite (plus « pro »)

La CI **construit une image Docker**, la pousse sur un registre (**GitHub Container Registry /
GHCR**) avec un tag (ex. le SHA du commit), puis le VPS fait un simple `docker pull` + `up`.

```
push main → CI: docker build + push ghcr.io/compte/projet:<sha>
          → VPS: docker compose pull && up -d   (image immuable)
```

Avantages :
- **Rollback instantané** : pour revenir en arrière, on redéploie le tag précédent. Aucune
  reconstruction, aucune surprise — l'image est figée.
- **VPS déchargé** du build (utile si le serveur est juste en ressources).
- **Reproductibilité** : la même image testée en CI est exactement celle qui tourne en prod.

À adopter quand tu veux des rollbacks propres ou que les builds deviennent lourds. Voir aussi
[doc 08 — variante GHCR](08-annexes.md#variante-images-pré-construites-ghcr).

## Et plus haut dans l'échelle ?

Les équipes à grande échelle vont jusqu'au **GitOps « pull »** : un agent sur le cluster
(ArgoCD, Flux sur Kubernetes) **surveille le repo** et synchronise l'état en continu, sans même
de push SSH. C'est puissant mais **largement sur-dimensionné** pour quelques petits projets.
Pour ton cas, **GitHub Actions → déploiement** est le bon niveau.

## Environnements (quand tu seras prêt)

Les pros séparent souvent :

| Branche | Déploie vers | Usage |
|---------|--------------|-------|
| `main` | serveur **production** | ce que voient les utilisateurs |
| `develop` (optionnel) | serveur/sous-domaine **staging** | tester avant la prod |

Pour commencer, **un seul environnement** (`main` → production) suffit. Tu ajouteras un staging le
jour où tu voudras tester sans risque.

## Récapitulatif

- **GitHub = source de vérité unique.** Le VPS n'est qu'un reflet de `main`.
- **Commit depuis n'importe où** ; git gère la fusion entre postes.
- **Branches + PR** ; `main` se déploie tout seul.
- **Jamais d'édition directe sur le serveur** (sauf `.env`).
- **Build sur serveur** pour démarrer ; **image GHCR** quand tu veux des rollbacks.
