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
@prefix rdf:    <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix xsd:    <http://www.w3.org/2001/XMLSchema#> .
"""

VALID = """
ex:ms a codhmo:HeritageObject ; crm:P1_is_identified_by ex:ms-id ; crm:P46_is_composed_of ex:layer .
ex:layer a codhmo:MaterialLayer ; crm:P45_consists_of codhmo:collagen-adhesive ;
    codhmo:hasMaterialState codhmo:Denatured .
ex:st a crmsci:S2_Sample_Taking ; crmsci:O5_removed ex:s ; crmsci:O3_sampled_from ex:layer ;
    crmsci:O4_sampled_at ex:region ; crm:P14_carried_out_by ex:person ; crm:P4_has_time-span ex:ts .
ex:person a crm:E21_Person .
ex:ts a crm:E52_Time-Span ; crm:P82a_begin_of_the_begin "2026-01-01T00:00:00"^^xsd:dateTime ;
    crm:P82b_end_of_the_end "2026-01-01T23:59:59"^^xsd:dateTime .
ex:p1 a crminf:I4_Proposition_Set ; rdf:predicate codhmo:hasBiologicalSource ;
    rdf:object <http://purl.obolibrary.org/obo/NCBITaxon_9986> .
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
    ("sampling without actor", "ex:st crm:P14_carried_out_by ex:person .", ""),
    ("sampling without date", "ex:st crm:P4_has_time-span ex:ts .", ""),
    ("sample without identifier", "ex:s crm:P1_is_identified_by ex:s-id .", ""),
    ("state outside scheme", "", "ex:layer codhmo:hasMaterialState ex:crunchy ."),
    ("species on sample", "", "ex:s codhmo:hasBiologicalSource ncbi:9986 ."),
    ("search without database", "ex:search prov:used ex:db .", ""),
    ("peptide without search", "ex:pep prov:wasGeneratedBy ex:search .", ""),
    ("evidence to non-belief", "", "ex:pep codhmo:supports ex:layer ."),
    ("hypothesis without proposition", "ex:h1 crminf:J4_that ex:p1 .", ""),
    ("generation without software", "ex:gen prov:wasAssociatedWith ex:seqdb-gen .", ""),
    ("generation without config", "ex:gen prov:used ex:cfg .", ""),
    ("asserted component role", "", "ex:layer codhmo:hasComponentRole codhmo:role-binder ."),
    ("asserted component", "", "ex:layer codhmo:hasComponentMaterial ex:layer ."),
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


@pytest.mark.xfail(reason="IN-A001 sampler (crm:P14) and date (crm:P4) not yet supplied", strict=True)
def test_pepys_instance_has_no_violations():
    ont = Graph().parse(ROOT / "ontology" / "codhmo.ttl")
    shapes = Graph().parse(ROOT / "shapes" / "codhmo-core-shapes.ttl")
    data = Graph().parse(ROOT / "examples" / "pepys-IN-A001.ttl")
    conforms, _, text = validate(data + ont, shacl_graph=shapes, inference="rdfs", allow_warnings=True)
    assert conforms, text


def test_pepys_taxa_only_inside_propositions():
    """Rule 2 / §34: the graph never asserts a biological source as fact."""
    from rdflib import URIRef
    data = Graph().parse(ROOT / "examples" / "pepys-IN-A001.ttl")
    assert not list(data.triples((None, URIRef("https://codicum.eu/ontology/codhmo#hasBiologicalSource"), None)))


@pytest.mark.parametrize("bad", ['"Oryctolagus cuniculus"', "<https://www.gbif.org/species/2436691>",
                                 "<http://purl.obolibrary.org/obo/NCBITaxon_rabbit>"])
def test_taxon_must_be_numeric_ncbi_iri(bad):
    g = Graph().parse(data=PREFIXES + VALID + f"""
        ex:p1 a crminf:I4_Proposition_Set ; rdf:predicate codhmo:hasBiologicalSource ; rdf:object {bad} .""",
        format="turtle")
    conforms, _ = _validate(g)
    assert not conforms


@pytest.mark.parametrize("name", ["kasso-2025-pakepu-white-paste", "sargent-2025-aein656-gold-leaf-adhesive",
                                  "charter-illustrative", "fiddyment-2021-birth-girdle",
                                  "palandri-2024-missale-nidrosiense", "brandt-2023-scythian-leather"])
def test_step6_examples_have_no_violations(name):
    ont = Graph().parse(ROOT / "ontology" / "codhmo.ttl")
    shapes = Graph().parse(ROOT / "shapes" / "codhmo-core-shapes.ttl")
    data = Graph().parse(ROOT / "examples" / f"{name}.ttl")
    conforms, _, text = validate(data + ont, shacl_graph=shapes, inference="rdfs", allow_warnings=True)
    assert conforms, text


def _scythian():
    return Graph().parse(ROOT / "examples" / "brandt-2023-scythian-leather.ttl")


def test_human_derived_flag_present_passes():
    ont = Graph().parse(ROOT / "ontology" / "codhmo.ttl")
    shapes = Graph().parse(ROOT / "shapes" / "codhmo-core-shapes.ttl")
    conforms, _, text = validate(_scythian() + ont, shacl_graph=shapes, inference="rdfs", allow_warnings=True)
    assert conforms, text


@pytest.mark.parametrize("node", ["quiver7-leather", "T7-human"])
def test_human_derived_flag_missing_fails(node):
    from rdflib import URIRef
    g = _scythian()
    g.remove((URIRef("https://codicum.eu/data/brandt-2023/" + node),
              URIRef("https://codicum.eu/ontology/codhmo#hasSensitivity"), None))
    conforms, _ = _validate(g)
    assert not conforms


@pytest.mark.parametrize("taxon", ["9605", "63221"])  # genus Homo; H. sapiens neanderthalensis
def test_archaic_or_genus_homo_does_not_require_flag(taxon):
    g = Graph().parse(data=PREFIXES + VALID + f"""
        ex:pep codhmo:compatibleWith ex:hx .
        ex:hx a codhmo:TaxonomicHypothesis ; crminf:J4_that ex:px .
        ex:px a crminf:I4_Proposition_Set ; rdf:subject ex:layer ;
            rdf:predicate codhmo:hasBiologicalSource ;
            rdf:object <http://purl.obolibrary.org/obo/NCBITaxon_{taxon}> .""", format="turtle")
    conforms, text = _validate(g)
    assert conforms, text
