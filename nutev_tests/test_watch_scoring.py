from nutev.global_watch.watch_scoring import score_watch_item


def test_guideline_scores_more_than_editorial():
    assert score_watch_item({'title':'new guideline', 'source_provider':'pubmed'}) > score_watch_item({'title':'editorial note', 'source_provider':'pubmed'})


def test_systematic_review_scores_more_than_generic():
    assert score_watch_item({'title':'systematic review of diet'}) > score_watch_item({'title':'diet study'})


def test_pdf_scores_more_than_metadata_only():
    assert score_watch_item({'title':'trial', 'download_status':'pdf'}) > score_watch_item({'title':'trial', 'download_status':'metadata_only'})


def test_official_sources_bonus():
    assert score_watch_item({'title':'report', 'source_provider':'official_sources'}) > score_watch_item({'title':'report', 'source_provider':'crossref'})
