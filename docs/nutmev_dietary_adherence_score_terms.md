# Dietary adherence score expansion rationale

This note records a small NutMEV search-strategy improvement candidate for the recurring curation cycle.

## Gap observed

The current query and prioritization layers already cover broad adherence, diet quality, healthy eating index, Mediterranean/DASH/plant-based patterns, and cardiometabolic/lifestyle nutrition terms. A narrow remaining gap is explicit wording used by many observational studies, trials, and reviews for pattern adherence measures:

- dietary pattern adherence
- diet adherence score
- diet adherence index
- dietary adherence score
- dietary adherence index
- diet quality index
- diet quality score
- healthy eating index score
- alternate healthy eating index
- Mediterranean diet adherence score
- Mediterranean diet score
- DASH adherence
- DASH score
- plant-based diet index
- healthy plant-based diet index

## Operational rationale

These expressions are relevant to NutMEV because they capture adherence to dietary patterns and diet-quality constructs connected to obesity, cardiometabolic risk, diabetes, hypertension, dyslipidemia, MASLD/NAFLD, and lifestyle nutrition interventions. They are more precise than a broad expansion with isolated words such as score or index.

## Recommended integration point

Preferred code target for a follow-up patch:

- `src/nutev/querypacks/semantic_blocks.py`: add the terms to `adherence_persistence` and `lifestyle_nutrition_patterns`.
- `src/nutev/global_watch/watch_scoring.py`: add moderate bonus terms for the same phrases so Global Watch prioritizes newly captured records without treating every score/index paper as high priority.

## Noise control

Do not add standalone `score`, `index`, or `adherence score` without a diet-pattern or nutrition anchor. Keep terms coupled to diet, dietary pattern, Mediterranean, DASH, or plant-based language.
