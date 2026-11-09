from rdflib import Graph

g = Graph()
g.parse("book.ttl", format="turtle")

q = """
PREFIX bk: <http://example.org/groupA-wizard-of-oz#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX schema: <https://schema.org/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
PREFIX pq: <http://www.wikidata.org/prop/qualifier/>

SELECT ?place ?population 
WHERE {
    ?place a schema:Place ;
           bk:mentionedIn bk:ChapterI ;
           owl:sameAs ?Resource .

    FILTER(STRSTARTS(STR(?Resource), "http://www.wikidata.org/entity/"))

    SERVICE <https://query.wikidata.org/sparql> {
        ?Resource p:P1082 ?statement .
        ?statement ps:P1082 ?population .
    }
}
LIMIT 1
"""

for row in g.query(q):
    print(f'Place: {row.place} - Population: {row.population}')
