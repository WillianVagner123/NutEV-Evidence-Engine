# Food Competence Semantic Extension

This extension adds a focused semantic block for food competence, eating competence, cooking self-efficacy, meal preparation confidence, meal planning self-efficacy, and related validated instruments.

Rationale:

- Improves coverage for NutMEV article 3 / framework evidence around food literacy, culinary skills, food agency, and adherence instruments.
- Adds behavior and instrument terms through the existing querypack extension pattern, preserving the base semantic block and avoiding broad refactors.
- Extends `food_literacy_agency` for article 3 retrieval and `adherence_persistence` for busca2b retrieval, because food competence often appears as a mediator of dietary adherence and maintenance.
- Keeps precision by using specific phrases such as `food competence questionnaire`, `eating competence inventory`, `meal preparation self-efficacy`, and `healthy grocery shopping skills` instead of generic terms such as `competence` alone.
