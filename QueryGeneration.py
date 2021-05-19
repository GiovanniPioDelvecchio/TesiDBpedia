import EntityHandler
from SPARQLWrapper import SPARQLWrapper, JSON
import random as rng
import language_tool_python
import FileHandler
import itertools


def correct_sentence(text):
    """Applica le correzioni del correttore language_tool_python alla stringa text

        Args:
            text: stringa da correggere
        Returns:
             my_new_text: stringa corretta
    """
    correct_string = text
    tool = language_tool_python.LanguageTool('en-US')
    matches = tool.check(text)

    my_mistakes = []
    my_corrections = []
    start_positions = []
    end_positions = []

    for rules in matches:
        if len(rules.replacements) > 0:
            start_positions.append(rules.offset)
            end_positions.append(rules.errorLength + rules.offset)
            my_mistakes.append(text[rules.offset:rules.errorLength + rules.offset])
            my_corrections.append(rules.replacements[0])

    my_new_text = list(text)

    for m in range(len(start_positions)):
        for i in range(len(text)):
            my_new_text[start_positions[m]] = my_corrections[m]
            if start_positions[m] < i < end_positions[m]:
                my_new_text[i] = ""

    my_new_text = "".join(my_new_text)
    return my_new_text


def generate_group_by_query(starting_entity):
    """Genera una query con modificatore "GROUP BY" partendo dall'entità starting_entity

        Args:
            starting_entity: entità di partenza da utilizzare per poter generare la query
        Returns:
             dict_to_return: dizionario contenente i campi:
                -type, ovvero il tipo dell'entità selezionato, da inserire nella query
                -relation, ovvero la relazione selezionata, da inserire nella query
                -formulated_query, ovvero il template SPARQL istanziato con i valori di type e relation
                -instantiated_nnqt, ovvero l'equivalente in linguaggio naturale della query SPARQL
                -result, ovvero il result set ottenuto dalla query
    """
    if len(starting_entity.relations_in_white_list) != 0:
        rand_relation_number = int(rng.random() * (len(starting_entity.relations_in_white_list) - 1))
        type_list_with_whitelisted = [x for x in starting_entity.type_list if x in FileHandler.get_type_whitelist()]
        rand_type_number = int(rng.random() * len(type_list_with_whitelisted))
        chosen_type = type_list_with_whitelisted[rand_type_number]
        # print(chosen_type)
        chosen_relation = starting_entity.relations_in_white_list[rand_relation_number]
        # print(chosen_relation)

        admitted_types = """http://dbpedia.org/ontology/FictionalCharacter
http://dbpedia.org/ontology/MusicalWork
http://dbpedia.org/ontology/WrittenWork"""
        admitted_list = admitted_types.split("\n")

        for current_admitted_type in admitted_list:
            if EntityHandler.sub_class_of(chosen_type, current_admitted_type):
                template = """
                                    SELECT DISTINCT ?subject COUNT(?object) as ?obj
                                    WHERE {
                                        ?subject a <%(type_to_insert)s>.
                                        ?subject <%(relation_to_insert)s> ?object
                                    }
                                    GROUP BY ?subject
                                    HAVING(COUNT(?object)>2)
                                    LIMIT 10
                                    """
                nnqt = "which are the %(type_to_insert)s that have more than 2 %(relation_to_insert)s"

                query = template % {"type_to_insert": chosen_type, "relation_to_insert": chosen_relation}
                nl_type = str(chosen_type.split("/")[len(chosen_type.split("/")) - 1]).lower() + "s"
                nl_rel = str(chosen_relation.split("/")[len(chosen_relation.split("/")) - 1]).lower()

                instantiated_nnqt = nnqt % {"type_to_insert": nl_type, "relation_to_insert": nl_rel}
                instantiated_nnqt = correct_sentence(instantiated_nnqt)
                # print(instantiated_nnqt)

                sparql = SPARQLWrapper("http://dbpedia.org/sparql")
                sparql.setReturnFormat(JSON)

                sparql.setQuery(query)  # the previous query as a literal string
                temp_dict = sparql.query().convert()
                """
                    DA FIXARE

                    if not temp_dict["results"]["bindings"]:
                    FileHandler.remove_relation_from_whitelist(chosen_relation)
                    modified_entity = EntityHandler.Entity(starting_entity.entity_URI)
                    generate_group_by_query(modified_entity)
                """

                dict_to_return = {"type": chosen_type, "relation": chosen_relation, "formulated_query": query,
                                  "instantiated_nnqt": instantiated_nnqt,
                                  "result": temp_dict}
                return dict_to_return
        return {}


def sparql_check_range(relation_uri, range_uri):

    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)
    #print(relation_uri)
    if relation_uri.split(":")[0] == "dbo":
        query = """ask where {""" + relation_uri + """ rdfs:range <"""+range_uri+""">}"""
    else:
        query = """ask where {<"""+relation_uri+"""> rdfs:range <"""+range_uri+""">}"""
    sparql.setQuery(query)
    #print(sparql.query().convert()["boolean"])
    return sparql.query().convert()["boolean"]


def apply_constraint(rel_list, constraint_value="num"):
    list_to_return = rel_list.copy()
    if constraint_value == "num":
        for rel in rel_list:
            if not sparql_check_range(rel, "http://www.w3.org/2001/XMLSchema#double"):
                list_to_return.remove(rel)
    if constraint_value.split(" ")[0] == "is":
        for rel in rel_list:
            if rel != constraint_value.split(" ")[1]:
                list_to_return.remove(rel)
    return list_to_return


def generate_queries():
    templates_list = FileHandler.acquire_query_templates_list()
    for template_entry in templates_list:
        type_variables_dict = map_valid_types_to_entities(template_entry["valid_types"])
        list_of_lists = []
        for key in type_variables_dict.keys():
            list_of_lists.append(type_variables_dict.get(key))
        for entity_tuple in itertools.product(*list_of_lists):
            dict_to_instantiate = map_dict_keys_tuple(type_variables_dict.keys(), entity_tuple)
            print(str(dict_to_instantiate))
            instantiate_single_query(dict_to_instantiate, template_entry)


def instantiate_single_query(entity_tuple, template_entry):
    dict_in_query = {}
    just_printed_flag = False
    for current_type_variable in entity_tuple.keys():
        considered_entity = EntityHandler.Entity(entity_tuple.get(current_type_variable))
        # ritrovamento di un tipo valido e di una relazione valida
        #type_list_with_whitelisted = [x for x in considered_entity.type_list if x in FileHandler.get_type_whitelist()]
        type_list_with_whitelisted = [x for x in considered_entity.type_list
                                      if x in EntityHandler.get_subclasses_of(
                                        template_entry["valid_types"][current_type_variable])]
        if len(type_list_with_whitelisted) != 0:
            rand_type_number = int(rng.random() * len(type_list_with_whitelisted))
            chosen_type = type_list_with_whitelisted[rand_type_number]  # non vanno più considerate le whitelists, bensì bisogna
            # considerare tutte le relazioni con prefisso dbo: che rispettino le prorpietà specificate
            relations_after_constraints = apply_constraint(considered_entity.relations_list,
                                                           template_entry["relation_constraints"])
            dict_in_query.update({current_type_variable:chosen_type})
            print(str(dict_in_query))
            for chosen_relation in relations_after_constraints:
                dict_in_query.update({"rel_to_insert":chosen_relation})
                if len(dict_in_query.keys()) > len(entity_tuple.keys()):
                    just_printed_flag = True
                    query = template_entry["template"] % dict_in_query
                    print(query)

            if len(dict_in_query.keys()) > len(entity_tuple.keys()) and (not just_printed_flag):
                query = template_entry["template"] % dict_in_query
                print(query)
            just_printed_flag = False





"""def generate_queries():
    templates_list = FileHandler.acquire_query_templates_list()
    for template_entry in templates_list:

        types_to_consider = EntityHandler.get_subclasses_of(template_entry["valid_types"])
        for chosen_type in types_to_consider:
            uris_to_use = EntityHandler.get_entities_of_type(chosen_type)
            if len(uris_to_use) != 0:
                instantiate_single_query(uris_to_use, template_entry)"""


"""def instantiate_single_query(uris_to_use, template_entry):
    considered_entity = EntityHandler.Entity(uris_to_use[0])
    # ritrovamento di un tipo valido e di una relazione valida
    type_list_with_whitelisted = [x for x in considered_entity.type_list if x in FileHandler.get_type_whitelist()]
    rand_type_number = int(rng.random() * len(type_list_with_whitelisted))
    chosen_type = type_list_with_whitelisted[rand_type_number]  # non vanno più considerate le whitelists, bensì bisogna
    # considerare tutte le relazioni con prefisso dbo: che rispettino le prorpietà specificate
    relations_after_constraints = apply_constraint(considered_entity.relations_list,
                                                   template_entry["relation_constraints"])
    print(relations_after_constraints)
    for chosen_relation in relations_after_constraints:
        # istanziamento delle query
        query = template_entry["template"] % {"type_to_insert": chosen_type, "rel_to_insert": chosen_relation}
        print(query)"""


def map_dict_to_subclasses(dict_to_map):
    dict_to_return = dict_to_map.copy()
    for key in dict_to_return.keys():
        dict_to_return.update({key:EntityHandler.get_subclasses_of(dict_to_map.get(key))})
    return dict_to_return


def map_dict_to_entities(dict_to_map):
    dict_to_return = {}
    for key in dict_to_map.keys():
        entity_list_to_add = []
        for current_type in dict_to_map.get(key):
            uris = EntityHandler.get_entities_of_type(current_type)
            if len(uris)!=0:
                entity_list_to_add.append(uris[0])
        dict_to_return.update({key:entity_list_to_add})
    return dict_to_return


def map_valid_types_to_entities(dict_to_map):
    return map_dict_to_entities(map_dict_to_subclasses(dict_to_map))


def enumerate_tuples(dict_to_map):
    list_of_lists = []
    for key in dict_to_map.keys():
        list_of_lists.append(dict_to_map.get(key))
    for element in itertools.product(*list_of_lists):
        print(element)


def map_dict_keys_tuple(keys, some_tuple):
    dict_to_return = {}
    i = 0
    for key in keys:
        dict_to_return.update({key:some_tuple[i]})
        i += 1
    return dict_to_return

#print(str(EntityHandler.Entity("http://dbpedia.org/resource/Love_Creek_(Rehoboth_Bay_tributary)").relations_list))

#print(str(apply_constraint(EntityHandler.Entity("http://dbpedia.org/resource/Love_Creek_(Rehoboth_Bay_tributary)").relations_list)))



"""temp_dict = map_dict_to_subclasses({"type_to_insert":"dbo:NaturalPlace", "type_2":"dbo:Person"})
print(str(map_dict_to_entities(temp_dict)))"""

"""some_dict = map_valid_types_to_entities({"type_to_insert":"dbo:NaturalPlace", "type_2":"dbo:Person"})
enumerate_tuples(some_dict)"""

#map_dict_keys_tuple(["ammaccabanane","qualcosa"],('http://dbpedia.org/resource/Love_Creek_(Rehoboth_Bay_tributary)', 'http://dbpedia.org/resource/A._A._Ewing'))

"""instantiate_single_query({'first_type': 'http://dbpedia.org/resource/1943:_The_Battle_of_Midway', 'second_type': 'http://dbpedia.org/resource/2014_Saint-Jean-sur-Richelieu_ramming_attack'},
                         {"template":"select distinct ?uri ?otherUri where {?uri a <%(first_type)s>.?otherUri a <%(second_type)s>.?uri <%(rel_to_insert)s> ?otherUri.}",
                          "valid_types":{"first_type":"dbo:Work", "second_type":"dbo:Person"},"relation_constraints":"is http://dbpedia.org/ontology/author"})"""
generate_queries()