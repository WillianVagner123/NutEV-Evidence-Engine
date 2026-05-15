def score_watch_item(item):
    text = f"{item.get('title','')} {item.get('evidence_type','')} {item.get('category','')}".lower()
    score = float(item.get('relevance_score') or 0)

    bonus = [
        ('clinical practice guideline', 60), ('guideline update', 60), ('guideline', 50),
        ('scientific statement', 45), ('consensus', 45), ('position statement', 40),
        ('systematic review', 35), ('meta-analysis', 35), ('umbrella review', 35),
        ('randomized trial', 30), ('randomised trial', 30), ('pragmatic trial', 30),
        ('official report', 25), ('framework', 25), ('questionnaire', 25), ('instrument', 25), ('scale', 25),
        ('food literacy', 15), ('culinary medicine', 15), ('adherence', 15), ('implementation', 15), ('feasibility', 15),
        ('obesity', 10), ('cardiometabolic', 10), ('diabetes', 10), ('hypertension', 10), ('dyslipidemia', 10), ('masld', 10), ('nafld', 10),
    ]
    for k, v in bonus:
        if k in text:
            score += v

    if item.get('is_new'): score += 15
    if item.get('download_status') == 'pdf': score += 10
    elif item.get('download_status') == 'html_snapshot': score += 5

    provider = (item.get('source_provider') or '').lower()
    provider_bonus = {'official_sources': 20, 'pubmed': 8, 'europepmc': 8, 'openalex': 6, 'crossref': 5}
    score += provider_bonus.get(provider, 0)

    penalties = [('editorial', -40), ('commentary', -35), ('letter', -30), ('case report', -30), ('animal', -30), ('in vitro', -30), ('pediatric', -15), ('child', -15), ('adolescent', -15), ('login', -30), ('buy', -30), ('paywall', -30), ('mostdownload', -30)]
    for k, v in penalties:
        if k in text:
            score += v
    if not (item.get('title') or '').strip():
        score -= 20
    return round(score, 3)
