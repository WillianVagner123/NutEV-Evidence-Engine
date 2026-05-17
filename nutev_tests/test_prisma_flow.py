from nutev.analysis.prisma import build_prisma_flow


def test_build_prisma_flow_uses_document_level_counts():
    rows = [
        {
            "title": "Obesity guideline",
            "doi": "10.1000/abc",
            "url": "https://example.org/a",
            "relevance_score": 9,
            "download_status": "metadata_only",
            "evidence_type": "guideline",
        },
        {
            "title": "Obesity guideline duplicate with pdf",
            "doi": "https://doi.org/10.1000/abc",
            "url": "https://example.org/b",
            "relevance_score": 9,
            "download_status": "pdf",
            "evidence_type": "guideline",
        },
        {
            "title": "Diet adherence trial",
            "url": "https://example.org/c",
            "year": 2024,
            "relevance_score": 8,
            "download_status": "metadata_only",
            "evidence_type": "trial",
        },
    ]

    flow = build_prisma_flow(rows, [], [])

    assert flow == {
        "registros_identificados": 3,
        "duplicados_removidos": 1,
        "registros_triados": 2,
        "documentos_com_pdf_ou_html": 1,
        "documentos_metadata_only": 1,
        "documentos_priorizados": 2,
    }
