# CODHMO design decisions

_Last updated: 2026-09-26 (D24–D34 accepted)_

Working notes for the final documentation. Each entry records what was decided, the alternatives, and why. Source handover: *CODICUM Heritage Materials & AI Agent* (17 Sept 2026).

## Guiding principle: meaning in the data, not in the storage

CODHMO is built for AI agents that will read the graph, often in fragments: a JSON-LD export, a query result, a few lines of Turtle pasted into a prompt. An agent that fetches and joins data is no longer the hard part. The risk is an agent **misreading** it, for example taking a hypothesis for a fact or a database candidate for an identification.

That makes explicit ontological meaning more valuable than linked-open-data connectivity alone. The rule we follow:

> **Every distinction the agent must respect is carried by the data itself (classes, definitions, relations), never by storage conventions, file layout or out-of-band knowledge.**

Linked open data still matters for **identity**. Stable, resolvable external IDs such as NCBI taxids and Getty AAT let an agent check what a term refers to. The combination we want is a strong ontology for meaning plus stable external IDs for identity.

The decisions below apply this principle.

## Decisions

### D1. Separate repository
CODHMO lives in `Palaeoprot/CODHMO`, not inside ZoomzPeak. The ontology is the semantic bridge. ZoomzPeak (peaks) and the search-database serialisation reference it but do not become it (handover §25, §34).

### D2. Standards and versions
The ontology targets **CIDOC CRM 7.1.3** (the ISO-correspondence version, not the 7.4 draft), **CRMsci 3.2** and **CRMinf 1.2.1**, the extension releases compatible with 7.1.3.
- The CRMsci and CRMinf IRIs were checked against the published RDFS files on 2026-09-17:
  - `http://www.cidoc-crm.org/extensions/crmsci/`
  - `http://www.cidoc-crm.org/extensions/crminf/`
- Corrections found during that check:
  - The observation class is `S4_Single_Observation`.
  - CRMinf 1.2.1 has no I6 Belief Value class, so confidence is the value of `J5_holds_to_be`.

### D3. Reuse before inventing
Every handover term was mapped in `alignment/codhmo-matrix.csv`.
- **Properties:** 14 of the 27 were dropped because CRM, CRMsci, CRMinf or PROV-O already covers them, 4 reuse CRM directly, and 9 are genuinely new.
- **Codicological kinds:** manuscript, charter, leaf and binding are CRM types owned by CODICUM, not CODHMO classes.

### D4. CRMinf for hypotheses
Material hypotheses and historical interpretations are subclasses of `crminf:I2_Belief`. They carry a proposition (`J4_that`) and a confidence (`J5_holds_to_be`). This reuses an existing argumentation model instead of defining a parallel one. HistoricalInterpretation is declared disjoint from MaterialHypothesis, so a material identification can never itself be a historical conclusion.

### D5. Material layers are CRMsci S10, attached by P46
A layer (adhesive, ink, sizing) is a `crmsci:S10_Material_Substantial` that is part of its object via `crm:P46_is_composed_of`. P56 "bears feature" was the alternative, but a layer is removable matter, not just a surface feature.

### D6. Materials as a SKOS vocabulary, not an OWL class tree
Material kinds (rabbit-skin glue, isinglass, starch paste, and so on) are `skos:Concept`s also typed `crm:E57_Material`, linked to Getty AAT by `skos:exactMatch` or `closeMatch`. This follows Linked Art practice.
- **Why not OWL:** material "kinds" are thesaurus relations, not logical subsets. Isinglass is both a fish product and an adhesive, and OWL subclassing would force unwanted inferences.
- **Where OWL is kept:** for things that SHACL must check structurally, such as Sample, MaterialLayer and the hypothesis classes.

### D7. Propositions are reified, not named graphs
H1's claim "the layer derives from NCBITaxon_9986" is stored as a `crminf:I4_Proposition_Set` with `rdf:subject`, `rdf:predicate` and `rdf:object`. The triple is never asserted.
- **Alternative:** named graphs. They read more naturally and can hold several triples per proposition, but the hypothetical status then lives only in the **container**. A merged store, a flat export or an agent's context window silently turns the claim into fact.
- **Why reification:** the status is part of the data wherever it travels, which is the guiding principle above. It also works in plain Turtle, JSON-LD and SHACL.
- **Tested:** query Q5 ("asserted biological sources") must return nothing, and a test fails if a bare `hasBiologicalSource` triple appears.
- **Revisit** if multi-triple propositions become common, such as full adhesive recipes.

### D8. Taxa are numeric NCBI taxid IRIs only
Biological sources use `http://purl.obolibrary.org/obo/NCBITaxon_<digits>`.
- **Why numeric IDs:** genus and species names are revised, but the numeric node and its higher-rank ancestors stay stable. Names are labels, never keys.
- **Rank:** state the rank the evidence supports and never promote a family taxid to a genus or species (handover Rule 3).
- **Enforcement:** SHACL rejects names, GBIF URLs and non-numeric IRIs.
- **Stale IDs:** `tools/check_ncbi_taxa.py` flags taxids that NCBI has merged (giving the replacement) or deleted.

### D9. Material state vs configured state
`codhmo:hasMaterialState` says the sample is denatured. `codhmo:configuredMaterialState` says the database was built to model denatured collagen. These are different claims about different things (handover §7).

### D10. Evidence relations are defeasible, and enforced by SHACL rather than RDFS
`supports`, `contradicts` and `compatibleWith` share the abstract parent `evidentialRelation`, whose definition says they imply no logical proof.
- **Removed range axiom:** they originally had `rdfs:range crminf:I2_Belief`. Under RDFS inference, evidence pointing at an adhesive layer silently made the layer a belief, so validation could never catch the error. The range was removed and SHACL enforces it instead.
- **General rule:** use RDFS domain and range only where the inference is actually wanted, and SHACL constraints everywhere else. The remaining domains and ranges still need this review.

### D11. Provenance via PROV-O
Database generation and search are `prov:Activity` subclasses, and databases, configurations and peptide results are `prov:Entity`. The generator (`seqdb-gen`, Rust) is a `prov:SoftwareAgent` that must carry a version.

### D12. Sampling must record who and when
Every `crmsci:S2_Sample_Taking` must have `crm:P14_carried_out_by` (a person, group or actor) and one `crm:P4_has_time-span` with `P82a` and `P82b` as `xsd:dateTime`, equal for a known instant.

### D13. Conformance = SHACL, questions = SPARQL tests
- **SHACL:** the handover's §26 minimum profile is `shapes/codhmo-core-shapes.ttl`. A MUST rule is a Violation and a SHOULD rule is a Warning.
- **SPARQL:** the agent questions Q1–Q10 are `queries/*.rq`. Their expected answers against the Pepys graph are pinned in `tests/test_queries.py`, so the graph provably answers them without reading prose.

### D14. Formulations: components with roles (Step 6)
A mixed material is a layer with several constituent `S10` bodies (`codhmo:hasComponentMaterial`). Each constituent carries a `codhmo:hasComponentRole` from a SKOS scheme: bulk, binder, additive or contaminant. The composition is itself a hypothesis, so each component link is a reified proposition. One belief may hold several propositions, one per component.
- **Test case:** Kasso et al. white paste CA220349, which is calcite bulk plus a collagen binder.
- **Evidence:** FTIR and SEM observations (`crmsci:S4_Single_Observation`). The binder's taxon is left unresolved because the source's proteomics was still underway.

### D15. Candidate taxa are not automatically competing
`hasCompetingHypothesis` means the alternatives exclude each other. A database report that lists several taxa for one glue does **not** imply that. The adhesive may be a mixture, as with Sargent et al. 2025 ÆIN 656, where mammalian taxa and a "large amount of fish peptides" were reported together.
- **Rule:** such candidates each get their own TaxonomicHypothesis linked by `compatibleWith`. Mark two of them competing only when there is a reason to think they exclude each other.
- **Rank:** each candidate keeps the rank the source supports. Equus stays a genus (9789), and "Bos mutus/taurus" is held at Bovidae (9895) because the species is not resolved.

### D16. Literature-derived records: sampler = author team, date = upper bound only (amends D12)
Published studies often don't report who sampled or when.
- **Actor:** the author team (`crm:E74_Group`, with `dcterms:source` giving the DOI).
- **Date:** a time-span with only `crm:P82b_end_of_the_end`. It currently uses the date the paper was captured, which is a true "on or before" bound. The rule now requires at least one bound rather than both.
- **Why:** this records only what is known, instead of inventing a date.

### D17. A heritage object needs no sample
The charter C1 case shows a charter with only an identifier and type is a valid CODHMO record. Scientific examination attaches later without restructuring the record (handover §33, Priority 6).

### D18. Component roles and composition are propositions, never assertions
The same markers can be read three ways: as a contaminant (sheep markers on a spine, put down to glue, in Palandri et al. 2024), as part of the formulation, or as evidence of use (residues on the MS. 632 birth girdle). A role is therefore an interpretation.
- **Rule:** `hasComponentRole` and `hasComponentMaterial` appear only inside reified propositions. SHACL rejects them as direct assertions.
- **Hypothesised components:** these nodes can still carry a description (`crm:P45`), but they are linked to a layer or a role only through propositions.

### D19. Domain inference rules are explicit CRMinf objects: bovine parchment = calf
ZooMS resolves a taxon, not the animal's age. The parchment-only rule `codhmo:rule-parchment-bos-is-calf` (a `crminf:I3_Inference_Logic`) states that bovine parchment must be calfskin, because workable parchment cannot be made from cattle older than about 8 weeks.
- **How it is recorded:** a `crminf:I5_Inference_Making` applies the rule (`J3`), takes the Bos taxonomic belief as its premise (`J1`) and concludes the calfskin belief (`J2`).
- **Why:** the calf claim can be traced to the rule, and an agent can see that it was derived, not observed.
- **Scope:** the rule does not apply to Bos leather or glue. It was supplied by M. Collins on 2026-09-17.
- **No "calf" taxon:** the taxon stays Bos (9903).

### D20. Competing vs co-occurring candidates, and recorded failures
- **Competing:** alternatives that exclude each other must be marked with `hasCompetingHypothesis`. For example, one leather sample whose markers are shared by Panthera, Mustelidae and Hyaenidae (Brandt et al. 2023, sample 34) can only come from one of them. This contrasts with a possible mixed glue (D15).
- **Failed identifications:** these are recorded as observations, for example "12 of 45 samples unidentified", not omitted.

### D21. Sensitivity flag for human-derived material
Human-derived material is flagged with `codhmo:hasSensitivity codhmo:sensitivity-human-derived` (SKOS `SensitivityScheme`).
- **A handling statement, not a scientific claim:** it is asserted directly, unlike taxa. It applies as soon as a human source is even *hypothesised*, because the ethical obligation doesn't wait for certainty.
- **Enforced:** SHACL requires the flag on both the material and the belief whenever a biological-source proposition points to *Homo sapiens* (9606). Neanderthals, Denisovans and genus-level *Homo* (9605) deliberately do not trigger it (decided 2026-09-17). The Scythian quiver object is also flagged.
- **Not triggered by contamination:** incidental modern human proteins (keratins, handling) are recorded as a contaminant role, not a biological source.
- **Extensible:** the same scheme can later hold other flags, such as sacred objects or restricted collections.

### D22. No rdfs:domain or rdfs:range on CODHMO properties
Every CODHMO property's domain and range was removed. Under RDFS inference they don't check anything; they retype whatever the property is misused on.
- **Examples:** `hasCompetingHypothesis` on a peptide would have made the peptide a belief, and `configuredMaterialState` on a sample would have made the sample a database configuration.
- **Replacement:** intended subjects and objects are stated in each definition and enforced by SHACL, with broken-graph tests.
- **Only wanted inference kept:** `owl:SymmetricProperty` on `hasCompetingHypothesis`.
- **Why the proposition-only properties were stripped too:** the domains on `hasBiologicalSource`, `hasComponentMaterial` and `hasComponentRole` never fired, but they looked like constraints.

### D23. Source records link results to rows in external stores
Bulk data (peak lists, spectra) stays in its store; the graph holds a `codhmo:SourceRecord` that locates one row. An observation (`crmsci:S4_Single_Observation`) or peptide identification points at it with `codhmo:hasSourceRecord`.
- **Locator:** store name (`inStore`), table (`inTable`: `ZOOMS_SPECTRA`, `MS2_SPECTRA` or `MS1_ENVELOPE`), the store's schema version, and key column/value pairs (`hasKey` → `keyName`, `keyValue`).
- **Natural keys for now:** ZooMS rows by `dataset_id` + `file_id`; MS2 rows by `dataset_id` + `raw_filename` + `scan_number`; MS1 envelopes by `pxd_accession` + `file_id` + `ms2_title`. SHACL requires each table's keys, exactly once. When ZoomzPeak ships a stable `spectrum_id`, only the key nodes change.
- **Known weaknesses (accepted 2026-09-17):** keys break if a file is renamed or a dataset re-ingested; the store does not yet guarantee key uniqueness; `ms2_title` format depends on the converter. The recorded schema version is what makes a later migration possible.
- **Round trip:** `queries/q11` walks record → observation → hypothesis → sample → object. It is tested on a synthetic fixture (`examples/zooms-sourcerecord-fixture.ttl`) because no ZooMS analysis has been run yet.

## Decisions from the ZooMS deposit pilots (accepted 2026-09-26)

These come from converting two public ZooMS deposits end to end (`data/ZOOMS_PILOT_FINDINGS.md`): Viñas-Caron et al. 2023, the AM 795 4to palimpsest (pilot A), and Peters et al. 2025, extinct Australian megafauna reference spectra (pilot B). All were accepted on 2026-09-26 and applied in ontology 0.2-draft; F* and Z* refer to the findings file. **Not yet applied:** D31 (reuse event; the pilot A converter does not yet emit groups A–D), D33 (needs the ZoomzPeak derived table), D25's DOI on pilot records is emitted but not required by SHACL. Direction set on 2026-09-26: ZoomzPeak is to be an mzPeak (HUPO-PSI) profile, and CODHMO stays aligned with CIDOC CRM.

### D24. Source-record keys follow mzPeak, not store columns (amends D23) — *Accepted 2026-09-26*
`ZOOMS_SPECTRA` keys are named after mzPeak concepts, so a locator stays valid when ZoomzPeak becomes an mzPeak profile.
- **Required keys:** `dataset_id` and `run` (the mzPeak run: the source file stem, without extension).
- **No spectrum index:** a ZooMS MALDI run holds one spectrum, so ZoomzPeak has no `spectrum_index` and none is required (decided 2026-09-26). If a multi-spectrum ZooMS format ever appears, the index is added as a key then.
- **Optional key:** `id`, the spectrum's native ID in mzPeak's `spectra_metadata.id` sense (e.g. the MALDI spot in `…P_azael.G6`).
- **Sample vs spectrum ID (decided 2026-09-26, follow mzPeak):** ZoomzPeak splits today's `sample_id` into the spectrum `id` and a run-level sample list (mzPeak `samples[]`: `id`, `name`, parameters such as replicate). Today the one column holds a replicate label in pilot A and a native ID in pilot B (Z2, Z5).
- **Why:** both pilots had to key on `file_id`, a filename that includes `.mzML` and is unique only inside its dataset (Z1).
- **Dataset key:** `dataset_id` must be an opaque, stable key, with the human label (author/year/topic) as metadata. The store currently files Peters et al. 2025 as `Douka_2024_Australian_Megafauna`, and renaming it would break every locator (Z7).
- **Checksums:** mzPeak lists each source file with a checksum. Most public ZooMS deposits don't provide one, so ZoomzPeak records a checksum only when the deposit does (e.g. PRIDE, some Zenodo records); it is never a key.
- **Migration:** the recorded `storeSchemaVersion` tells a migration which locators use the old `file_id` form. Until ZoomzPeak writes `run`, converters emit `file_id` as well, so D23's SHACL keeps passing.
- **Later (peak picking):** ZoomzPeak currently stores profile spectra only, so mzPeak's profile/centroid split doesn't apply yet. Once spectra are peak-picked, centroid rows gain columns for the expected m/z and the delta of the centroid from it; that is a separate decision.

### D25. Spectra outside ProteomeXchange need a citable locator — *Accepted 2026-09-26*
mzPeak and PSI use the Universal Spectrum Identifier (`mzspec:<PXD>:<run>:<index>`), which needs a ProteomeXchange accession. Most ZooMS spectra are on Zenodo, Mendeley Data, Figshare or ADS and have none.
- **Historical data:** these spectra will never have a USI. A `SourceRecord` carries `dcterms:source` = the deposit DOI (e.g. `10.5281/zenodo.6967158`), so a spectrum can still be cited from the graph without the store.
- **Future:** a spectrum identifier for ZooMS is one of the aims of proposing ZoomzPeak as a standard. When it exists, it becomes an optional `SourceRecord` key alongside the DOI; the DOI is kept for historical records.

### D26. The method is stated on the inference — *Accepted 2026-09-26*
A `crminf:I5_Inference_Making` that concludes a taxonomic belief records its technique with `crm:P33_used_specific_technique`, pointing to a concept in a new `codhmo:IdentificationMethodScheme` (manual marker reading, SpecieScan, PAMPA, database search, …).
- **Why:** pilot A reports a manual and an automated call per sample, and they disagree for UoC29 and UoC32. Without a method, the two beliefs can only be told apart by IRI (F2).
- **Paper as source:** the publication goes on the I5 as `dcterms:source`. `J1_used_as_premise` stays for beliefs and observations (F3), which settles the earlier "paper as premise" wording.

### D27. Mixtures use D15; a doubtful member gets its own determinacy — *Accepted 2026-09-26*
Pilot A's manual call `Sheep+Goat+Calf?` is a mixture: several skins or contamination on one leaf. D15 already covers this: one `TaxonomicHypothesis` per member, linked by `compatibleWith` and not competing.
- **Correction:** the pilot A converter wrongly tagged the members `compatible-only`. It will follow D15 (F1).
- **New:** a member the source marks as doubtful (the `?` on Calf) gets `J5_holds_to_be codhmo:tentative`, a new concept in `DeterminacyScheme`.
- **D19 interaction:** the calf rule takes only a `determined` Bos belief as premise, so a tentative Bos member never yields a calfskin claim (F5).

### D28. A reference specimen's taxon is a type assignment, not a hypothesis — *Accepted 2026-09-26*
When a study takes a specimen's identity as given (curated, morphological or voucher ID) and uses its spectra to derive markers, that identity is a `crm:E17_Type_Assignment`: P41 classified the material, P42 assigned the taxon, P14 by the curator or author team, with `dcterms:source` the paper. It is not a `TaxonomicHypothesis` supported by the spectra.
- **Why:** in pilot B the taxon is the premise and the markers are the conclusion. A hypothesis supported by its own reference spectra is circular (F11).
- **Marker derivation:** an I5 whose premises are the type assignment and the spectra, and whose conclusion is a marker-set belief. The marker set needs a class, which is left open.
- **CRM-native:** E17 is already in CIDOC CRM, so no new class is needed for the identity.

### D29. Taxa missing from NCBI may use a second authority (amends D8) — *Accepted 2026-09-26*
NCBI stays the required authority whenever it has the taxon. When it does not, a biological-source proposition may use a Catalogue of Life, GBIF backbone or Paleobiology Database taxon IRI, and must also give the nearest NCBI ancestor with `codhmo:nearestNcbiTaxon`.
- **Why:** pilot B's *Zygomaturus trilobus* and *Palorchestes azael* have no NCBI node at species, genus or family level. Under D8 they collapse to the order Diprotodontia (38609), erasing exactly what ZooMS of extinct fauna produces (F13). *Protemnodon mamkurra* reaches only genus level (2493641).
- **Guard:** SHACL still rejects names and IRIs from other sources. `check_ncbi_taxa.py` reports when an NCBI node has since appeared.

### D30. Bone, dentine and extract materials; samples of samples — *Accepted 2026-09-26*
Add `bone`, `dentine`, `antler`, `ivory` and `collagen-extract` (with `gelatin` as a narrower concept) to the material scheme. A sample drawn from an earlier extract is an `S13_Sample` whose `O3_sampled_from` is the earlier sample, which CRMsci allows.
- **Why:** pilot B had to declare bone and gelatin locally, and specimen MBS01's sample is ultrafiltered gelatin made for radiocarbon dating (F12).

### D31. Reuse of a support is a production event — *Accepted 2026-09-26*
A leaf reused from an earlier book is modelled with CRM production: the earlier object is an `E22_Human-Made_Object`, and the reuse is an `E12_Production` with `P16_used_specific_object` (the earlier leaf) and `P108_has_produced` (the new codex). Attributing a leaf to a particular earlier book is a hypothesis, as with taxa.
- **Why:** pilot A's headline result is that AM 795 4to was assembled from at least four earlier manuscripts (groups A–D), and CODHMO had no way to say it (F8).

### D32. Leaf identity is separate from sampling — *Accepted 2026-09-26*
There is one `MaterialLayer` per physical leaf or bifolio, keyed by folio (and quire), and several samplings may point at it.
- **Why:** pilot A made one layer per sample, which duplicated folio 89 (sampled as UoC21 and UoC53) (F9).

### D33. Derived measurements live in ZoomzPeak, not in the graph — *Accepted 2026-09-26*
Quantities computed from spectra (PQI, SE, identification score, proteomic cluster) go in a ZoomzPeak derived table keyed as in D24. The graph holds an `S4_Single_Observation` pointing at that row.
- **Why:** this keeps the D23 split (measurement in the store, interpretation in the graph). Pilot A dropped all of these because neither side had a place for them (F6).
- **Codicological observations** (ink, ruling, thickness, follicle pattern; F7) stay open. They are not spectral, so they need a CRMsci observation pattern.

### D34. Validation recipe — *Accepted 2026-09-26*
Shapes run against the **data and ontology merged** (`validate(data + ont, inference="rdfs")`), as the tests do. Passing the ontology as `ont_graph` gives false P45 violations and J5 warnings (F10). Say so in the README and the converter docstrings.

## Open items
- ~~Replace the synthetic source-record fixture with a real ZooMS row~~: real rows now exist in `data/vinas-caron-2023/` and `data/peters-2025/` (2026-09-26). The fixture stays as a minimal test; for key names see D24.
- ZoomzPeak changes needed for D24/D33: a `run` column and a spectrum `id` column (mzPeak naming); a sample list separate from replicates (Z2); instrument taken from the paper when the files lack it (Z3); a record of spectra measured but not deposited (Z4).
- Marker-set class for D28.
- Palandri et al. 2024 (Zenodo 18772648): MA01-MA20 sample-to-fragment/location mapping requested from the author (2026-09-17); the Missale example holds one representative spine sample until then.
- IN-A001 has not been sampled yet; its sampler, date and results will be added after processing, then tested with the researcher.
- Real analytical values to replace the PLACEHOLDERs in the Pepys example.
- Namespace IRI (`https://codicum.eu/ontology/codhmo#` is provisional).
- PSI-MS/UNIMOD alignment for peptide and PTM properties.
- Getty AAT matches for the material concepts.
- Real charter case to replace the illustrative one; AAT match for seal wax.
- Kasso binder taxon once proteomics is published; the fish taxon in ÆIN 656 at the rank the data support.
