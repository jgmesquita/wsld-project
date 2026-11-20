# Output

* File      : book.ttl
* Namespace : http://example.org/groupA-wizard-of-oz#
* Triples   : 129


### 1. COMPETENCY-QUESTION COVERAGE
* 6 of 6 questions return at least one row.

    * ok    cq1.rq  (1 rows)
    * ok    cq2.rq  (2 rows)
    * ok    cq3.rq  (1 rows)
    * ok    cq4.rq  (1 rows)
    * ok    cq5.rq  (2 rows)
    * ok    cq6.rq  (3 rows)

* Judge correctness yourself: rows returned is not rows right.

### 2. PRECISION
* 20 triples drawn at random from 51 data triples, seed 2026.
* Written to precision_sample.md - mark each TRUE or FALSE against the book.

### 3. IRI REUSE
* Vocabulary reuse: 12 of 27 distinct domain predicates and classes are reused = 0.44
(rdf, rdfs, owl and xsd are excluded: using them is not a choice)
    * 7  https://schema.org/
    * 3  http://purl.org/dc/terms/
    * 2  http://xmlns.com/foaf/0.1/

* Entity links: 4 of your 33 individuals are linked outward (owl:sameAs / rdfs:seeAlso / skos:*Match)

### 4. ORPHAN NODES
* 0 of 20 data nodes take part in no object property.
* Four numbers for the report:
   * coverage      6/6
   * precision     ____/20   (fill in from precision_sample.md)
   * reuse ratio   0.44
   * orphans       0
* Record one sentence per measure saying what it means for your graph.