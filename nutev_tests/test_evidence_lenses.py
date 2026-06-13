from nutev.analysis.nutev_classifier import classify_evidence


ONTOLOGY = {
    "domains": {
        "clinical_outcomes": ["remission", "risk"],
        "implementation": ["implementation", "delivery"],
        "equity": ["equity", "low-income"],
        "dietary_patterns": ["mediterranean", "diet quality"],
        "policy_systems": ["guideline", "policy"],
    },
    "outcomes": {},
}

LENSES = {
    "lenses": {
        "busca1": {
            "focus": "policy_systems",
            "domains": ["policy_systems", "dietary_patterns", "equity"],
        },
        "busca2a": {
            "focus": "clinical_outcomes",
            "domains": ["clinical_outcomes", "dietary_patterns", "policy_systems"],
        },
        "busca2b": {
            "focus": "implementation",
            "domains": ["implementation", "clinical_outcomes", "dietary_patterns"],
        },
        "a3": {
            "focus": "framework",
            "domains": ["implementation", "policy_systems", "dietary_patterns"],
        },
    }
}


def test_evidence_lenses_reference_known_ontology_domains():
    known_domains = set(ONTOLOGY["domains"])
    configured_domains = {
        domain
        for lens in LENSES["lenses"].values()
        for domain in lens.get("domains", [])
    }

    assert configured_domains <= known_domains


def test_evidence_lenses_classify_workstream_aligned_records():
    records = [
        {
            "title": "Mediterranean diet quality guideline for low-income adults",
            "abstract": "",
            "extracted_text": "",
        },
        {
            "title": "Implementation delivery program for diabetes remission risk",
            "abstract": "",
            "extracted_text": "",
        },
    ]

    classified = classify_evidence(records, ONTOLOGY, LENSES)

    assert classified[0]["lens_busca1_present"] == 1
    assert classified[0]["lens_busca2a_present"] == 1
    assert classified[1]["lens_busca2b_present"] == 1
    assert "busca2b" in classified[1]["evidence_lenses"]
