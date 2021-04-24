from SPARQLWrapper import SPARQLWrapper, JSON
import random as rng
import FileHandler
import QueryGeneration


class Entity:
    entity_URI = ""
    relations_list = []
    relations_in_white_list = []
    type_list = []

    def __init__(self, uri=FileHandler.get_uri_from_file('..\entities_new.txt')):

        self.entity_URI = uri
        self.relations_list = self.__get_relations()
        self.relations_in_white_list = self.__get_relations_from_white_list()
        self.type_list = self.__get_types()

    def __get_relations(self):
        relation_name = "rel"
        query = """ SELECT DISTINCT ?""" + relation_name + """ WHERE {
                        <""" + self.entity_URI + """> ?rel ?obj  FILTER(!isLiteral(?obj))}"""
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setReturnFormat(JSON)

        sparql.setQuery(query)  # the previous query as a literal string
        temp_dict = sparql.query().convert()["results"]["bindings"]
        #print(len(temp_dict))
        list_to_return = [temp_dict[i][relation_name]["value"] for i in range(0, len(temp_dict))]
        return list_to_return

    def __get_relations_from_white_list(self):
        # leggi gli elementi dal file whitelist delle relazioni
        relations_in_white_list = FileHandler.get_relation_whitelist()#open('..\\relations.txt', 'r').read().split("\n")
        # crea lista intersezione fra whitelist e relazioni native del soggetto, considerando
        # solo i suffissi
        intersection = []
        for single_native_relation in self.relations_list:
            if single_native_relation.split("/")[2].startswith("dbpedia.org"):
                rel_split = single_native_relation.split("/")
                suffix = rel_split[len(rel_split) - 1]
                for wl_rel in relations_in_white_list:
                    if suffix in wl_rel:
                        if single_native_relation not in intersection:
                            intersection.append(single_native_relation)
        return intersection

    def __get_types(self):
        str_type = "t"
        query = """ 
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT DISTINCT ?""" + str_type + """ WHERE{<""" + self.entity_URI + """> rdf:type  ?""" + str_type + """
                FILTER (strstarts(str(?""" + str_type + """), str(dbo:)))}
                """
        # opzionalmente si potrebbero aggiungere anche i tipi che hanno come prefisso owl, concatenando
        # la condizione "|| strstarts(str(?""" + str_type + """), str(owl:))" a FILTER

        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setReturnFormat(JSON)

        sparql.setQuery(query)  # the previous query as a literal string
        temp_dict = sparql.query().convert()["results"]["bindings"]
        type_list_to_return = [temp_dict[i][str_type]["value"] for i in range(0, len(temp_dict))]
        return type_list_to_return

    def get_objects(self, single_relation):
        obj_name = "obj"
        query = """ SELECT DISTINCT ?""" + obj_name + """ WHERE {
                                <""" + self.entity_URI + """> <""" + single_relation + """> ?obj}"""
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setReturnFormat(JSON)

        sparql.setQuery(query)  # the previous query as a literal string
        temp_dict = sparql.query().convert()["results"]["bindings"]
        obj_list_to_return = [temp_dict[i][obj_name]["value"] for i in range(0, len(temp_dict))]
        return obj_list_to_return



