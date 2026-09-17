"""Check every NCBI taxid IRI in one or more RDF files against the live NCBI Taxonomy.

Numeric taxids survive renames, but NCBI occasionally merges nodes (merged.dmp) or
deletes them (delnodes.dmp). This reports any taxid that is no longer active, with the
replacement taxid for merges, and exits non-zero so it can gate CI.

    python tools/check_ncbi_taxa.py examples/*.ttl
"""
from __future__ import annotations

import json
import re
import sys
import urllib.request
from pathlib import Path

from rdflib import Graph, URIRef

TAXON_IRI = re.compile(r"^http://purl\.obolibrary\.org/obo/NCBITaxon_(\d+)$")
ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=taxonomy&retmode=json&id="
BATCH = 200


def taxids_in(paths: list[Path]) -> set[str]:
    ids = set()
    for path in paths:
        for term in Graph().parse(path).all_nodes():
            if isinstance(term, URIRef) and (m := TAXON_IRI.match(str(term))):
                ids.add(m.group(1))
    return ids


def fetch_summaries(ids: list[str]) -> dict:
    result = {}
    for i in range(0, len(ids), BATCH):
        with urllib.request.urlopen(ESUMMARY + ",".join(ids[i:i + BATCH]), timeout=60) as r:
            result.update(json.load(r)["result"])
    return result


def classify(taxid: str, summaries: dict) -> tuple[str, str]:
    """Return (status, detail): status is active, merged, deleted or unknown."""
    rec = summaries.get(taxid)
    if rec is None or "error" in rec:
        return "deleted", "not found in NCBI Taxonomy"
    status = rec.get("status", "")
    if status == "active":
        return "active", rec.get("scientificname", "")
    if status == "merged":
        return "merged", f"merged into NCBITaxon_{rec.get('akataxid')}"
    return "unknown", f"NCBI status {status!r}"


def main(argv: list[str]) -> int:
    ids = sorted(taxids_in([Path(a) for a in argv]), key=int)
    if not ids:
        print("no NCBI taxids found")
        return 0
    summaries = fetch_summaries(ids)
    stale = 0
    for taxid in ids:
        status, detail = classify(taxid, summaries)
        stale += status != "active"
        print(f"{'OK   ' if status == 'active' else 'STALE'} NCBITaxon_{taxid}: {status} - {detail}")
    return 1 if stale else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
