from pathlib import Path
import json

from nutev.provider_settings import load_provider_registry, load_provider_settings, mask_secret, save_provider_settings
from nutev.audit.models import RecommendationCandidate


def test_provider_registry_loads():
    reg = load_provider_registry(Path('config'))
    assert reg.get('providers')


def test_provider_settings_save_without_secret(tmp_path: Path):
    save_provider_settings(tmp_path, {'providers': {'openai': {'enabled': True, 'mode': 'assistive', 'env_var': 'OPENAI_API_KEY', 'secret_source': 'env'}}})
    data = load_provider_settings(tmp_path)
    assert data['providers']['openai']['secret_source'] == 'env'
    txt = (tmp_path/'00_settings'/'provider_settings.local.json').read_text(encoding='utf-8')
    assert 'api_key' not in txt


def test_mask_secret():
    assert mask_secret('abcdef123456').startswith('ab')


def test_llm_governance_rules_load():
    rules = json.loads(Path('config/llm_governance_rules.json').read_text(encoding='utf-8'))
    assert 'final_recommendation_approval' in rules['forbidden_llm_roles']


def test_llm_cannot_approve_recommendation_without_claims():
    r = RecommendationCandidate(recommendation_id='r', recommendation_text='x', protocol_component='p', recommendation_status='approved_for_protocol', supporting_claim_ids=[])
    assert r.recommendation_status != 'approved_for_protocol'
