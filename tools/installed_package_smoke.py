"""Run with the clean venv Python -I, outside the checkout, after wheel install."""
from importlib.metadata import version
import json
from pathlib import Path
import sys

import nutev
from nutev.__version__ import __version__
from nutev.reference_identity import dedupe_records, normalize_doi
from nutev.tenancy import Principal

assert __version__ == version('nutev-nutmev')
assert 'site-packages' in str(Path(nutev.__file__).resolve()), 'source checkout shadowed installed wheel'
assert normalize_doi('https://doi.org/10.1000/fixture') == '10.1000/fixture'
rows = [{'title': 'Synthetic duplicate', 'doi': '10.1000/fixture', 'source_provider': 'fixture'},
        {'title': 'Synthetic duplicate', 'doi': 'https://doi.org/10.1000/fixture', 'source_provider': 'fixture'}]
assert len(dedupe_records(rows)) == 1
assert Principal is not None
print(json.dumps({'status': 'PASS', 'version': version('nutev-nutmev'),
                  'interpreter': sys.version.split()[0], 'source_checkout_used': False,
                  'external_providers_contacted': False}))
