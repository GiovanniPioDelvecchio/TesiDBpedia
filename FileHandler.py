import random as rng
from SPARQLWrapper import SPARQLWrapper, JSON
import string
import random as rng
import json

"""Package che si occupa di gestire i files utilizzati all'interno del progetto

L'obiettivo di questo package è esporre un'interfaccia con i files agli altri moduli, in modo
da non demandare ai singoli moduli l'accesso alle risorse esterne.

Esempio tipico di utilizzo:

foo = get_uri_from_file('files_to_add\entities_new.txt')
bar = expand_entity_file('files_to_add\entities_new.txt')
"""


def get_uri_from_file(file_name):
    """Considera un'entità a caso presa dal file file_name

    Args:
        file_name: file di entità da cui bisogna prenderne una.
    Returns:
         entity_list[n_result]: una delle entry del file, precisamente la entry in posizione n_result.
    """
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
    """Funzione che si occupa di espandere (riscrivere) il file di entità, in base alle caratteristiche scelte.

    Args:
        file_name: file di entità da arricchire con nuove entità che soddisfino determinate condizioni.
    """
    alphabet = list(string.ascii_uppercase)
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

def write_type_list(file_name="files_to_add/type_whitelist.txt"):
    """Funzione che si occupa della scrittura del file contenente tutti i tipi di entità ammessi, selezionati
        in base alla gerarchia di tipi in DBpedia

        Args:
            file_name: file in cui vanno scritti tutti i tipi ammessi
    """
    query = """
            select distinct ?Sub where {
                {
                    select distinct ?Type where 
                    {
                        ?Athing rdfs:subClassOf owl:Thing.
                        ?Type rdfs:subClassOf ?Athing.
                        ?SubType rdfs:subClassOf ?Type.
                    }
                GROUP BY ?Type
                HAVING(COUNT(?SubType)>1)
                }
            ?Sub rdfs:subClassOf ?Type.
            }
            """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)
    sparql.setQuery(query)
    temp_dict = sparql.query().convert()["results"]["bindings"]
    temp_dict_len = len(temp_dict)
    type_uris_results = [temp_dict[i]["Sub"]["value"] for i in range(0, temp_dict_len)]
    type_file = open(file_name, 'w', encoding="utf-8")
    
    for i in range(temp_dict_len):
        type_file.write(str(type_uris_results[i]) + "\n")

def get_type_whitelist(file_name="files_to_add/type_whitelist.txt"):
    """Si occupa di prendere da file la lista completa di tipi di entità da considerare.

    Args:
        file_name: file da cui prendere la lista di URI pari ai tipi di entità da considerare.
    Returns:
        types_list: lista di URI pari ai tipi di entità da considerare.
    """
    type_file = open(file_name, 'r', encoding="utf-8")
    types_read = type_file.read()
    types_list = types_read.split("\n")
    return types_list

def expand_entity_file_from_type_file(entity_file_name="files_to_add/entities_from_types.txt",
                                      type_file_name="files_to_add/type_whitelist.txt"):

    num_result_per_type = 10

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)

    type_file = open(type_file_name, 'r', encoding="utf-8")
    types_read = type_file.read()
    types_list = types_read.split("\n")
    entity_file = open(entity_file_name, 'w', encoding="utf-8")
    for specific_type in types_list:
        print("Current type:" + specific_type)
        query = """
                select distinct ?uri where {
                    ?uri rdf:type <"""+specific_type+""">
                }
                LIMIT """+str(num_result_per_type)+"""
                """
        sparql.setQuery(query)
        temp_dict = sparql.query().convert()["results"]["bindings"]
        temp_dict_len = len(temp_dict)
        entity_uris_results = [temp_dict[i]["uri"]["value"] for i in range(0, temp_dict_len)]
        for entity in entity_uris_results:
            entity_file.write(entity + "\n")





def get_type_blacklist(file_name="files_to_add/type_blacklist.txt"):
    """Si occupa di prendere da file la lista completa di tipi di entità da escludere.

    Args:
        file_name: file da cui prendere la lista di URI pari ai tipi di entità da escludere.
    Returns:
        types_list: lista di URI pari ai tipi di entità da escludere.
    """
    type_file = open(file_name, 'r', encoding="utf-8")
    types_read = type_file.read()
    types_list = types_read.split("\n")
    return types_list


def get_relation_whitelist(file_name="files_to_add/relations_new.txt"):
    """Si occupa di prendere da file la lista completa di relazioni da considerare.

    Args:
        file_name: file da cui prendere la lista di URI pari alle relazioni da considerare.
    Returns:
        relation_list: lista di URI pari alle relazioni da considerare.
    """
    relations_file = open(file_name, 'r', encoding="utf-8")
    relation_read = relations_file.read()
    relation_list = relation_read.split("\n")
    return relation_list


def remove_relation_from_whitelist(relation_name, file_name="files_to_add/relations_new.txt"):
    """Si occupa di eliminare dal file file_name l'URI relation_name

    Args:
        relation_name: URI della relazione da cancellare dal file file_name
        file_name: file da cui cancellare l'URI relation_name (se presente, altrimenti il file rimane invariato).
    """
    relations_file = open(file_name, 'r', encoding="utf-8")
    relation_read = relations_file.read()
    relation_list = relation_read.split("\n")
    relation_list.remove(relation_name)
    relations_file = open(file_name, 'w', encoding="utf-8")
    relation_list_len = len(relation_list)
    for i in range(relation_list_len):
        relations_file.write(str(relation_list[i]) + "\n")


def serialize_query_set(dict_to_serialize, file_name="files_to_add/generated_queries.txt"):
    """Si occupa di serializzare un dizionario all'interno del file file_name, utilizzando la sintassi JSON con
    una certa spaziatura ed indentazione.

    Args:
        dict_to_serialize: dizionario da serializzare su file file_name.
        file_name: file su cui va serializzato dict_to_serialize con sintassi JSON.
    """
    generated_file = open(file_name, 'a', encoding="utf-8")
    generated_file.close()
    generated_file = open(file_name, 'r', encoding="utf-8")
    raw_data = generated_file.read()
    #print(raw_data)
    if raw_data == "":
        data = []
    else:
        data = json.loads(raw_data, strict = "False")

    data.append(dict_to_serialize)
    to_serialize = data.copy()
    #print(str(data))
    generated_file.close()
    generated_file = open(file_name, 'w', encoding="utf-8")
    generated_file.write(json.dumps(to_serialize, indent = 4, sort_keys = True))
    generated_file.close()


def wipe_file_content(file_name):
    """Si occupa di eliminare tutto il contenuto di un file chiamato file_name

        Args:
            file_name: nome del file di cui si vuole eliminare il contenuto
    """
    file_to_wipe = open(file_name, 'w', encoding="utf-8")
    file_to_wipe.close()


def acquire_query_templates_list(file_name="files_to_add/templates_new.txt"):
    """Si occupa di acquisire la lista di dizionari contenenti le informazioni per ogni template da istanziare

            Args:
                file_name: nome del file in cui è contenuta la lista di dizionari di templates, il file deve rispettare
                il formato json
    """
    templates_file = open(file_name, "r", encoding="utf-8")
    data = json.load(templates_file, strict=False)
    templates_file.close()
    return data


def wipe_template_output_files(template_dir="files_to_add/templates_new.txt"):
    """Ogni dizionario relativo ad un template ha un campo che specifica il percorso del file in cui deve salvare
    i risultati di ogni istanza di quel template. Questa funzone si occupa di cancellare il contenuto di ogni file di
    output.

            Args:
                template_dir: nome del file contenente la lista di dizionari relativi ai templates, necessario
                per poter ottenere il percorso relativo ad ogni file di output, il cui contenuto va eliminato
    """
    template_list = acquire_query_templates_list(template_dir)
    for single_template in template_list:
        wipe_file_content(single_template["save_name"])

