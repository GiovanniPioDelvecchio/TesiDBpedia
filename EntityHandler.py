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
    relations_in_white_list = []
    type_list = []

    def __init__(self, uri=FileHandler.get_uri_from_file('files_to_add\entities_new.txt')):
        """Costruttore della classe Entity.

        Costruisce un oggetto di classe Entity partendo da un URI.
        Args:
            uri: l'uri corrispondente all'entità in DBpedia di cui si vuole avere un oggetto, può essere scelto
            arbitrariamente da chi usa la classe, ma come default è stata impostata la scelta casuale di una
            delle entità di un file.
        """
        self.entity_URI = uri
        self.relations_list = self.__get_relations()
        self.relations_in_white_list = self.__get_relations_from_white_list()
        self.type_list = self.__get_types()

    def __get_relations(self):
        """Si occupa di avvalorare relations_list"""
        relation_name = "rel"
        query = """ SELECT DISTINCT ?""" + relation_name + """ WHERE {
                        <""" + self.entity_URI + """> ?rel ?obj  FILTER(!isLiteral(?obj))}"""
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)
        temp_dict = sparql.query().convert()["results"]["bindings"]
        list_to_return = [temp_dict[i][relation_name]["value"] for i in range(0, len(temp_dict))]
        return list_to_return

    def __get_relations_from_white_list(self):
        """Si occupa di calcolare l'intersezione fra le relazioni della whitelist e la lista di relazioni
        dell'entità. Tale intersezione viene considerata considerando prefisso http://dbpedia.org
        e suffisso pari a uno dei suffissi presenti nella whitelist di relazioni
        """
        relations_in_white_list = FileHandler.get_relation_whitelist()
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



