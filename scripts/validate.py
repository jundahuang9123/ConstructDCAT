#!/usr/bin/env python3
"""Validate the Construct-DCAT vocabulary, examples, and query."""

from __future__ import annotations

import sys
from pathlib import Path

from rdflib import Graph, Namespace, URIRef
from rdflib.compare import isomorphic
from rdflib.namespace import OWL, RDF, RDFS, SKOS
from rdflib.plugins.sparql.parser import parseQuery


ROOT = Path(__file__).resolve().parents[1]
ONTOLOGY = URIRef("https://w3id.org/construct-dcat")
CX = Namespace("https://w3id.org/construct-dcat#")
DCAT = Namespace("http://www.w3.org/ns/dcat#")

CLASSES = {CX.AASDataset, CX.BIMDataset}
PROPERTIES = {
    CX.describesAssetType,
    CX.usesOntology,
    CX.alignsWithConcept,
    CX.hasAASSubmodel,
}
TERMS = CLASSES | PROPERTIES


class ValidationError(RuntimeError):
    """Raised when a required vocabulary invariant is not satisfied."""


def parse_graph(relative_path: str, rdf_format: str) -> Graph:
    path = ROOT / relative_path
    try:
        return Graph().parse(path, format=rdf_format)
    except Exception as exc:  # rdflib exposes parser-specific exception types
        raise ValidationError(f"Could not parse {relative_path}: {exc}") from exc


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def validate() -> None:
    turtle = parse_graph("construct-dcat.ttl", "turtle")
    jsonld = parse_graph("construct-dcat.jsonld", "json-ld")
    pages_turtle = parse_graph("docs/construct-dcat.ttl", "turtle")
    pages_jsonld = parse_graph("docs/construct-dcat.jsonld", "json-ld")
    example = parse_graph("examples/example-catalog.ttl", "turtle")

    ontology_subjects = set(turtle.subjects(RDF.type, OWL.Ontology))
    require(
        ontology_subjects == {ONTOLOGY},
        "The sole owl:Ontology IRI must be https://w3id.org/construct-dcat.",
    )

    for term in sorted(TERMS, key=str):
        require(any(turtle.triples((term, None, None))), f"Missing term: {term}")

    declared_cx_terms = {
        subject
        for subject in turtle.subjects()
        if isinstance(subject, URIRef) and str(subject).startswith(str(CX))
    }
    require(
        declared_cx_terms == TERMS,
        "The initial release must declare exactly the specified six cx: terms.",
    )

    for class_iri in CLASSES:
        require(
            (class_iri, RDF.type, OWL.Class) in turtle,
            f"{class_iri} must be an owl:Class.",
        )
        require(
            (class_iri, RDFS.subClassOf, DCAT.Dataset) in turtle,
            f"{class_iri} must be a subclass of dcat:Dataset.",
        )

    for property_iri in PROPERTIES:
        require(
            (property_iri, RDF.type, OWL.ObjectProperty) in turtle,
            f"{property_iri} must be an owl:ObjectProperty.",
        )
        require(
            (property_iri, RDFS.domain, DCAT.Dataset) in turtle,
            f"{property_iri} must have domain dcat:Dataset.",
        )
        require(
            not any(turtle.triples((property_iri, RDFS.subPropertyOf, None))),
            f"{property_iri} must not have an initial rdfs:subPropertyOf alignment.",
        )

    require(
        (CX.describesAssetType, RDFS.range, RDFS.Class) in turtle,
        "cx:describesAssetType must have range rdfs:Class.",
    )
    require(
        (CX.alignsWithConcept, RDFS.range, SKOS.Concept) in turtle,
        "cx:alignsWithConcept must have range skos:Concept.",
    )
    for property_iri in {CX.usesOntology, CX.hasAASSubmodel}:
        require(
            not any(turtle.triples((property_iri, RDFS.range, None))),
            f"{property_iri} must not have a formal range in version 0.1.0.",
        )

    require(
        isomorphic(turtle, jsonld),
        "construct-dcat.ttl and construct-dcat.jsonld are not equivalent RDF graphs.",
    )
    require(
        isomorphic(turtle, pages_turtle) and isomorphic(jsonld, pages_jsonld),
        "The GitHub Pages serialization copies must match the root vocabulary files.",
    )
    require(len(example) > 0, "The example catalog must contain RDF statements.")

    query_path = ROOT / "queries" / "wall-bot.rq"
    query_text = query_path.read_text(encoding="utf-8")
    try:
        parseQuery(query_text)
    except Exception as exc:
        raise ValidationError(f"Could not parse queries/wall-bot.rq: {exc}") from exc

    expected_wall_dataset = URIRef("https://example.org/construct-dcat/wall-model")
    query_results = list(example.query(query_text))
    require(
        any(row.dataset == expected_wall_dataset for row in query_results),
        "queries/wall-bot.rq must retrieve the example IFC wall dataset.",
    )

    print(
        "Validation passed: root and Pages serializations are equivalent, all six "
        "terms are valid, and the example catalog and SPARQL query parse and run successfully."
    )


if __name__ == "__main__":
    try:
        validate()
    except ValidationError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
