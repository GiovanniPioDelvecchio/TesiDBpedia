import random as rng
from SPARQLWrapper import SPARQLWrapper, JSON
import string
import random as rng
import json


def get_uri_from_file(file_name):
    entities_file = open(file_name, 'r', encoding="utf-8")
    entities = entities_file.read()
    entity_list = entities.split("\n")
    n_result = int(rng.random() * len(entity_list))
    #print(n_result)
    return entity_list[n_result]


# è necessario ottenere una whitelist di entità diversa rispetto a quella fornita dal paper di
# riferimento. Questo perché necessitiamo di entità che abbiano tipi piuttosto disparati, in
# modo da generare query in linguaggio naturale piuttosto specifiche (ad non sono interessanti
# le entità che hanno come tipi solo: owl:Thing, dbo:Person, dbo:Agent ecc.).
# Per fare questo si selezionano, in ordine alfabetico, porzioni di entità di dbpedia, le quali
# devono rispettare le seguenti caratteristiche:
# -avere il prefisso dbr:
# -avere almeno 3 tipi con prefisso dbo:
def expand_entity_file(file_name):
    alphabet = list(string.ascii_uppercase)
    # character = alphabet[0]
    max_len = 100
    entities_file = open(file_name, 'w', encoding="utf-8")
    for character in alphabet:
        query = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?uri COUNT(?t) as ?numtypes WHERE{?uri rdf:type  ?t
                FILTER (strstarts(str(?t), str(dbo:)) && strstarts(str(?uri), "http://dbpedia.org/resource/""" + str(
            character) + """"^^xsd:string) )
                }
                GROUP BY ?uri
                HAVING (COUNT(?t)>=3)
                LIMIT """ + str(max_len) + """ 
                """

        print(query)
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.addExtraURITag("timeout", "30000")
        sparql.setReturnFormat(JSON)
        print("Sto eseguendo la query...")
        sparql.setQuery(query)
        temp_dict = sparql.query().convert()["results"]["bindings"]
        temp_dict_len = len(temp_dict)
        entity_uris_results = [temp_dict[i]["uri"]["value"] for i in range(0, temp_dict_len)]
        print(entity_uris_results)
        for i in range(temp_dict_len):
            entities_file.write(str(entity_uris_results[i]) + "\n")


def get_type_blacklist(file_name="files_to_add/type_blacklist.txt"):
    type_file = open(file_name, 'r', encoding="utf-8")
    types_read = type_file.read()
    types_list = types_read.split("\n")
    return types_list


def get_relation_whitelist(file_name="files_to_add/relations_new.txt"):
    relations_file = open(file_name, 'r', encoding="utf-8")
    relation_read = relations_file.read()
    relation_list = relation_read.split("\n")
    return relation_list


def remove_relation_from_whitelist(relation_name, file_name="files_to_add/relations_new.txt"):
    relations_file = open(file_name, 'r', encoding="utf-8")
    relation_read = relations_file.read()
    relation_list = relation_read.split("\n")
    relation_list.remove(relation_name)
    relations_file = open(file_name, 'w', encoding="utf-8")
    relation_list_len = len(relation_list)
    for i in range(relation_list_len):
        relations_file.write(str(relation_list[i]) + "\n")


def serialize_query_set(dict_to_serialize, file_name="files_to_add/generated_queries.txt"):
    generated_file = open(file_name, 'w', encoding="utf-8")
    generated_file.write(json.dumps(dict_to_serialize, indent = 4, sort_keys = True))

# expand_entity_file("../entities_new.txt")
