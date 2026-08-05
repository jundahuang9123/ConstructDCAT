#!/usr/bin/env python3
"""Validate the Construct-DCAT vocabulary, examples, and query."""

from __future__ import annotations

import sys
from collections import Counter
from hashlib import sha256
from html.parser import HTMLParser
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

SPEC_SNAPSHOTS = (
    "docs/index.html",
    "docs/releases/latest/index.html",
    "docs/releases/0.1.0/index.html",
)

PAGES_SERIALIZATIONS = (
    ("docs/construct-dcat.ttl", "turtle"),
    ("docs/construct-dcat.jsonld", "json-ld"),
    ("docs/releases/latest/construct-dcat.ttl", "turtle"),
    ("docs/releases/latest/construct-dcat.jsonld", "json-ld"),
    ("docs/releases/0.1.0/construct-dcat.ttl", "turtle"),
    ("docs/releases/0.1.0/construct-dcat.jsonld", "json-ld"),
)

PUBLISHED_SUPPORT_FILES = (
    ("examples/example-catalog.ttl", "docs/releases/0.1.0/examples/example-catalog.ttl"),
    ("examples/example-catalog.ttl", "docs/releases/latest/examples/example-catalog.ttl"),
    ("queries/wall-bot.rq", "docs/releases/0.1.0/queries/wall-bot.rq"),
    ("queries/wall-bot.rq", "docs/releases/latest/queries/wall-bot.rq"),
    ("CITATION.cff", "docs/releases/0.1.0/CITATION.cff"),
    ("CITATION.cff", "docs/releases/latest/CITATION.cff"),
)

REQUIRED_SPEC_IDS = {
    "abstract",
    "sotd",
    "overview",
    "AASDataset",
    "BIMDataset",
    "describesAssetType",
    "usesOntology",
    "alignsWithConcept",
    "hasAASSubmodel",
    "examples",
    "resources",
    "version-history",
}


class ValidationError(RuntimeError):
    """Raised when a required vocabulary invariant is not satisfied."""


class IdCollector(HTMLParser):
    """Collect element IDs from a generated specification snapshot."""

    def __init__(self) -> None:
        super().__init__()
        self.ids: list[str] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        del tag
        element_id = dict(attrs).get("id")
        if element_id:
            self.ids.append(element_id)


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
    for relative_path, rdf_format in PAGES_SERIALIZATIONS:
        pages_graph = parse_graph(relative_path, rdf_format)
        require(
            isomorphic(turtle, pages_graph),
            f"{relative_path} must match the root vocabulary graph.",
        )

    snapshot_bytes = [
        (ROOT / relative_path).read_bytes() for relative_path in SPEC_SNAPSHOTS
    ]
    require(
        len(set(snapshot_bytes)) == 1,
        "The root, latest, and 0.1.0 specification snapshots must be identical.",
    )

    snapshot_text = snapshot_bytes[0].decode("utf-8")
    snapshot_lower = snapshot_text.lower()
    for forbidden_marker in (
        "<script",
        "respecconfig",
        "respec-w3c",
        "www.w3.org/tools/respec",
        '<link rel="stylesheet"',
    ):
        require(
            forbidden_marker not in snapshot_lower,
            f"The static specification must not contain {forbidden_marker!r}.",
        )

    id_collector = IdCollector()
    id_collector.feed(snapshot_text)
    id_counts = Counter(id_collector.ids)
    duplicate_ids = sorted(
        element_id for element_id, count in id_counts.items() if count > 1
    )
    require(not duplicate_ids, f"Duplicate HTML IDs in specification: {duplicate_ids}")
    require(
        REQUIRED_SPEC_IDS <= set(id_collector.ids),
        "The specification is missing required stable section or term fragments.",
    )
    source_bytes = (ROOT / "spec" / "index.html").read_bytes()
    vendor_css_bytes = (ROOT / "spec" / "vendor" / "w3c-base.css").read_bytes()
    build_hash = sha256(source_bytes + b"\0" + vendor_css_bytes).hexdigest()
    require(
        f'<meta name="construct-dcat-build-sha256" content="{build_hash}">'
        in snapshot_text,
        "The static specification must be rebuilt after changing its source or CSS.",
    )
    require(
        '<style id="construct-dcat-vendored-base">' in snapshot_text,
        "The static specification must contain the vendored base stylesheet.",
    )
    require(
        "Construct-DCAT 0.1.0" in snapshot_text
        and "Initial conceptual release" in snapshot_text,
        "The specification must identify version 0.1.0 and its release status.",
    )
    require(
        "W3C-internal document" not in snapshot_text
        and "does not represent consensus of the W3C Membership"
        not in snapshot_text,
        "The independent specification must not contain W3C status boilerplate.",
    )
    require(
        "Copyright © 2026 Junda Huang" in snapshot_text
        and "https://creativecommons.org/licenses/by/4.0/" in snapshot_text,
        "The specification must publish the Construct-DCAT CC BY 4.0 notice.",
    )
    for source_path, published_path in PUBLISHED_SUPPORT_FILES:
        require(
            (ROOT / source_path).read_bytes() == (ROOT / published_path).read_bytes(),
            f"{published_path} must match {source_path}.",
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
        "Validation passed: all RDF copies are equivalent, all six terms are valid, "
        "the static specification snapshots are synchronized, and the example catalog "
        "and SPARQL query parse and run successfully."
    )


if __name__ == "__main__":
    try:
        validate()
    except ValidationError as exc:
        print(f"Validation failed: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
