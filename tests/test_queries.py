"""Agent-question tests (handover §24, §30 Phase 4): Q1-Q10 answered from the Pepys graph alone."""
from pathlib import Path

import pytest
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[1]
PEPYS = "https://codicum.eu/data/pepys-2981/"
NCBI = "http://purl.obolibrary.org/obo/NCBITaxon_"


@pytest.fixture(scope="module")
def graph():
    return Graph().parse(ROOT / "examples" / "pepys-IN-A001.ttl")


def ask(graph, name):
    query = next((ROOT / "queries").glob(f"{name}-*.rq")).read_text(encoding="utf-8")
    return {tuple(str(v).removeprefix(PEPYS) for v in row) for row in graph.query(query)}


def test_q01_what_was_sampled(graph):
    assert ask(graph, "q01") == {("IN-A001", "adhesive-layer-frag4")}


def test_q02_from_where(graph):
    assert ask(graph, "q02") == {("IN-A001", "Beneath fragment 4, page 5", "MS2981-p5-frag4", "MS2981")}


def test_q03_analytical_method(graph):
    assert ask(graph, "q03") == {("search-1", "searchdb-1")}


def test_q04_compatible_taxa_are_candidates(graph):
    assert ask(graph, "q04") == {("PEP001", "H1", NCBI + "9986"), ("PEP001", "H2", NCBI + "7900")}


def test_q05_no_hypothesis_leaks_into_facts(graph):
    """An agent asking for asserted biological sources must get nothing back."""
    assert ask(graph, "q05") == set()


def test_q06_competing_hypotheses(graph):
    pairs = {frozenset(p) for p in ask(graph, "q06")}
    assert pairs == {frozenset(p) for p in [("H1", "H2"), ("H1", "H3"), ("H2", "H3"),
                                              ("HI1", "HI2"), ("HI1", "HI3"), ("HI2", "HI3")]}


def test_q07_supporting_evidence_does_not_discriminate(graph):
    rows = ask(graph, "q07")
    assert {(h, e) for h, _, e in rows} == {("H1", "PEP001"), ("H2", "PEP001")}
    assert all(r.endswith("compatibleWith") for _, r, _ in rows)


def test_q08_no_contradicting_evidence_yet(graph):
    assert ask(graph, "q08") == set()


def test_q09_historical_interpretations_unresolved(graph):
    assert ask(graph, "q09") == {("HI1",), ("HI2",), ("HI3",)}


def test_q10_database_generation(graph):
    (row,) = ask(graph, "q10")
    assert row[:3] == ("searchdb-1", "dbgen-1", "seqdb-gen")
    assert row[4].endswith("#Denatured")
