"""Tests for live FAO FBDG discovery (mocked HTML, no network)."""
from __future__ import annotations

from nutev.acquire.fao_discovery import (
    collect_country_urls,
    country_to_sources,
    discover_fao_guides,
    scrape_country,
)

_HOME = """
<html><body>
  <a href="/nutrition/education/food-dietary-guidelines/regions/countries/brazil/en/">Brazil</a>
  <a href="/nutrition/education/food-dietary-guidelines/regions/countries/kenya/">Kenya</a>
  <a href="/other/link">Not a country</a>
</body></html>
"""

_BRAZIL = """
<html><body>
  <h1>Brazil</h1>
  <p>Official name</p><p>Guia Alimentar para a População Brasileira</p>
  <p>Publication year</p><p>2014</p>
  <h3>Downloadable materials</h3>
  <ul>
    <li><a href="/docs/guia_brasil.pdf">Guia Alimentar (PDF)</a></li>
    <li><a href="https://fao.org/docs/resumo.pdf">Resumo Executivo</a></li>
  </ul>
</body></html>
"""

_KENYA = """
<html><body>
  <h1>Kenya</h1>
  <p>Official name</p><p>Kenya National Dietary Guidelines</p>
  <p>Publication year</p><p>2017</p>
</body></html>
"""


class _Resp:
    def __init__(self, text="", code=200):
        self.text, self.status_code = text, code


class _Session:
    def __init__(self, mapping):
        self.mapping = mapping

    def get(self, url, timeout=None):
        return self.mapping.get(url, _Resp(code=404))


def test_collect_country_urls_normalizes_and_filters():
    urls = collect_country_urls(_HOME)
    assert any(u.endswith("/countries/brazil/en/") for u in urls)
    assert any(u.endswith("/countries/kenya/en/") for u in urls)   # missing /en/ appended
    assert all("/regions/countries/" in u for u in urls)
    assert not any("/other/link" in u for u in urls)


def test_scrape_country_reads_fields_and_downloadables():
    c = scrape_country(_BRAZIL, "https://fao.org/.../countries/brazil/en/")
    assert c["official_name"] == "Guia Alimentar para a População Brasileira"
    assert c["publication_year"] == "2014"
    assert len(c["downloadables"]) == 2
    assert c["country_slug"] == "brazil"


def test_country_to_sources_one_per_file():
    c = scrape_country(_BRAZIL, "https://fao.org/.../countries/brazil/en/")
    sources = country_to_sources(c)
    assert len(sources) == 2                        # two downloadable PDFs
    assert all(s["url"].endswith(".pdf") for s in sources)
    assert sources[0]["country"] == "brazil"
    assert sources[0]["document_version"] == "2014"


def test_country_without_files_falls_back_to_page():
    c = scrape_country(_KENYA, "https://fao.org/.../countries/kenya/en/")
    sources = country_to_sources(c)
    assert len(sources) == 1
    assert sources[0]["url"].endswith("/countries/kenya/en/")
    assert sources[0]["name"] == "Kenya National Dietary Guidelines"


def test_discover_fao_guides_end_to_end():
    home = "https://www.fao.org/nutrition/education/food-dietary-guidelines"
    brazil = "https://www.fao.org/nutrition/education/food-dietary-guidelines/regions/countries/brazil/en/"
    kenya = "https://www.fao.org/nutrition/education/food-dietary-guidelines/regions/countries/kenya/en/"
    session = _Session({home: _Resp(_HOME), brazil: _Resp(_BRAZIL), kenya: _Resp(_KENYA)})

    sources = discover_fao_guides(session, home_url=home)
    # Brazil (2 files) + Kenya (1 page) = 3 sources.
    assert len(sources) == 3
    countries = {s["country"] for s in sources}
    assert countries == {"brazil", "kenya"}
