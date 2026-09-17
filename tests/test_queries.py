"""Agent-question tests (handover §24, §30 Phase 4): Q1-Q10 answered from the Pepys graph alone."""
from pathlib import Path

import pytest
from rdflib import Graph, URIRef

ROOT = Path(__file__).resolve().parents[1]
PEPYS = "https://codicum.eu/data/pepys-2981/"
NCBI = "http://purl.obolibrary.org/obo/NCBITaxon_"
CODHMO = "https://codicum.eu/ontology/codhmo#"


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


def load(name):
    return Graph().parse(ROOT / "examples" / f"{name}.ttl")


def test_mixed_ranks_stay_candidates_and_are_not_forced_to_compete():
    g = load("sargent-2025-aein656-gold-leaf-adhesive")
    assert {row[2].removeprefix(NCBI) for row in ask(g, "q04")} == {"9789", "9823", "9833", "9895"}
    assert ask(g, "q05") == set()  # nothing asserted as fact
    assert ask(g, "q06") == set()  # candidates may co-occur in a mixture


def test_mixed_paste_has_bulk_and_binder_without_taxon():
    g = load("kasso-2025-pakepu-white-paste")
    role = URIRef(CODHMO + "hasComponentRole")
    assert not list(g.triples((None, role, None)))  # never asserted
    RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
    roles = {str(g.value(p, URIRef(RDF + "object"))).rsplit("#", 1)[1]
             for p in g.subjects(URIRef(RDF + "predicate"), role)}
    assert roles == {"role-bulk", "role-binder"}
    assert ask(g, "q04") == set() and ask(g, "q05") == set()


def test_charter_samples_trace_to_their_layers():
    base = "https://codicum.eu/data/illustrative-charter/"
    assert ask(load("charter-illustrative"), "q01") == {
        ("ILLUSTRATIVE-C2-parchment", base + "parchment-support"),
        ("ILLUSTRATIVE-C2-ink", base + "ink-layer"),
        ("ILLUSTRATIVE-C2-seal", base + "seal"),
    }


def test_birth_girdle_separates_support_residue_and_use():
    g = load("fiddyment-2021-birth-girdle")
    by_hyp = {row[1]: row[2].removeprefix(NCBI) for row in ask(g, "q04")
              if row[1].startswith("https://codicum.eu/data/fiddyment-2021/")}
    short = {k.rsplit("/", 1)[1]: v for k, v in by_hyp.items()}
    assert short == {"T-support-sheep": "9940", "R-honey": "7460", "R-milk": "9963"}
    assert ask(g, "q05") == set()
    contradicted = {h.rsplit("/", 1)[1] for h, _ in ask(g, "q08")}
    assert contradicted == {"R-eggyolk"}  # control blank weakens egg yolk
    assert ask(g, "q09") == set()        # the use interpretation now has evidence


def test_missale_calf_is_derived_by_parchment_rule_not_observed():
    g = load("palandri-2024-missale-nidrosiense")
    q = """PREFIX crminf: <http://www.cidoc-crm.org/extensions/crminf/>
           SELECT ?premise ?conclusion WHERE {
             ?i crminf:J3_applied <https://codicum.eu/ontology/codhmo#rule-parchment-bos-is-calf> ;
                crminf:J1_used_as_premise ?premise ; crminf:J2_concluded_that ?conclusion . }"""
    rows = {tuple(str(v).rsplit("/", 1)[1] for v in r) for r in g.query(q)}
    assert rows == {("T-bos", "H-calf")}
    assert {r[2].removeprefix(NCBI) for r in ask(g, "q04")} == {"9903", "9940"}  # no "calf" taxon


def test_scythian_exclusive_alternatives_compete():
    g = load("brandt-2023-scythian-leather")
    pairs = {frozenset(x.rsplit("/", 1)[1] for x in p) for p in ask(g, "q06")}
    assert pairs == {frozenset(p) for p in [("T34-panthera", "T34-mustelidae"),
                                              ("T34-panthera", "T34-hyaenidae"),
                                              ("T34-mustelidae", "T34-hyaenidae")]}
    assert NCBI + "9606" in {r[2] for r in ask(g, "q04")}
    assert ask(g, "q05") == set()
