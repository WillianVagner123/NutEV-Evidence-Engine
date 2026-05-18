from nutev.analysis.relevance import keep_candidate_for_download, score_record


SCORING_RULES = {
    "keyword_points": {},
    "source_points": {},
    "workstream_points": {},
}


def test_out_of_scope_pediatric_article_is_downranked_and_flagged():
    record = {
        "source": "pubmed",
        "title": "Pediatric obesity dietary intervention protocol",
        "abstract": "Children and adolescents in a school setting.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/1/",
    }

    scored = score_record(record, SCORING_RULES, "busca2b")

    assert "pediatric_population" in scored["out_of_scope_flags"]
    assert scored["out_of_scope_penalty"] < 0
    assert not keep_candidate_for_download(scored, "busca2b")


def test_out_of_scope_animal_in_vitro_article_is_hard_excluded():
    record = {
        "source": "pubmed",
        "title": "In vitro mouse adipocyte model of low-carb diet response",
        "abstract": "Cell culture and murine experiment.",
        "url": "https://pubmed.ncbi.nlm.nih.gov/2/",
    }

    scored = score_record(record, SCORING_RULES, "busca2b")

    assert "animal_or_preclinical" in scored["out_of_scope_flags"]
    assert "bench_or_cellular" in scored["out_of_scope_flags"]
    assert not keep_candidate_for_download(scored, "busca2b")


def test_adult_coherent_lifestyle_trial_is_rescued_for_download():
    record = {
        "source": "pubmed",
        "title": "Randomized lifestyle intervention trial for adult obesity and dietary adherence",
        "abstract": "Adults with cardiometabolic risk received a Mediterranean diet implementation program.",
        "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC1234567/",
    }

    scored = score_record(record, SCORING_RULES, "busca2b")

    assert scored["out_of_scope_flags"] == []
    assert scored["relevance_score"] >= 7
    assert keep_candidate_for_download(scored, "busca2b")
