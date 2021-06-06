from SPARQLWrapper import SPARQLWrapper, JSON
import FileHandler


"""Package rappresentante una entità di DBpedia.

L'obiettivo di questa classe è realizzare un'astrazione della generica entità di DBpedia.
Ciò è possibile tramite il costruttore, che ha come unico argomento l'uri a cui si riferisce l'entità.
Dati relativi a quell'entità sono ritrovati tramite query SPARQL e salvati come attributi di istanza.

Esempio tipico di utilizzo:

foo = Entity("http://dbpedia.org/resource/foo")
rel_list = foo.relations_list                       #considera la lista di relazioni di foo
obj = foo.get_objects(rel_list[0])                  #trova l'oggetto del predicato rel_list[0]
                                                    #che ha come soggetto foo
"""
class Entity:
    """Questa classe serve a rappresentare le entità in DBpedia.

    Attributi:
        entity_URI: l'effettivo URI dell'entità presente in DBpedia.
        relations_list: lista delle relazioni che hanno come soggetto entity_URI in DBpedia.
        relations_in_white_list: intersezione fra la lista di relazioni dell'entità e la lista di entità ammesse.
        type_list: lista dei tipi dell'entità.
    """

    entity_URI = ""
    relations_list = []
    type_list = []

    def __init__(self, uri):        #=FileHandler.get_uri_from_file('files_to_add\entities_new.txt')
        """Costruttore della classe Entity.

        Costruisce un oggetto di classe Entity partendo da un URI.
        Args:
            uri: l'uri corrispondente all'entità in DBpedia di cui si vuole avere un oggetto, può essere scelto
            arbitrariamente da chi usa la classe, ma come default è stata impostata la scelta casuale di una
            delle entità di un file.
        """
        self.entity_URI = uri
        self.relations_list = self.__get_relations()
        self.type_list = self.__get_types()

    def __get_relations(self):
        """Si occupa di avvalorare relations_list"""
        relation_name = "rel"
        query = """ SELECT DISTINCT ?""" + relation_name + """ WHERE {
                        <""" + self.entity_URI + """> ?""" + relation_name + """ ?obj.
                        filter(strstarts(str(?""" + relation_name + """), str(dbo:)))}""" #FILTER(!isLiteral(?obj))
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)
        temp_dict = sparql.query().convert()["results"]["bindings"]
        list_to_return = [temp_dict[i][relation_name]["value"] for i in range(0, len(temp_dict))]

        return list_to_return

    def __get_types(self):
        """Si occupa di avvalorare type_list"""
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
        sparql.setQuery(query)
        temp_dict = sparql.query().convert()["results"]["bindings"]
        type_list_to_return = [temp_dict[i][str_type]["value"] for i in range(0, len(temp_dict))]
        return type_list_to_return

    def get_objects(self, single_relation):
        """Ritrova gli oggetti della relazione single_relation, che ha come soggetto l'entità

        Args:
            single_relation: URI corrispondente ad una relazione contenuta in relations_list
        Returns:
            obj_list_to_return: lista di oggetti obj per cui la proprietà single_relation(self, obj) è vera
        """
        obj_name = "obj"
        query = """ SELECT DISTINCT ?""" + obj_name + """ WHERE {
                                <""" + self.entity_URI + """> <""" + single_relation + """> ?obj}"""
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)  # the previous query as a literal string
        temp_dict = sparql.query().convert()["results"]["bindings"]
        obj_list_to_return = [temp_dict[i][obj_name]["value"] for i in range(0, len(temp_dict))]
        return obj_list_to_return


def sub_class_of(first_uri, second_uri):
    """Restituisce True se first_uri è un discendente di second_uri nella gerarchia delle classi di DBpedia

            Args:
                fist_uri: uri di cui si vuole sapere se è discendente di second_uri
                second_uri: uri di cui si vuole sapere se è antenato di first_uri
            Returns:
                True se first_uri è discendente di second_uri nella gerarchia delle classi di DBpedia,
                False altrimenti
    """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)

    if first_uri != "http://www.w3.org/2002/07/owl#Thing":
        query_ask = """ask where { <""" + first_uri + """> rdfs:subClassOf <""" + second_uri + """>.}"""

        sparql.setQuery(query_ask)
        answer = sparql.query().convert()["boolean"]
        if (answer):
            return answer
        else:
            query_upper_class = """select distinct ?uri where {<""" + first_uri + """> rdfs:subClassOf ?uri}"""
            sparql.setQuery(query_upper_class)
            upper_class = sparql.query().convert()["results"]["bindings"][0]["uri"]["value"]
            return sub_class_of(upper_class, second_uri)
    else:
        return False


def get_entities_of_type(type_uri):
    """Restituisce una lista di entità di tipo type_uri

        Args:
            type_uri: uri corrispondente al tipo di entità da restituire
        Returns:
            result_set: lista di entità di tipo type_uri
    """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)
    query = """select distinct ?uri where {?uri rdf:type <"""+type_uri+""">} LIMIT 10"""
    sparql.setQuery(query)
    temp_dict = sparql.query().convert()["results"]["bindings"]
    temp_dict_len = len(temp_dict)
    result_set = [temp_dict[i]["uri"]["value"] for i in range(temp_dict_len)]
    return result_set

def get_entity_with_most_relations(type_uri):
    """Restituisce l'entità di tipo type_uri con il maggior numero di relazioni associate

        Args:
            type_uri: uri corrispondente al tipo di entità da restituire
        Returns:
            result: "" se non è stata trovata alcuna entità di tipo type_uri, altrimenti è l'entità di tipo
            type_uri con il maggior numero di relazioni associate
    """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)
    query = """select distinct ?uri count(?rel) as ?numrel where {?uri rdf:type <"""+type_uri+""">.
                ?uri ?rel ?obj.
                } ORDER BY DESC(?numrel) LIMIT 1"""
    sparql.setQuery(query)
    temp_dict = sparql.query().convert()["results"]["bindings"]
    temp_dict_len = len(temp_dict)
    result = ""
    if temp_dict_len > 0:
        result = temp_dict[0]["uri"]["value"]
    return result


def get_subclasses_of(type_uri):
    """Restituisce la lista di sottoclassi della classe type_uri

        Args:
            type_uri: uri corrispondente ad una classe di cui si vogliono conoscere le sottoclassi dirette
        Returns:
            result_set: lista di sottoclassi dirette di type_uri
    """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)
    if type_uri.split(":")[0] == "dbo":
        query = """select distinct ?uri where {?uri rdfs:subClassOf """+type_uri+"""}"""
    else:
        query = """select distinct ?uri where {?uri rdfs:subClassOf <"""+type_uri+""">}"""
    sparql.setQuery(query)
    temp_dict = sparql.query().convert()["results"]["bindings"]
    temp_dict_len = len(temp_dict)
    result_set = [temp_dict[i]["uri"]["value"] for i in range(temp_dict_len)]
    return result_set



