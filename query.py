from pathlib import Path
from rdflib import Graph

QUERY_NUMBER = 6

PREFIXES = """
PREFIX bk: <http://example.org/groupA-wizard-of-oz#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX schema: <https://schema.org/>
PREFIX p: <http://www.wikidata.org/prop/>
PREFIX ps: <http://www.wikidata.org/prop/statement/>
"""


def local_name(resource):
    return resource.rsplit("#", 1)[-1]


QUERIES = {
    # 1 - Qual é a população da cidade mencionada no primeiro capítulo?
    1: (
        """
        SELECT ?place ?population
        WHERE {
            ?place a schema:Place ;
                   bk:mentionedIn bk:ChapterI ;
                   owl:sameAs ?resource .
            FILTER(STRSTARTS(STR(?resource), "http://www.wikidata.org/entity/"))
            SERVICE <https://query.wikidata.org/sparql> {
                ?resource p:P1082 ?statement .
                ?statement ps:P1082 ?population .
            }
        }
        LIMIT 1
        """,
        lambda row: f"Place: {row.place} - Population: {row.population}",
    ),
    # 2 - Que personagens aparecem no 1º capítulo e não no 2º capítulo?
    2: (
        """
        SELECT ?character WHERE {
            ?character bk:appearsIn bk:ChapterI .
            FILTER NOT EXISTS { ?character bk:appearsIn bk:ChapterII }
        }
        ORDER BY ?character
        """,
        lambda row: f"Personagem: {local_name(row.character)}",
    ),
    # 3 - Que personagens morrem no 2º capítulo?
    3: (
        """
        SELECT DISTINCT ?character WHERE {
            ?character bk:appearsIn bk:ChapterII ;
                       bk:killedBy ?killer .
        }
        ORDER BY ?character
        """,
        lambda row: f"Personagem: {local_name(row.character)}",
    ),
    # 4 - Que bruxa inimiga da Bruxa do Norte governa o País dos Munchkins e que objeto mágico possui?
    4: (
        """
        SELECT DISTINCT ?witch ?item WHERE {
            bk:WitchOfTheNorth (bk:enemiesWith|^bk:enemiesWith) ?witch .
            ?witch a bk:Witch ;
                   bk:rules bk:MunchkinCountry ;
                   bk:possesses ?item .
            ?item a bk:Item .
        }
        ORDER BY ?witch ?item
        """,
        lambda row: f"Bruxa: {local_name(row.witch)} - Objeto mágico: {local_name(row.item)}",
    ),
    # 5 - Que personagens relacionadas com Dorothy aparecem no primeiro capítulo e vivem no Kansas?
    5: (
        """
        SELECT DISTINCT ?character WHERE {
            bk:Dorothy (schema:relatedTo|^schema:relatedTo) ?character .
            ?character bk:appearsIn bk:ChapterI ;
                       bk:livesIn bk:Kansas .
        }
        ORDER BY ?character
        """,
        lambda row: f"Personagem: {local_name(row.character)}",
    ),
    # 6 - Que personagens vivem no mesmo local que um agricultor que aparece no primeiro capítulo?
    6: (
        """
        SELECT DISTINCT ?character ?place WHERE {
            ?farmer schema:hasOccupation bk:Farmer ;
                    bk:appearsIn bk:ChapterI ;
                    bk:livesIn ?place .
            ?character bk:livesIn ?place .
            FILTER(?character != ?farmer)
        }
        ORDER BY ?character ?place
        """,
        lambda row: f"Personagem: {local_name(row.character)} - Local: {local_name(row.place)}",
    ),
}


def main():
    if QUERY_NUMBER not in QUERIES:
        raise SystemExit("Escolha um número entre 1 e 6.")

    graph = Graph()
    graph.parse(Path(__file__).with_name("book.ttl"), format="turtle")
    query, format_row = QUERIES[QUERY_NUMBER]
    for row in graph.query(PREFIXES + query):
        print(format_row(row))


if __name__ == "__main__":
    main()
