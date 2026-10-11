"""FORAGE - search current theories across all domains (OpenAlex), cited never ingested, grouped by
domain for a structural fit. The HTTP is mocked; this pins the parsing, the domain grouping, and the
honest-when-unreachable behaviour."""
import concordance.papers as P


def test_search_parses_openalex(monkeypatch):
    fake = {"meta": {"count": 99}, "results": [
        {"display_name": "A critical monotone quantity", "publication_year": 2026,
         "authorships": [{"author": {"display_name": "A. Mathematician"}}],
         "concepts": [{"display_name": "Mathematics", "level": 0},
                      {"display_name": "Fluid dynamics", "level": 1},
                      {"display_name": "too-deep", "level": 3}],
         "cited_by_count": 5, "doi": "https://doi.org/10.x", "id": "https://openalex.org/W1",
         "abstract_inverted_index": {"A": [0], "coercive": [1], "functional": [2]}}]}
    monkeypatch.setattr(P, "_get", lambda url, timeout=12: fake)
    r = P.search("coercive functional")
    assert r["count"] == 1 and r["total"] == 99
    c = r["candidates"][0]
    assert c["title"] == "A critical monotone quantity" and c["year"] == 2026
    assert c["domains"] == ["Mathematics", "Fluid dynamics"]     # level <= 1 only; "too-deep" dropped
    assert c["abstract"] == "A coercive functional"               # rebuilt from the inverted index
    assert "NOT verified" in r["note"]


def test_structural_fit_groups_by_domain(monkeypatch):
    fake = {"meta": {"count": 2}, "results": [
        {"display_name": "X", "concepts": [{"display_name": "Physics", "level": 0},
                                           {"display_name": "Thermodynamics", "level": 1}]},
        {"display_name": "Y", "concepts": [{"display_name": "Mathematics", "level": 0},
                                           {"display_name": "Thermodynamics", "level": 1}]}]}
    monkeypatch.setattr(P, "_get", lambda url, timeout=12: fake)
    r = P.structural_fit("a monotone quantity controlling a nonlinear term")
    doms = {d["domain"]: d["hits"] for d in r["domains_touched"]}
    assert doms.get("Thermodynamics") == 2 and doms.get("Physics") == 1 and doms.get("Mathematics") == 1


def test_unreachable_source_is_honest(monkeypatch):
    def boom(url, timeout=12):
        raise OSError("no net")
    monkeypatch.setattr(P, "_get", boom)
    r = P.search("anything")
    assert r["count"] == 0 and "could not be reached" in r["note"]
