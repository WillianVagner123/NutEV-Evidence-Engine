from pathlib import Path

from nutev.querypacks.provider_queries import render_queries_for_provider
from nutev.settings import load_json


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def test_culinary_medicine_supplement_expands_provider_queries() -> None:
    taxonomy = load_json(_repo_root() / "config" / "keyword_taxonomy.json")

    busca2b_queries = render_queries_for_provider(taxonomy, "busca2b", "pubmed")
    busca2b_joined = "\n".join(busca2b_queries)

    assert '"culinary medicine intervention"[Title/Abstract]' in busca2b_joined
    assert '"teaching kitchen intervention"[Title/Abstract]' in busca2b_joined
    assert '"experiential nutrition education"[Title/Abstract]' in busca2b_joined


def test_framework_queries_include_teaching_kitchen_curriculum_terms() -> None:
    taxonomy = load_json(_repo_root() / "config" / "keyword_taxonomy.json")

    framework_queries = render_queries_for_provider(taxonomy, "a3", "europepmc")
    framework_joined = "\n".join(framework_queries)

    assert 'TITLE_ABS:"culinary medicine curriculum"' in framework_joined
    assert 'TITLE_ABS:"teaching kitchen curriculum"' in framework_joined
    assert 'TITLE_ABS:"cooking self-efficacy scale"' in framework_joined
