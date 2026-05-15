import json
from pathlib import Path


def test_taxonomy_v4_blocks_present():
    d=json.loads(Path('config/keyword_taxonomy.json').read_text(encoding='utf-8'))
    assert 'controlled_vocabulary' in d and 'update_terms' in d and 'institutions_societies' in d
