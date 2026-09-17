"""Minimal conformance tests: one valid graph, and one broken graph per MUST rule."""
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph

ROOT = Path(__file__).resolve().parents[1]
PREFIXES = """
@prefix codhmo: <https://codicum.eu/ontology/codhmo#> .
@prefix crm:    <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix crmsci: <http://www.cidoc-crm.org/extensions/crmsci/> .
@prefix crminf: <http://www.cidoc-crm.org/extensions/crminf/> .
@prefix prov:   <http://www.w3.org/ns/prov#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix ncbi:   <http://purl.obolibrary.org/obo/NCBITaxon_> .
@prefix ex:     <https://example.org/> .
"""

VALID = """
ex:ms a codhmo:HeritageObject ; crm:P1_is_identified_by ex:ms-id ; crm:P46_is_composed_of ex:layer .
ex:layer a codhmo:MaterialLayer ; crm:P45_consists_of codhmo:collagen-adhesive ;
    codhmo:hasMaterialState codhmo:Denatured .
ex:st a crmsci:S2_Sample_Taking ; crmsci:O5_removed ex:s ; crmsci:O3_sampled_from ex:layer ;
    crmsci:O4_sampled_at ex:region .
ex:s a crmsci:S13_Sample ; crm:P1_is_identified_by ex:s-id ; crmsci:O5i_was_removed_by ex:st .
ex:gen a codhmo:DatabaseGeneration ; prov:wasAssociatedWith ex:seqdb-gen ; prov:used ex:cfg .
ex:seqdb-gen a prov:SoftwareAgent ; dcterms:hasVersion "x" .
ex:cfg a codhmo:GenerationConfiguration ; codhmo:configuredMaterialState codhmo:Denatured .
ex:db a codhmo:SearchDatabase ; prov:wasGeneratedBy ex:gen .
ex:search a codhmo:DatabaseSearch ; prov:used ex:db .
ex:pep a codhmo:PeptideIdentification ; prov:wasGeneratedBy ex:search ; codhmo:compatibleWith ex:h1 .
ex:h1 a codhmo:TaxonomicHypothesis ; crminf:J4_that ex:p1 .
"""

# (name, triples to remove from VALID, triples to add)
BROKEN = [
    ("object without identifier", "ex:ms crm:P1_is_identified_by ex:ms-id .", ""),
    ("orphan material layer", "ex:ms crm:P46_is_composed_of ex:layer .", ""),
    ("sample taking without sample", "ex:st crmsci:O5_removed ex:s .", ""),
    ("sample without identifier", "ex:s crm:P1_is_identified_by ex:s-id .", ""),
    ("state outside scheme", "", "ex:layer codhmo:hasMaterialState ex:crunchy ."),
    ("species on sample", "", "ex:s codhmo:hasBiologicalSource ncbi:9986 ."),
    ("search without database", "ex:search prov:used ex:db .", ""),
    ("peptide without search", "ex:pep prov:wasGeneratedBy ex:search .", ""),
    ("evidence to non-belief", "", "ex:pep codhmo:supports ex:layer ."),
    ("hypothesis without proposition", "ex:h1 crminf:J4_that ex:p1 .", ""),
    ("generation without software", "ex:gen prov:wasAssociatedWith ex:seqdb-gen .", ""),
    ("generation without config", "ex:gen prov:used ex:cfg .", ""),
    ("unversioned software", 'ex:seqdb-gen dcterms:hasVersion "x" .', ""),
]


def _validate(data: Graph):
    """Validate data merged with the ontology, so SKOS concepts and subclass axioms are visible."""
    ont = Graph().parse(ROOT / "ontology" / "codhmo.ttl")
    shapes = Graph().parse(ROOT / "shapes" / "codhmo-core-shapes.ttl")
    conforms, _, text = validate(data + ont, shacl_graph=shapes, inference="rdfs")
    return conforms, text


def test_valid_graph_conforms():
    conforms, text = _validate(Graph().parse(data=PREFIXES + VALID, format="turtle"))
    assert conforms, text


@pytest.mark.parametrize("name,remove,add", BROKEN, ids=[b[0] for b in BROKEN])
def test_broken_graph_fails(name, remove, add):
    g = Graph().parse(data=PREFIXES + VALID, format="turtle")
    if remove:
        g -= Graph().parse(data=PREFIXES + remove, format="turtle")
    if add:
        g.parse(data=PREFIXES + add, format="turtle")
    conforms, _ = _validate(g)
    assert not conforms, f"{name} should violate a MUST rule"
