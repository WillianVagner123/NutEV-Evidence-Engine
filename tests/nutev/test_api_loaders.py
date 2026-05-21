from pathlib import Path
import json

import pandas as pd

from nutev.api.loaders import filter_df, list_artifacts, paginate_df, read_csv_safe, read_json_safe, read_markdown_safe, read_xlsx_safe


def test_safe_readers_missing(tmp_path: Path):
    assert read_csv_safe(tmp_path/'x.csv').empty
    assert read_xlsx_safe(tmp_path/'x.xlsx').empty
    out = read_json_safe(tmp_path/'x.json')
    assert out.get('available') is False
    assert read_markdown_safe(tmp_path/'x.md') == ''


def test_safe_readers_existing(tmp_path: Path):
    pd.DataFrame([{'a': 1}]).to_csv(tmp_path/'a.csv', index=False)
    assert len(read_csv_safe(tmp_path/'a.csv')) == 1
    (tmp_path/'a.json').write_text(json.dumps({'k': 'v'}), encoding='utf-8')
    assert read_json_safe(tmp_path/'a.json')['k'] == 'v'


def test_filter_and_paginate_and_artifacts(tmp_path: Path):
    df = pd.DataFrame([{'x':'abc'},{'x':'def'}])
    filt = filter_df(df, {'x': 'ab'})
    assert len(filt) == 1
    page = paginate_df(df, limit=1, offset=1)
    assert page['total'] == 2 and len(page['items']) == 1
    (tmp_path/'02_metadata').mkdir(parents=True)
    pd.DataFrame([{'a':1}]).to_csv(tmp_path/'02_metadata'/'f.csv', index=False)
    artifacts = list_artifacts(tmp_path)
    assert artifacts and artifacts[0]['artifact_type'] == '02_metadata'
