#!/usr/bin/env python3
"""
evaluate_graph.py - the four M2 measurements, computed the same way for every group.

Usage:
    python evaluate_graph.py book.ttl --base http://example.org/mybook#
    python evaluate_graph.py book.ttl --base http://example.org/mybook# --queries cq/
    python evaluate_graph.py book.ttl --base http://example.org/mybook# --seed 7

--base is your own namespace: the one you minted IRIs in. Everything outside it
counts as external (reused).

--queries is a folder holding your six competency questions as .rq files
(cq1.rq ... cq6.rq). Without it, coverage is skipped.

The script writes precision_sample.md next to your file: twenty randomly drawn
triples for you to mark TRUE or FALSE against the book by hand. Nothing else is
manual.
"""

import argparse
import random
import sys
from collections import defaultdict
from pathlib import Path

from rdflib import Graph, RDF, RDFS, OWL, URIRef, BNode, Literal
from rdflib.namespace import XSD, SKOS, DCTERMS, FOAF

# Namespaces that are schema, not data. Triples using these predicates describe
# the model rather than the book, so they are excluded from the precision sample.
SCHEMA_PREDICATES = {
    RDF.type, RDFS.subClassOf, RDFS.subPropertyOf, RDFS.domain, RDFS.range,
    RDFS.label, RDFS.comment, RDFS.seeAlso, RDFS.isDefinedBy,
    OWL.equivalentClass, OWL.disjointWith, OWL.inverseOf, OWL.onProperty,
    OWL.someValuesFrom, OWL.allValuesFrom, OWL.cardinality, OWL.minCardinality,
    OWL.maxCardinality, OWL.members, OWL.intersectionOf, OWL.unionOf,
}

VOCAB_NAMESPACES = [str(RDF), str(RDFS), str(OWL), str(XSD)]


def is_internal(term, base):
    return isinstance(term, URIRef) and str(term).startswith(base)


def is_external(term, base):
    return isinstance(term, URIRef) and not str(term).startswith(base)


def namespace_of(iri):
    s = str(iri)
    for sep in ("#", "/"):
        if sep in s:
            return s.rsplit(sep, 1)[0] + sep
    return s


# ---------------------------------------------------------------- measure 1
def coverage(graph, qdir):
    """How many competency questions the graph can answer.

    A question counts as answered when its query returns at least one row.
    Whether the row is RIGHT is for you to say in the report - the script only
    tells you whether the graph has anything to say at all.
    """
    files = sorted(Path(qdir).glob("*.rq"))
    if not files:
        return None, []
    results = []
    for f in files:
        try:
            rows = list(graph.query(f.read_text(encoding="utf-8")))
            results.append((f.name, len(rows)))
        except Exception as exc:                       # a query that will not parse
            results.append((f.name, f"ERROR: {exc}"))
    answered = sum(1 for _, n in results if isinstance(n, int) and n > 0)
    return (answered, len(files)), results


# ---------------------------------------------------------------- measure 2
def precision_sample(graph, base, seed, out_path):
    """Draw 20 data triples at random for manual checking against the book.

    Data triples only: schema axioms and labels are excluded, because checking
    'Person rdfs:subClassOf Thing' against a novel means nothing. The sample is
    RANDOM and seeded - you do not get to pick the twenty you like.
    """
    data = [
        (s, p, o) for s, p, o in graph
        if p not in SCHEMA_PREDICATES
        and not isinstance(s, BNode)
        and not isinstance(o, BNode)
        and (is_internal(s, base) or is_internal(o, base))
    ]
    rng = random.Random(seed)
    k = min(20, len(data))
    sample = rng.sample(data, k) if data else []

    def short(t):
        if isinstance(t, Literal):
            return f'"{t}"'
        s = str(t)
        for sep in ("#", "/"):
            if sep in s:
                return s.rsplit(sep, 1)[1] or s
        return s

    lines = [
        "# Precision sample (M2)",
        "",
        f"Seed: {seed}. Population: {len(data)} data triples. Drawn: {k}.",
        "",
        "Mark each triple TRUE if the book supports it and FALSE if it does not.",
        "A triple you cannot decide counts as FALSE; say why in the report.",
        "",
        "| # | subject | predicate | object | TRUE / FALSE | note |",
        "|---|---------|-----------|--------|--------------|------|",
    ]
    for i, (s, p, o) in enumerate(sample, 1):
        lines.append(f"| {i} | {short(s)} | {short(p)} | {short(o)} |  |  |")
    lines += ["", "Precision = TRUE / " + str(k) + " = ____"]
    Path(out_path).write_text("\n".join(lines), encoding="utf-8")
    return k, len(data)


# ---------------------------------------------------------------- measure 3
def reuse(graph, base):
    """Vocabulary reuse, and entity links, reported separately.

    Vocabulary reuse asks: of the distinct predicates and classes you use, how
    many came from somewhere else? Minting ex:hasAuthor when schema:author
    exists is what this catches.

    Entity linking is counted separately, because characters and places in your
    book MUST be minted - there is no external IRI for most of them. Where one
    does exist (Wikidata has your author, and often the famous characters too),
    an owl:sameAs or rdfs:seeAlso to it is worth having, and this counts them.
    """
    predicates = {p for _, p, _ in graph if isinstance(p, URIRef)}
    classes = {o for _, p, o in graph.triples((None, RDF.type, None))
               if isinstance(o, URIRef) and str(o) not in (str(OWL.Class),
                                                           str(OWL.ObjectProperty),
                                                           str(OWL.DatatypeProperty),
                                                           str(OWL.NamedIndividual),
                                                           str(OWL.Ontology),
                                                           str(OWL.Restriction),
                                                           str(OWL.FunctionalProperty))}
    classes |= {s for s, _, _ in graph.triples((None, RDF.type, OWL.Class))
                if isinstance(s, URIRef)}

    # rdf, rdfs, owl and xsd are not a choice: every graph uses them. Counting
    # them as "reuse" would give everybody the same free 0.4 and measure nothing.
    # What is measured is DOMAIN vocabulary: schema.org, FOAF, Dublin Core, SKOS,
    # BIBO, CIDOC-CRM, Wikidata properties, and so on.
    vocab = {t for t in (predicates | classes)
             if not any(str(t).startswith(ns) for ns in VOCAB_NAMESPACES)}
    external = {t for t in vocab if is_external(t, base)}
    ratio = len(external) / len(vocab) if vocab else 0.0

    by_ns = defaultdict(int)
    for t in external:
        by_ns[namespace_of(t)] += 1

    link_predicates = (OWL.sameAs, RDFS.seeAlso, SKOS.exactMatch, SKOS.closeMatch)
    links = [(s, p, o) for p in link_predicates
             for s, _, o in graph.triples((None, p, None))
             if is_internal(s, base) and is_external(o, base)]

    internal_individuals = {
        s for s, _, _ in graph.triples((None, RDF.type, None))
        if is_internal(s, base)
    } - {s for s, _, _ in graph.triples((None, RDF.type, OWL.Class))}

    return {
        "vocab_total": len(vocab),
        "vocab_external": len(external),
        "ratio": ratio,
        "by_namespace": dict(sorted(by_ns.items(), key=lambda kv: -kv[1])),
        "entity_links": len(links),
        "individuals": len(internal_individuals),
    }


# ---------------------------------------------------------------- measure 4
def orphans(graph, base):
    """Nodes that are in the graph but not in the story.

    An orphan is one of your own resources that takes part in no object
    property at all: nothing points to it and it points to nothing. It may
    carry a type and a name and three literals, and still be an island.

    Typing, labelling and literals do not count as connections. If Watson is in
    your file with a name and a birth year but is never linked to Holmes, to a
    place or to an event, Watson is an orphan - and the graph knows nothing
    about him that a spreadsheet row would not.
    """
    connected = set()
    for s, p, o in graph:
        if p in SCHEMA_PREDICATES or isinstance(o, Literal):
            continue
        if is_internal(s, base) and isinstance(o, URIRef):
            connected.add(s)
            if is_internal(o, base):
                connected.add(o)

    described = {s for s, _, _ in graph if is_internal(s, base)}
    described |= {o for _, _, o in graph if is_internal(o, base)}

    # classes, properties and the ontology header are not data nodes
    schema_nodes = set()
    for t in (OWL.Class, OWL.ObjectProperty, OWL.DatatypeProperty,
              OWL.AnnotationProperty, OWL.Ontology, RDFS.Class, RDF.Property):
        schema_nodes |= {s for s, _, _ in graph.triples((None, RDF.type, t))}

    # A term used as a predicate, or as the object of rdf:type, is schema even
    # when it was never declared. Without this, a group that writes
    # "bk:appearsIn a rdf:Property" - or that never declares bk:Chapter at all -
    # sees its own vocabulary counted as orphan data.
    schema_nodes |= {p for _, p, _ in graph if isinstance(p, URIRef)}
    schema_nodes |= {o for _, _, o in graph.triples((None, RDF.type, None))
                     if isinstance(o, URIRef)}

    data_nodes = {n for n in described if n not in schema_nodes}
    orphan_set = data_nodes - connected
    return sorted(str(n) for n in orphan_set), len(data_nodes)


# ---------------------------------------------------------------- report
def main():
    ap = argparse.ArgumentParser(description="M2 measurements for a book knowledge graph")
    ap.add_argument("file", help="your Turtle file, e.g. G04_M1_book.ttl")
    ap.add_argument("--base", required=True, help="your own namespace, e.g. http://example.org/mybook#")
    ap.add_argument("--queries", help="folder with cq1.rq ... cq6.rq")
    ap.add_argument("--seed", type=int, default=2026, help="sampling seed (keep 2026 unless told otherwise)")
    args = ap.parse_args()

    g = Graph()
    suffix = Path(args.file).suffix.lower()
    fmt = {".ttl": "turtle", ".owl": "xml", ".rdf": "xml", ".nt": "nt",
           ".jsonld": "json-ld", ".n3": "n3"}.get(suffix, "turtle")
    if not Path(args.file).exists():
        sys.exit(f"File not found: {args.file}\n"
                 f"Run this from the folder that holds your Turtle file, "
                 f"or give the full path.")
    try:
        g.parse(args.file, format=fmt)
    except Exception as exc:
        sys.exit(f"{args.file} could not be parsed as {fmt}.\n"
                 f"{type(exc).__name__}: {exc}\n"
                 f"Fix the file before measuring it. Common causes: a missing "
                 f"full stop at the end of a statement, an undeclared prefix, "
                 f"or an unclosed angle bracket or quote.")

    print(f"\nFile      : {args.file}")
    print(f"Namespace : {args.base}")
    print(f"Triples   : {len(g)}\n")
    print("=" * 62)

    cov, detail = coverage(g, args.queries) if args.queries else (None, [])
    print("\n1. COMPETENCY-QUESTION COVERAGE")
    if cov:
        print(f"   {cov[0]} of {cov[1]} questions return at least one row.")
        for name, n in detail:
            mark = "ok  " if isinstance(n, int) and n > 0 else "EMPTY" if n == 0 else "FAIL"
            print(f"     {mark}  {name}  ({n} rows)" if isinstance(n, int) else f"     {mark}  {name}  {n}")
        print("   Judge correctness yourself: rows returned is not rows right.")
    else:
        print("   skipped (no --queries folder given)")

    out = Path(args.file).with_name("precision_sample.md")
    k, pop = precision_sample(g, args.base, args.seed, out)
    print("\n2. PRECISION")
    print(f"   {k} triples drawn at random from {pop} data triples, seed {args.seed}.")
    print(f"   Written to {out.name} - mark each TRUE or FALSE against the book.")

    r = reuse(g, args.base)
    print("\n3. IRI REUSE")
    print(f"   Vocabulary reuse: {r['vocab_external']} of {r['vocab_total']} distinct "
          f"domain predicates and classes are reused = {r['ratio']:.2f}")
    print("   (rdf, rdfs, owl and xsd are excluded: using them is not a choice)")
    for ns, n in r["by_namespace"].items():
        print(f"     {n:3d}  {ns}")
    print(f"   Entity links: {r['entity_links']} of your {r['individuals']} individuals "
          f"are linked outward (owl:sameAs / rdfs:seeAlso / skos:*Match)")

    orph, total = orphans(g, args.base)
    print("\n4. ORPHAN NODES")
    print(f"   {len(orph)} of {total} data nodes take part in no object property.")
    for o in orph[:15]:
        print(f"     {o}")
    if len(orph) > 15:
        print(f"     ... and {len(orph) - 15} more")

    print("\n" + "=" * 62)
    print("\nFour numbers for the report:")
    print(f"   coverage      {cov[0]}/{cov[1]}" if cov else "   coverage      (run with --queries)")
    print(f"   precision     ____/{k}   (fill in from precision_sample.md)")
    print(f"   reuse ratio   {r['ratio']:.2f}")
    print(f"   orphans       {len(orph)}")
    print("\nRecord one sentence per measure saying what it means for your graph.\n")


if __name__ == "__main__":
    main()