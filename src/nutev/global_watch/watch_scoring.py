from __future__ import annotations


def score_watch_item(item: dict) -> float:
    text = (
        f"{item.get('title', '')} "
        f"{item.get('evidence_type', '')} "
        f"{item.get('category', '')}"
    ).lower()
    score = float(item.get("relevance_score") or 0)

    bonus = [
        ("clinical practice guideline", 60),
        ("practice guideline", 55),
        ("guideline update", 60),
        ("guideline", 50),
        ("food-based dietary guideline", 45),
        ("food guide", 40),
        ("nutrition guideline", 40),
        ("scientific statement", 45),
        ("consensus", 45),
        ("consensus report", 45),
        ("expert consensus", 45),
        ("practice advisory", 45),
        ("practice guidance", 42),
        ("guidance statement", 42),
        ("joint statement", 40),
        ("position statement", 40),
        ("position paper", 40),
        ("policy statement", 40),
        ("clinical guidance", 40),
        ("practice recommendation", 40),
        ("standards of care", 45),
        ("clinical pathway", 40),
        ("care pathway", 35),
        ("systematic review", 35),
        ("meta-analysis", 35),
        ("meta analysis", 35),
        ("network meta-analysis", 35),
        ("network meta analysis", 35),
        ("umbrella review", 35),
        ("overview of reviews", 35),
        ("review of reviews", 35),
        ("randomized trial", 30),
        ("randomised trial", 30),
        ("pragmatic trial", 30),
        ("official report", 25),
        ("framework", 25),
        ("questionnaire", 25),
        ("instrument", 25),
        ("scale", 25),
        ("food literacy", 15),
        ("food and nutrition literacy", 15),
        ("nutrition literacy", 15),
        ("culinary medicine", 15),
        ("food agency", 15),
        ("cooking skills", 12),
        ("food skills", 12),
        ("food label", 10),
        ("adherence", 15),
        ("dietary adherence", 15),
        ("implementation", 15),
        ("implementation science", 15),
        ("implementation research", 15),
        ("implementation strategy", 15),
        ("implementation outcomes", 15),
        ("implementation fidelity", 15),
        ("implementation facilitation", 15),
        ("implementation support", 12),
        ("implementation evaluation", 12),
        ("process evaluation", 15),
        ("knowledge translation", 15),
        ("behavioral lifestyle intervention", 15),
        ("behavioral weight loss", 15),
        ("goal setting", 12),
        ("social support", 12),
        ("food access", 12),
        ("lifestyle counseling", 12),
        ("lifestyle counselling", 12),
        ("medical nutrition therapy", 15),
        ("nutrition counseling", 12),
        ("nutrition counselling", 12),
        ("nutrition care", 10),
        ("feasibility", 15),
        ("sustainability", 12),
        ("dissemination", 12),
        ("scale-up", 12),
        ("scale up", 12),
        ("food environment", 15),
        ("behavior change technique", 12),
        ("barriers and facilitators", 12),
        ("mediterranean diet", 12),
        ("dash", 12),
        ("mind diet", 12),
        ("portfolio diet", 12),
        ("nordic diet", 12),
        ("new nordic diet", 12),
        ("plant-based", 12),
        ("whole-food plant-based", 12),
        ("whole food plant based", 12),
        ("planetary health diet", 12),
        ("eat-lancet", 12),
        ("meal planning", 12),
        ("commensality", 12),
        ("shared meals", 10),
        ("family meals", 10),
        ("social eating", 10),
        ("eat together", 10),
        ("self-efficacy", 10),
        ("self efficacy", 10),
        ("obesity", 10),
        ("cardiometabolic", 10),
        ("weight management", 10),
        ("adiposity", 10),
        ("diabetes", 10),
        ("prediabetes", 10),
        ("hypertension", 10),
        ("blood pressure", 10),
        ("dyslipidemia", 10),
        ("dyslipidaemia", 10),
        ("hyperlipidemia", 10),
        ("hyperlipidaemia", 10),
        ("hypercholesterolemia", 10),
        ("hypercholesterolaemia", 10),
        ("hypertriglyceridemia", 10),
        ("hypertriglyceridaemia", 10),
        ("insulin resistance", 10),
        ("masld", 10),
        ("nafld", 10),
        ("mafld", 10),
        ("nash", 10),
        ("steatotic liver disease", 12),
        ("metabolic dysfunction-associated steatotic liver disease", 12),
        ("fatty liver", 12),
        ("non-alcoholic steatohepatitis", 12),
        ("nonalcoholic steatohepatitis", 12),
    ]
    for key, value in bonus:
        if key in text:
            score += value

    if item.get("is_new"):
        score += 15
    if item.get("download_status") == "pdf":
        score += 10
    elif item.get("download_status") == "html_snapshot":
        score += 5

    provider = (item.get("source_provider") or "").lower()
    provider_bonus = {
        "official_sources": 20,
        "pubmed": 8,
        "europepmc": 8,
        "openalex": 6,
        "crossref": 5,
    }
    score += provider_bonus.get(provider, 0)

    penalties = [
        ("editorial", -40),
        ("commentary", -35),
        ("letter", -30),
        ("case report", -30),
        ("animal", -30),
        ("in vitro", -30),
        ("pediatric", -15),
        ("child", -15),
        ("adolescent", -15),
        ("login", -30),
        ("buy", -30),
        ("paywall", -30),
        ("mostdownload", -30),
    ]
    for key, value in penalties:
        if key in text:
            score += value

    if not (item.get("title") or "").strip():
        score -= 20

    return round(score, 3)
