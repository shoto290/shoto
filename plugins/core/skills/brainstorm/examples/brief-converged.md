<!-- Schema is stable; any planning skill can parse this format. -->

# Brainstorm: Faut-il ajouter un mode offline à notre app mobile ?

## Context

L'équipe produit reçoit des plaintes récurrentes d'utilisateurs en zones de mauvaise connectivité (transports, sous-sols, voyages). L'app actuelle exige une connexion permanente pour toute lecture. Avant de planifier un chantier potentiellement coûteux, l'équipe veut cadrer le périmètre minimal viable d'un mode offline et décider si l'investissement vaut le coup.

## Rules applied

- All ideas welcome.
- No judgment during the brainstorm.
- More ideas the better — go for quantity.
- Duplicates are OK.

## Rounds

### Round 1 — Starbursting

1. Who — utilisateurs en transports en commun (métro, train).
2. Who — utilisateurs en déplacement international (sans data roaming).
3. What — lecture seule des écrans déjà visités récemment.
4. What — écriture différée des actions (file d'attente synchronisée plus tard).
5. When — déclenchement automatique dès perte de signal.
6. Where — uniquement les écrans listés dans une whitelist (home, favoris, lectures récentes).
7. Why — réduire le churn lié aux frictions de connectivité.
8. How — cache local chiffré + queue de mutations + résolution de conflits last-write-wins.

### Round 2 — How-Now-Wow

1. Cache lecture seule des derniers écrans visités (simple, gros gain UX).
2. Queue d'écriture différée pour les actions non critiques.
3. Mode "voyage" activable manuellement avec pré-téléchargement explicite.
4. Synchronisation bidirectionnelle complète avec résolution de conflits.
5. Détection automatique de la perte de signal + bannière persistante.

## Evaluation

### How-Now-Wow

| Idea | Bucket (Now/How/Wow) | Justification |
|------|----------------------|---------------|
| Cache lecture seule des écrans récents             | Now | Faible coût technique, impact UX immédiat sur la majorité des plaintes. |
| Queue d'écriture différée                          | Wow | Originalité moyenne mais effet "magique" pour l'utilisateur, complexité maîtrisée. |
| Mode voyage avec pré-téléchargement manuel         | How | Très original mais coûteux à designer côté UX et infra (volumes, expiration). |
| Synchronisation bidirectionnelle complète          | How | Cher, risqué (conflits), faible ratio valeur/effort à ce stade. |
| Détection perte de signal + bannière               | Now | Trivial, complète bien le cache lecture seule. |

## Decision

CONVERGED

## Retained idea

Livrer un **mode offline minimal "lecture + différé"** : cache local chiffré des derniers écrans visités, file d'attente des actions d'écriture non critiques (likes, commentaires, brouillons), et bannière persistante quand la connexion est perdue. Out of scope pour cette itération : la synchronisation bidirectionnelle avec résolution de conflits, le pré-téléchargement manuel "mode voyage", et toute action transactionnelle (paiement, modification de compte). La cible prioritaire est l'utilisateur en transports en commun, pas le voyageur international.

## Open questions

- Quelle taille maximale de cache local avant éviction LRU ?
- Politique de purge du cache à la déconnexion / changement de compte ?
- Quelles actions sont jugées "non critiques" et donc différables sans risque ?

## Metadata

- **Date**: 2026-05-27
- **Slug**: mode-offline-app-mobile
- **Rounds**: 2
