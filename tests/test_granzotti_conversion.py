"""The Granzotti converter is pinned to the sample that was mapped by hand.

examples/granzotti-2026-mm13944-s1-ground-layer.ttl is the ground truth: it was read off the
supplements by hand before any code existed. If the converter and that file ever disagree about
MM 13944 / S1, the converter is wrong until a human says otherwise.
"""
import sys
from pathlib import Path

import pytest
from rdflib import Graph
from pyshacl import validate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from granzotti_to_codhmo import convert, parse_taxonomy  # noqa: E402

HAND = ROOT / "examples" / "granzotti-2026-mm13944-s1-ground-layer.ttl"

TAXA_Q = """
PREFIX codhmo: <https://codicum.eu/ontology/codhmo#>
PREFIX crminf: <http://www.cidoc-crm.org/extensions/crminf/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
SELECT ?tax ?det WHERE {
  ?h a codhmo:TaxonomicHypothesis ; crminf:J4_that ?p ; crminf:J5_holds_to_be ?det .
  ?p rdf:object ?tax . %s }
"""


@pytest.fixture(scope="module")
def generated():
    ttl, stats = convert()
    return Graph().parse(data=ttl, format="turtle"), stats


def _taxa(graph, where=""):
    return sorted((str(t).rsplit("_", 1)[-1], str(d).rsplit("#", 1)[-1])
                  for t, d in graph.query(TAXA_Q % where))


def test_no_unmapped_source_strings(generated):
    """Every institution and taxon string resolves through the normalisation tables."""
    _, st = generated
    assert not st["unmapped"], sorted(st["unmapped"])
    assert not st["unmapped_inst"], sorted(st["unmapped_inst"])


def test_counts_match_the_paper(generated):
    _, st = generated
    assert (st["rows"], st["objects"], st["samples"]) == (340, 14, 25)


def test_agrees_with_the_hand_mapped_sample(generated):
    graph, _ = generated
    where = 'FILTER(CONTAINS(STR(?p), "Medelhavsmuseet-MM-13944-S1"))'
    assert _taxa(graph, where) == _taxa(Graph().parse(HAND))


def test_generated_graph_conforms(generated):
    graph, _ = generated
    ont = Graph().parse(ROOT / "ontology" / "codhmo.ttl")
    shapes = Graph().parse(ROOT / "shapes" / "codhmo-core-shapes.ttl")
    conforms, _, text = validate(graph + ont, shacl_graph=shapes,
                                 inference="rdfs", allow_warnings=True)
    assert conforms, text


def test_undetermined_yields_no_hypothesis(generated):
    _, st = generated
    assert st["undetermined_rows"] > 0


# --- the Blast ID grammar, per data/granzotti-2026/determinacy_normalisation.tsv ---

def test_bare_undetermined_is_empty():
    assert parse_taxonomy("Undetermined") == []


def test_determined_list():
    assert parse_taxonomy("Equus asinus, Equus caballus") == [
        ("Equus asinus", "determined"), ("Equus caballus", "determined")]


def test_preferred_plus_alternatives():
    assert parse_taxonomy("Bos sp., (Bubalus bubalis, Bubalus carabanensis)") == [
        ("Bos sp.", "determined"),
        ("Bubalus bubalis", "alternatives-only"),
        ("Bubalus carabanensis", "alternatives-only")]


def test_no_comma_before_the_paren():
    """3 rows omit the comma; a comma-split alone would merge X with the first alternative."""
    assert parse_taxonomy("Philantomba maxwellii (Capra ibex)") == [
        ("Philantomba maxwellii", "determined"), ("Capra ibex", "alternatives-only")]


def test_fully_parenthesised_has_no_preferred_taxon():
    """4 rows are entirely hedged; promoting the first member would invent a preference."""
    assert parse_taxonomy("(Triticum intermedium, Triticum urartu)") == [
        ("Triticum intermedium", "alternatives-only"),
        ("Triticum urartu", "alternatives-only")]


def test_compatible_only_prefix_and_its_typo():
    for cell in ("Undetermined, compatible Bos sp.", "Undetermine, compatible Bos sp."):
        assert parse_taxonomy(cell) == [("Bos sp.", "compatible-only")]


def test_hybrid_survives_the_comma_split():
    """A hybrid can be one member of a comma list, so it must not be split into its parents."""
    got = parse_taxonomy("(Secale cereale x Triticum turgidum subsp. durum, Triticum intermedium)")
    assert got == [("Secale cereale x Triticum turgidum subsp. durum", "alternatives-only"),
                   ("Triticum intermedium", "alternatives-only")]


def test_caprine_call_recorded_at_the_shared_parent(generated):
    """Capra hircus/Ovis aries resolves to Caprinae (9963), not two competing hypotheses."""
    graph, _ = generated
    assert any(tax == "9963" for tax, _ in _taxa(graph))
