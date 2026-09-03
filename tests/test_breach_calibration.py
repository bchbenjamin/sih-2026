from scripts.phase2.breach_parameters import PLACEHOLDER_CITATIONS


def test_template_citation_cannot_unlock_solver_run():
    assert "your source / report / calibration id" in PLACEHOLDER_CITATIONS
    assert "" in PLACEHOLDER_CITATIONS
