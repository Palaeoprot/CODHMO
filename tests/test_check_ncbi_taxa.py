"""Offline tests for the NCBI stale-taxid classifier."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_ncbi_taxa import classify  # noqa: E402

SUMMARIES = {
    "9986": {"status": "active", "scientificname": "Oryctolagus cuniculus"},
    "111": {"status": "merged", "akataxid": "222"},
    "333": {"error": "cannot get document summary"},
}


def test_active():
    assert classify("9986", SUMMARIES)[0] == "active"


def test_merged_reports_replacement():
    assert classify("111", SUMMARIES) == ("merged", "merged into NCBITaxon_222")


def test_deleted_or_missing():
    assert classify("333", SUMMARIES)[0] == "deleted"
    assert classify("444", SUMMARIES)[0] == "deleted"
