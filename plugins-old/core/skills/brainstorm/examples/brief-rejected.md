<!-- Schema is stable; any planning skill can parse this format. -->

# Brainstorm: Faut-il intégrer un chatbot IA généraliste dans le dashboard admin ?

## Context

Un sponsor interne pousse pour ajouter un chatbot IA généraliste dans le dashboard admin "pour faire moderne". L'équipe veut explorer sérieusement les cas d'usage avant d'investir, et décider si le besoin est réel ou cosmétique. Les admins existants sont peu nombreux et déjà formés à l'outil actuel.

## Rules applied

- All ideas welcome.
- No judgment during the brainstorm.
- More ideas the better — go for quantity.
- Duplicates are OK.

## Rounds

### Round 1 — What-if

1. What if le chatbot répondait aux questions sur les métriques du dashboard → duplique les graphiques déjà visibles.
2. What if le chatbot exécutait des actions admin → besoin de garde-fous lourds (authz, audit, rollback).
3. What if le chatbot était un assistant de recherche dans la doc interne → utile mais hors périmètre dashboard.
4. What if le chatbot synthétisait les alertes de la semaine → faisable, mais un widget statique suffit.
5. What if le chatbot guidait l'onboarding des nouveaux admins → utile une seule fois par admin.
6. What if le chatbot expliquait les écarts entre deux périodes → niche, déjà couvert par les filtres.
7. What if le chatbot générait des rapports exportables → recouvre la fonctionnalité Export existante.
8. What if le chatbot servait de couche d'accessibilité (lecture vocale) → vrai besoin, mais résolu par les outils OS.

### Round 2 — SWOT (sur le candidat le plus prometteur : assistant de recherche dans la doc interne)

1. Strengths — réduit le temps de recherche pour les nouveaux admins.
2. Weaknesses — hors périmètre du dashboard ; duplique un futur projet "knowledge base".
3. Opportunities — pourrait devenir un produit transverse à toute l'entreprise.
4. Threats — coût d'embedding + maintenance des sources ; risque de réponses hallucinées sur des données sensibles.

## Evaluation

### SWOT

| Quadrant | Bullets |
|----------|---------|
| Strengths     | Onboarding plus rapide ; ressenti "moderne" auprès du sponsor. |
| Weaknesses    | Sort du périmètre dashboard ; faible nombre d'admins → faible ROI ; aucun cas d'usage propre au dashboard n'a survécu au round 1. |
| Opportunities | Pourrait justifier un projet "assistant doc" transverse, séparé du dashboard. |
| Threats       | Hallucinations sur données admin sensibles ; coût récurrent d'embeddings ; concurrence interne avec un futur knowledge base. |

## Decision

DROPPED

## Drop reason

Aucun des cas d'usage générés ne survit à l'évaluation : soit ils dupliquent une fonctionnalité déjà présente (graphiques, exports, filtres), soit ils sortent du périmètre du dashboard (recherche dans la doc, onboarding général), soit ils introduisent un risque disproportionné par rapport au gain (actions admin via langage naturel). La demande initiale relève d'un effet de mode plus que d'un besoin utilisateur identifié. La question est **fermée pour le dashboard admin**, mais l'idée d'un assistant transverse de recherche documentaire reste **parquée** pour un brainstorm séparé, à initier seulement si une demande utilisateur émerge.

## Open questions

- Faut-il documenter formellement le refus auprès du sponsor pour éviter une relance ?
- Y a-t-il un besoin réel d'assistant doc côté support / customer success qui mériterait son propre cadrage ?
- À quels signaux saurait-on que la décision doit être réévaluée (volume d'admins, complexité du dashboard) ?

## Metadata

- **Date**: 2026-05-27
- **Slug**: chatbot-ia-dashboard-admin
- **Rounds**: 2
