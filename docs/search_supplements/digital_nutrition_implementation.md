# Digital Nutrition Implementation Supplement

This supplement expands NutMEV retrieval and prioritization for digital or remote nutrition interventions that remain anchored to the project scope: lifestyle nutrition, obesity, cardiometabolic risk, diabetes prevention, adherence, and implementation.

## Rationale

Digital delivery is increasingly common in lifestyle medicine and nutrition implementation studies, especially for diabetes prevention programs, remote dietitian support, mobile dietary self-monitoring, food diaries, app-supported adherence, telehealth nutrition counseling, and virtual lifestyle interventions. These records can be missed when searches rely only on generic implementation, diet, or lifestyle terms.

## Precision Guardrails

The expansion avoids broad standalone technology terms such as generic app, software, artificial intelligence, wearable, or digital platform. Terms are phrased with explicit nutrition, diet, dietitian, diabetes prevention, lifestyle intervention, adherence, or weight-loss anchors to reduce irrelevant digital health retrieval.

## Files

- `config/keyword_taxonomy_supplement_digital_nutrition.json`: query expansion terms and workstream web hints.
- `config/scoring_rules_supplement_digital_nutrition.json`: scoring boosts for retrieved digital nutrition implementation signals.
- `nutev_tests/test_digital_nutrition_supplements.py`: regression tests for query inclusion and score prioritization.
