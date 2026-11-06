from rdflib import Graph

g = Graph()
g.parse("book.ttl", format="turtle") # fails if your Turtle is broken
print(len(g), "triples")
g.serialize("book.rdf", format="xml")
g.serialize("book.jsonld", format="json-ld")
g.serialize("book-roundtrip.ttl", format="turtle")