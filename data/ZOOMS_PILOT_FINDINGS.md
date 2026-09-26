# ZooMS deposit pilot — CODHMO / ZoomzPeak findings

> 2026-09-26

Two ZooMS deposits, chosen to differ; the parquet_master ZooMS store is treated as ZoomzPeak.

| Pilot | Deposit | Converter | Output |
|---|---|---|---|
| A | Viñas-Caron et al. 2023, AM 795 4to palimpsest, Zenodo 6967158 | `tools/zooms_deposit_to_codhmo.py` | `vinas-caron-2023/` |
| B | Peters et al. 2025, extinct Australian megafauna reference spectra, Zenodo 14418148 (doi:10.3389/fmamm.2025.1564287) | `tools/peters_2025_to_codhmo.py` | `peters-2025/` |

Findings F1–F10 and Z1–Z4 come from pilot A; F11–F13 and Z5–Z7 from pilot B.

Proposed responses: D24–D34 in `docs/design-decisions.md`.

## Result (pilot A)

| Check | Outcome |
|---|---|
| Samples (Dataset S1) | 54 |
| Spectrum observations → ZoomzPeak `SourceRecord` | 101 (34 samples) |
| Samples with no deposited spectrum → `DocumentLocator` fallback | 20 (UoC35–UoC54) |
| Taxonomic hypotheses | 60 (2 manual/automated conflicts) |
| SHACL (data + ontology, rdfs, warnings allowed) | **conforms** |
| q11 source row → object | 101/101 records resolve to AM 795 4to |
| q06 competing hypotheses | 8 rows (UoC29, UoC32) |

The graph conforms, but only because several things the paper says could not be said. Those are the findings.

## Result (pilot B)

| Check | Outcome |
|---|---|
| Specimens | 3 (MBS01 *Zygomaturus trilobus*, SCP02 *Palorchestes azael*, MCP02 *Protemnodon mamkurra*) |
| Spectrum observations → ZoomzPeak `SourceRecord` | 9 (3 replicates each) |
| SHACL | conforms (3 warnings: sampling location not reported) |
| q11 | 9/9 resolve |
| Taxa recordable in NCBI | 0 of 3 at species; 1 at genus (*Protemnodon* 2493641); 2 only at order (Diprotodontia 38609) |

## Findings

### CODHMO

- **F1: No mixture determinacy.** *(Revised 2026-09-26: D15 already covers mixtures via `compatibleWith`; the converter misapplied `compatible-only`. Remaining gap = the doubtful member, see D27.)* The manual call for UoC29/UoC32 is `Sheep+Goat+Calf?`: several skins or contamination on one leaf. `DeterminacyScheme` has determined / indistinguishable / alternatives-only / compatible-only; all assume ONE true source. The converter had to use `compatible-only`, which is wrong. The `?` on one member (Calf) is also inexpressible. → Add `codhmo:mixture` (all members present), and a per-member confidence.
- **F2: No method on an inference.** The paper gives a manual AND an automated call per sample. CODHMO can't say which method made which hypothesis; the pilot encodes it in IRIs and labels. → Allow `crm:P33_used_specific_technique` (or `codhmo:usedMethod`) on `crminf:I5_Inference_Making`, with a scheme (manual marker reading, SpecieScan, PAMPA, …).
- **F3: Paper-as-premise vs J1 range.** The logged decision says a paper-asserted proposition is an I5 with the paper as premise. But `J1_used_as_premise` ranges over I2 Belief, so the pilot uses the observations as premises and puts the paper on `dcterms:source`. → State the pattern in design-decisions.md, with an example.
- **F4: Colloquial taxon names, no rank guard.** "Sheep"/"Goat" were mapped to *Ovis aries* 9940 / *Capra hircus* 9925 by a hard-coded dict. ZooMS markers rarely separate a domestic species from its wild congeners. → Use a `taxon_normalisation.tsv` as Granzotti does, and decide whether ZooMS "Sheep" should be recorded at *Ovis* (9935) with `indistinguishable`.
- **F5: The calf rule (D19) can't fire.** "Calf?" appears inside a mixture call. The Bos→calf rule needs a Bos hypothesis to be a premise; a member of an uncertain mixture isn't one. Bos 9913 was emitted with no calf inference. Depends on F1.
- **F6: Derived measurements have no home.** Dataset S1 has PQI, SE, confidence score and proteomic cluster: numbers computed from spectra that are neither raw data (ZoomzPeak) nor hypotheses. PQI is a deamidation index, arguably a material-state observation. All were dropped. → Decide whether these become `S4_Single_Observation` values with a `SourceRecord`/`DocumentLocator`, or a ZoomzPeak derived table.
- **F7: Codicological observations dropped.** Visual cluster, ink remains, text orientation, line spacing, thickness, hair-follicle pattern, glass-like layer. CODHMO has no home for non-proteomic observations of a leaf.
- **F8: Palimpsest provenance can't be expressed.** The paper's main claim is that the leaves come from ≥4 earlier manuscripts (groups A–D) reused in AM 795 4to. CODHMO has no "support re-used from an earlier object" relation or production event, so the headline result isn't in the graph.
- **F9: Leaf vs sample.** Folio 89 was sampled twice (UoC21, UoC53), and the paper samples *bifolios*. The converter makes one `MaterialLayer` per sample, which duplicates the leaf. → A leaf/bifolio identity key is needed (one layer, several samplings). Recto/verso lives only in `uoc_metadata`.
- **F10: Validation recipe.** Shapes pass only when the ontology is MERGED into the data graph (`validate(data + ont, …)`). Passing it as `ont_graph` gives 54 false P45 violations and 4 false J5 warnings. → Document this, or make the shapes self-contained.

- **F11: A reference specimen's taxon is a premise, not a hypothesis.** In pilot B the species identity (morphology/curation) is the INPUT and the spectra are taken to derive markers. CODHMO can only express taxa as `TaxonomicHypothesis`, so a premise is recorded as if the ZooMS spectra concluded it — the evidential arrow points the wrong way. → Model a reference/voucher identification (e.g. `crm:E17_Type_Assignment` by the curator, cited as premise) and a marker-derivation activity whose output is a marker set, not a taxon.
- **F12: No bone, dentine, gelatin or collagen-extract materials.** The E57 list is manuscript/adhesive-oriented; pilot B had to declare `bone` and `ultrafiltered gelatin` locally. Also no way to say MBS01's sample is a *re-used* extract (gelatin made for radiocarbon) — a sample of a sample.
- **F13: NCBI-only taxa fail for extinct species.** The MUST rule (numeric NCBITaxon IRI) forces *Zygomaturus trilobus* and *Palorchestes azael* up to the ORDER Diprotodontia — the family and genus don't exist in NCBI. This loses exactly the information ZooMS of extinct fauna exists to produce. → Allow a second authority for taxa absent from NCBI (e.g. GBIF / Catalogue of Life / Paleobiology Database IRIs), with NCBI preferred when present, and keep the source name on the proposition.

### ZoomzPeak (store)

- **Z1: `file_id` is a filename.** `UoC01_1.mzML` is unique only within the dataset, and the extension is part of the key. D23's `spectrum_id` is still needed.
- **Z2: Sample and replicate are conflated.** `sample_id` = `UoC01_1` is the replicate. The deposit's sample is `UoC01` (3 replicates). The converter splits on the last `_`, which is fragile. → Add `sample_id` + `replicate` columns.
- **Z3: Instrument not recorded.** `instrument` is null and `instrument_status` is `not_reported`, but the paper states a Bruker Ultraflex III (York). Paper-derived instrument metadata needs a path in.
- **Z4: Incomplete deposit is invisible.** 162 replicate spectra were acquired (54 × 3); 101 were deposited: UoC35–54 have none and UoC34 has 2 of 3. Neither store records "measured but not deposited", as distinct from "not measured".

- **Z5: `sample_id` holds the spectrum native id in pilot B.** e.g. `SCP02_Palorchestes-azael_1_P_azael.G6` — that is the mzML spectrum id / MALDI spot (`G6`), not a sample. The same column holds a replicate label in pilot A. One column, three meanings.
- **Z6: File naming is inconsistent inside one deposit.** `MCP02_Protemnodon…_1` vs `MCP02-Protemnodon…_2`; parsing the sample code needed a two-separator split.
- **Z7: `dataset_id` is misattributed.** The store calls this deposit `Douka_2024_Australian_Megafauna`; it is Peters & Oertle 2025. The key is part of every `SourceRecord`, so renaming it breaks links — ZoomzPeak needs a stable opaque dataset key with the human label as metadata.

## mzPeak parity (HUPO-PSI)

ZoomzPeak should be an mzPeak profile, so CODHMO `SourceRecord` keys should name mzPeak concepts, not store columns. Source: mzPeak specification (hupo-psi.github.io/mzPeak-specification), read 2026-09-26.

| mzPeak concept | mzPeak location | ZoomzPeak today | Decision (2026-09-26) |
|---|---|---|---|
| Run | one `.mzpeak` per run; `file_description.source_files[]` | `file_id` (filename incl. `.mzML`), `raw_path` | Key on `run` = file stem (D24) |
| Spectrum index | `spectrum_index` entity column | none | Not needed: one spectrum per MALDI run |
| Spectrum native ID | `spectra_metadata.parquet` `id` | overloaded into `sample_id` (Z5) | Follow mzPeak: separate `id` column |
| Sample | run-level `samples[]` {id, name, parameters} | `sample_id` = replicate or native ID | Follow mzPeak: sample list, replicate as a parameter (Z2) |
| Source-file checksum | `source_files[].checksum` | none | Recorded only when the deposit provides one; never a key |
| Profile vs centroid | profile to `spectra_data`, centroid to `spectra_peaks` | profile only | Not yet relevant; after peak picking, add expected m/z and centroid delta columns |
| Instrument | `instrument_configurations[]` (MS:1000031) | null (Z3) | Populate from the paper when files lack it |
| USI | `mzspec:<PXD>:<run>:<index>` | not possible: no PXD | None for historical data (cite by deposit DOI); a ZooMS identifier is a goal of the ZoomzPeak proposal (D25) |

CIDOC-CRM side: both pilots validate against CRM/CRMsci/CRMinf, but F8 (reuse of a support), F11 (voucher identification = `E17_Type_Assignment`) and F12 (sample of a sample) are all expressible in CRM/CRMsci already — CODHMO just hasn't adopted those classes.

## Not yet done

- Taxids checked live against NCBI E-utilities for pilot B; pilot A's 9940/9925/9913 are standard.
- No pytest files yet for either pilot, pending decisions on F1/F2/F11/F13.
- The two converters share ~40% of their code; merge into one deposit-adapter tool once the key scheme is settled.
