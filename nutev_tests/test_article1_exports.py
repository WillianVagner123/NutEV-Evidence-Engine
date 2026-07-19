"""Article-1 reproducible exports (§17): A/B/C/D matrix, PRISMA counts, dictionary."""
from __future__ import annotations

from nutev.export.article1_exports import (
    abcd_matrix_rows,
    prisma_counts,
    prisma_diagram_mermaid,
)


def test_abcd_matrix_wide_shape():
    rows = [{
        "name": "Guia", "country": "brazil", "reference": "MoH. 2014.",
        "domain_A_state": "RECOMMENDED", "domain_A_intensity": 2,
        "domain_B_state": "OPERATIONALIZED", "domain_B_intensity": 3,
        "domain_C_state": "MENTIONED", "domain_C_intensity": 1,
        "domain_D_state": "NOT_ASSESSED", "domain_D_intensity": "",
    }]
    matrix = abcd_matrix_rows(rows)
    m = matrix[0]
    assert m["A_state"] == "RECOMMENDED" and m["A_intensity"] == 2
    assert m["B_intensity"] == 3
    # n_domains_positive counts RECOMMENDED/OPERATIONALIZED (A, B) = 2.
    assert m["n_domains_positive"] == 2


def test_prisma_counts_included_is_pending():
    registries = {
        "file_assets": [1, 2, 3], "versions": [1, 2], "families": [1],
    }
    queue = [
        {"screen_flag": "ready_to_screen"},
        {"screen_flag": "ready_to_screen"},
        {"screen_flag": "no_full_text"},
    ]
    c = prisma_counts(registries, queue)
    assert c["identified_file_assets"] == 3
    assert c["unique_document_versions"] == 2
    assert c["ready_to_screen"] == 2
    assert c["excluded_no_full_text_or_poor_ocr"] == 1
    # The pipeline never declares a final included corpus.
    assert c["included"] == "pending"


def test_prisma_diagram_is_mermaid():
    c = prisma_counts({"file_assets": [1], "versions": [1], "families": [1]}, [])
    md = prisma_diagram_mermaid(c)
    assert md.startswith("```mermaid") and "flowchart TD" in md
    assert "PENDENTE" in md  # included stays pending in the diagram too
