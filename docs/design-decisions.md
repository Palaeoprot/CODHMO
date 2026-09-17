# CODHMO design decisions

_Last updated: 2026-09-17_

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

## Open items
- Palandri et al. 2024 (Zenodo 18772648): MA01-MA20 sample-to-fragment/location mapping requested from the author (2026-09-17); the Missale example holds one representative spine sample until then.
- IN-A001 sampler and date (the Pepys conformance test is expected to fail until they are supplied).
- Real analytical values to replace the PLACEHOLDERs in the Pepys example.
- Namespace IRI (`https://codicum.eu/ontology/codhmo#` is provisional).
- Review of the remaining RDFS domains and ranges (D10).
- PSI-MS/UNIMOD alignment for peptide and PTM properties.
- Getty AAT matches for the material concepts.
- Real charter case to replace the illustrative one; AAT match for seal wax.
- Kasso binder taxon once proteomics is published; the fish taxon in ÆIN 656 at the rank the data support.
- Reference papers with mixed binders (e.g. Zaggia et al. 2026): the library copy is a failed web capture and needs re-downloading.
