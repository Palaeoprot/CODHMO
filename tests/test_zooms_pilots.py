"""D24-D34: the two ZooMS deposit pilots conform, and the new rules bite."""

from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[1]
ONT = Graph().parse(ROOT / "ontology" / "codhmo.ttl")
SHAPES = Graph().parse(ROOT / "shapes" / "codhmo-core-shapes.ttl")
PREFIXES = """
@prefix codhmo: <https://codicum.eu/ontology/codhmo#> .
@prefix crminf: <http://www.cidoc-crm.org/extensions/crminf/> .
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix x:      <https://example.org/> .
"""


def _conforms(data: Graph) -> tuple[bool, str]:
    ok, _, text = validate(data + ONT, shacl_graph=SHAPES, inference="rdfs", allow_warnings=True)
    return ok, text


@pytest.mark.parametrize("path", ["vinas-caron-2023/vinas-caron-2023.ttl", "peters-2025/peters-2025.ttl"])
def test_pilot_graphs_conform(path):
    ok, text = _conforms(Graph().parse(ROOT / "data" / path))
    assert ok, text


def test_pilot_records_resolve():
    q = (ROOT / "queries" / "q11-source-record-to-object.rq").read_text(encoding="utf-8")
    for path, n in [("vinas-caron-2023/vinas-caron-2023.ttl", 101), ("peters-2025/peters-2025.ttl", 9)]:
        g = Graph().parse(ROOT / "data" / path)
        assert len({r[0] for r in g.query(q)}) == n


def _proposition(obj: str, extra: str = "") -> Graph:
    return Graph().parse(data=PREFIXES + f"""
x:p a crminf:I4_Proposition_Set ; rdf:subject x:layer ;
    rdf:predicate codhmo:hasBiologicalSource ; rdf:object {obj} {extra} .""", format="turtle")


def test_gbif_taxon_with_nearest_ncbi_passes():  # D29
    ok, text = _conforms(_proposition("<https://www.gbif.org/species/4825997>",
                                      "; codhmo:nearestNcbiTaxon <http://purl.obolibrary.org/obo/NCBITaxon_38609>"))
    assert ok, text


def test_gbif_taxon_without_nearest_ncbi_fails():  # D8 still holds without D29's ancestor
    ok, _ = _conforms(_proposition("<https://www.gbif.org/species/4825997>"))
    assert not ok


def test_zooms_record_needs_run_key():  # D24
    g = Graph().parse(data=PREFIXES + """
x:rec a codhmo:SourceRecord ; codhmo:inStore "ZoomzPeak" ; codhmo:inTable "ZOOMS_SPECTRA" ;
    codhmo:storeSchemaVersion "0.1.0" ; codhmo:hasKey x:k0 , x:k1 .
x:k0 codhmo:keyName "dataset_id" ; codhmo:keyValue "D" .
x:k1 codhmo:keyName "file_id" ; codhmo:keyValue "F.mzML" .
x:obs codhmo:hasSourceRecord x:rec .""", format="turtle")
    ok, text = _conforms(g)
    assert not ok and "run" in text


def test_tentative_belief_cannot_feed_calf_rule():  # D27 + D19
    g = Graph().parse(data=PREFIXES + """
x:H-bos a codhmo:TaxonomicHypothesis ; crminf:J4_that x:p ; crminf:J5_holds_to_be codhmo:tentative .
x:p a crminf:I4_Proposition_Set ; rdf:subject x:layer ; rdf:predicate codhmo:hasBiologicalSource ;
    rdf:object <http://purl.obolibrary.org/obo/NCBITaxon_9913> .
x:inf a crminf:I5_Inference_Making ; crminf:J3_applied codhmo:rule-parchment-bos-is-calf ;
    crminf:J1_used_as_premise x:H-bos ; crminf:J2_concluded_that x:H-calf .""", format="turtle")
    ok, text = _conforms(g)
    assert not ok and "tentative" in text
