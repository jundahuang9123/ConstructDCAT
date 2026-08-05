# Construct-DCAT

Construct-DCAT is a lightweight RDF vocabulary for adding representation-independent semantic anchors to DCAT catalog records for heterogeneous construction datasets. The catalog metadata is RDF, but the data it describes may be IFC, Asset Administration Shell (AAS) JSON, tabular, geospatial, sensor, document, RDF, or another representation.

## Identity and status

- Vocabulary IRI: `https://w3id.org/construct-dcat`
- Namespace: `https://w3id.org/construct-dcat#`
- Preferred prefix: `cx:`
- Version: `0.1.0`
- Status: initial conceptual release

## Scope

Construct-DCAT extends descriptions of `dcat:Dataset` records with a small set of construction-oriented discovery anchors. It can be used in DCAT and DCAT-AP catalogs, but version 0.1.0 is not a complete DCAT-AP profile and defines no SHACL constraints. `cx:AASDataset` and `cx:BIMDataset` are initial examples, not an exhaustive dataset taxonomy.

The four properties do not hard-code a closed list of external vocabularies. Their objects are IRIs from any suitable ontology, class hierarchy, AAS model, or controlled vocabulary. This release asserts no `rdfs:subPropertyOf` alignments to DCAT or Dublin Core.

## Current terms

| Term | Kind | Domain or parent | Range | Meaning |
| --- | --- | --- | --- | --- |
| `cx:AASDataset` | Class | subclass of `dcat:Dataset` | — | A dataset represented by, or organized around, one or more Asset Administration Shells. |
| `cx:BIMDataset` | Class | subclass of `dcat:Dataset` | — | A dataset containing building information modeling data. |
| `cx:describesAssetType` | Object property | `dcat:Dataset` | `rdfs:Class` | The physical asset or building-element type described by the dataset. |
| `cx:usesOntology` | Object property | `dcat:Dataset` | no formal range | An ontology, vocabulary, or semantic resource used or referenced by the dataset. Values may identify OWL ontologies, SKOS concept schemes, or other resolvable resources. |
| `cx:alignsWithConcept` | Object property | `dcat:Dataset` | `skos:Concept` | A controlled concept used to classify or semantically align the dataset. |
| `cx:hasAASSubmodel` | Object property | `dcat:Dataset` | no formal range | An AAS submodel or submodel descriptor exposed as a catalog-level discovery anchor. A range is deferred until a stable canonical RDF class IRI is selected. |

## Turtle example

```turtle
@prefix bot:  <https://w3id.org/bot#> .
@prefix cx:   <https://w3id.org/construct-dcat#> .
@prefix dcat: <http://www.w3.org/ns/dcat#> .
@prefix ex:   <https://example.org/construct-dcat/> .
@prefix ifc:  <https://standards.buildingsmart.org/IFC/DEV/IFC4_3/OWL#> .

ex:wall-model
    a dcat:Dataset, cx:BIMDataset ;
    cx:describesAssetType ifc:IfcWall ;
    cx:usesOntology bot: ;
    dcat:distribution ex:wall-model-ifc .
```

This RDF describes the catalog record. Its distribution can remain a non-RDF IFC-SPF file; the same principle applies to AAS JSON, CSV, geospatial files, sensor exports, and documents. See the [complete example](examples/example-catalog.ttl).

## Construct-DCAT and VoID

> VoID can describe vocabularies, classes, properties, and partitions occurring within RDF datasets. Construct-DCAT instead exposes representation-independent semantic anchors on DCAT catalog records, including records for non-RDF datasets. RDF datasets may use both vocabularies together.

## Repository layout

```text
ConstructDCAT/
├── .github/workflows/validate.yml
├── docs/
│   ├── construct-dcat.jsonld
│   ├── construct-dcat.ttl
│   └── index.html
├── examples/example-catalog.ttl
├── queries/wall-bot.rq
├── scripts/validate.py
├── .gitignore
├── CITATION.cff
├── LICENSE
├── README.md
├── construct-dcat.jsonld
├── construct-dcat.ttl
└── requirements.txt
```

## Validation

```bash
python -m pip install -r requirements.txt
python scripts/validate.py
```

The validator parses both vocabulary serializations and their GitHub Pages copies, checks the six-term model, confirms the serializations are RDF-isomorphic, and parses and executes the SPARQL query. The copies under `docs/` let the W3ID content-negotiation targets return RDF-specific media types; the canonical editable sources remain the repository-root files.

## License and maintainer

Construct-DCAT is licensed under [Creative Commons Attribution 4.0 International](LICENSE).

Maintained by [Junda Huang](https://orcid.org/0000-0002-1246-5759), University of Wuppertal. Contact: [huang@uni-wuppertal.de](mailto:huang@uni-wuppertal.de) · GitHub: [jundahuang9123](https://github.com/jundahuang9123)
