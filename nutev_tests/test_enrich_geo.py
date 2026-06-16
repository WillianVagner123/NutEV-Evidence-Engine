from __future__ import annotations

from nutev.analysis.enrich_geo import detect_language, enrich_record, region_for


def test_region_for_known_and_unknown():
    assert region_for("BR") == "South America"
    assert region_for("us") == "North America"
    assert region_for("DE") == "Europe"
    assert region_for("CN") == "Asia"
    assert region_for("ZZ") == ""


def test_detect_language_scripts():
    assert detect_language("糖尿病と食事の研究") == "ja"  # contains kana
    assert detect_language("2型糖尿病") == "zh"  # pure Han
    assert detect_language("средиземноморская диета") == "ru"
    assert detect_language("حمية البحر الأبيض المتوسط") == "ar"


def test_detect_language_latin_stopwords_and_default():
    assert detect_language("dieta mediterrânea e saúde no estudo") == "pt"
    assert detect_language("the effect of diet on cardiovascular outcomes") == "en"
    assert detect_language("") == ""


def test_enrich_record_country_region_language():
    row = {"country_codes": ["BR", "US", "BR"], "title": "Mediterranean diet", "abstract": "trial"}
    out = enrich_record(row)
    assert out["countries"] == ["BR", "US"]  # de-duped, order preserved
    assert out["country"] == "BR"
    assert out["region"] == "South America"
    assert out["language"] == "en"  # detected fallback
    assert out["cited_by_count"] == 0


def test_enrich_record_passthrough_language_and_counts():
    row = {"country_codes": [], "language": "pt", "cited_by_count": "17"}
    out = enrich_record(row)
    assert out["language"] == "pt"  # provider-reported wins, no detection
    assert out["countries"] == []
    assert out["country"] == ""
    assert out["region"] == ""
    assert out["cited_by_count"] == 17


def test_enrich_record_string_country_codes():
    out = enrich_record({"country_codes": "br; us"})
    assert out["countries"] == ["BR", "US"]
    assert out["region"] == "South America"
