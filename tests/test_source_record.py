"""Step 7 (D23): a row in an external store resolves to observation, hypothesis, sample and object."""
from pathlib import Path

import pytest
from pyshacl import validate
from rdflib import Graph, Literal

ROOT = Path(__file__).resolve().parents[1]
FX = "https://codicum.eu/data/fixture-zooms/"
PREFIXES = """
@prefix codhmo: <https://codicum.eu/ontology/codhmo#> .
@prefix crmsci: <http://www.cidoc-crm.org/extensions/crmsci/> .
@prefix fx:     <https://codicum.eu/data/fixture-zooms/> .
"""


def _fixture():
    return Graph().parse(ROOT / "examples" / "zooms-sourcerecord-fixture.ttl")


def _validate(data: Graph):
    ont = Graph().parse(ROOT / "ontology" / "codhmo.ttl")
    shapes = Graph().parse(ROOT / "shapes" / "codhmo-core-shapes.ttl")
    conforms, _, text = validate(data + ont, shacl_graph=shapes, inference="rdfs",
                                 allow_warnings=True)
    return conforms, text


def _resolve(graph, table, keys):
    """Find the record whose keys match exactly, then walk q11 from it."""
    query = (ROOT / "queries" / "q11-source-record-to-object.rq").read_text(encoding="utf-8")
    key_filter = " ".join(
        f'?record codhmo:hasKey [ codhmo:keyName "{name}" ; codhmo:keyValue "{value}" ] .'
        for name, value in keys.items())
    query = query.replace("?record a codhmo:SourceRecord ;", key_filter + "\n  ?record a codhmo:SourceRecord ;")
    rows = graph.query(query, initBindings={"table": Literal(table)})
    return {tuple(str(v).removeprefix(FX) if v is not None else None for v in row) for row in rows}


def test_fixture_conforms():
    conforms, text = _validate(_fixture())
    assert conforms, text


def test_round_trip_resolves_one_row_to_its_object():
    rows = _resolve(_fixture(), "ZOOMS_SPECTRA", {"dataset_id": "FIXTURE-DATASET", "run": "FIXTURE-FILE-0001"})
    assert rows == {("rec", "obs", "H1", "S1", "object")}


def test_round_trip_wrong_key_resolves_nothing():
    assert _resolve(_fixture(), "ZOOMS_SPECTRA", {"dataset_id": "FIXTURE-DATASET", "run": "NO-SUCH-FILE"}) == set()


def test_round_trip_wrong_table_resolves_nothing():
    assert _resolve(_fixture(), "MS2_SPECTRA", {"dataset_id": "FIXTURE-DATASET", "run": "FIXTURE-FILE-0001"}) == set()


# (name, triples to remove from the fixture, triples to add)
BROKEN = [
    ("no schema version", 'fx:rec codhmo:storeSchemaVersion "0.1.0" .', ""),
    ("no store", 'fx:rec codhmo:inStore "ZoomzPeak" .', ""),
    ("unknown table", 'fx:rec codhmo:inTable "ZOOMS_SPECTRA" .', 'fx:rec codhmo:inTable "PEAKS" .'),
    ("two tables", "", 'fx:rec codhmo:inTable "MS2_SPECTRA" .'),
    ("missing required key", "fx:rec codhmo:hasKey fx:rec-file .", ""),
    ("MS2 row without scan number", 'fx:rec codhmo:inTable "ZOOMS_SPECTRA" .',
     'fx:rec codhmo:inTable "MS2_SPECTRA" . fx:rec codhmo:hasKey fx:k-raw . '
     'fx:k-raw codhmo:keyName "raw_filename" ; codhmo:keyValue "x.raw" .'),
    ("repeated key", "", 'fx:rec codhmo:hasKey fx:k-dup . fx:k-dup codhmo:keyName "run" ; codhmo:keyValue "OTHER" .'),
    ("key without value", 'fx:rec-file codhmo:keyValue "FIXTURE-FILE-0001" .', ""),
    ("record linked from sample", "", "fx:S1 codhmo:hasSourceRecord fx:rec ."),
    ("record link to non-record", "", "fx:obs codhmo:hasSourceRecord fx:S1 ."),
]


@pytest.mark.parametrize("name,remove,add", BROKEN, ids=[b[0] for b in BROKEN])
def test_broken_source_record_fails(name, remove, add):
    g = _fixture()
    if remove:
        g -= Graph().parse(data=PREFIXES + remove, format="turtle")
    if add:
        g.parse(data=PREFIXES + add, format="turtle")
    conforms, _ = _validate(g)
    assert not conforms, f"{name} should violate a MUST rule"
