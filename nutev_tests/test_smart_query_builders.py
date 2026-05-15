from nutev.querypacks.smart_builders import build_country_queries, build_guideline_queries, build_instrument_queries, build_smart_queries


def _t():
    return {
      'controlled_vocabulary':{'mesh_dec':['Lifestyle Medicine']},
      'update_terms':['guideline update'],
      'instrument_terms':['Food Literacy Questionnaire'],
      'institutions_societies':{'brazil_latam':['BVS'], 'europe':['NICE']},
      'negative_noise_terms':['editorial']
    }


def test_build_guideline_queries_contains_expected_terms():
    q=build_guideline_queries(_t(),'busca1','quick')[0]['query'].lower()
    assert 'guideline' in q and ('obesity' in q or 'cardiometabolic' in q) and ('diet' in q or 'nutrition' in q or 'lifestyle' in q)


def test_build_instrument_queries_contains_questionnaire():
    q=build_instrument_queries(_t(),'busca1','thesis')[0]['query'].lower()
    assert 'questionnaire' in q or 'instrument' in q


def test_build_country_queries_contains_institution():
    q=build_country_queries(_t(),'busca1','exhaustive')[0]['query']
    assert 'BVS' in q or 'NICE' in q


def test_mode_query_counts():
    tq=_t()
    a=len(build_smart_queries(tq,['busca1'],'quick')['busca1'])
    b=len(build_smart_queries(tq,['busca1'],'thesis')['busca1'])
    c=len(build_smart_queries(tq,['busca1'],'exhaustive')['busca1'])
    assert a < b < c
