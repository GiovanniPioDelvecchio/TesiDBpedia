import EntityHandler
from SPARQLWrapper import SPARQLWrapper, JSON
import random as rng
import language_tool_python
import FileHandler


def correct_sentence(text):
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
    rand_relation_number = int(rng.random() * (len(starting_entity.relations_in_white_list)-1))
    type_list_without_blacklisted = [x for x in starting_entity.type_list if x not in FileHandler.get_type_blacklist()]
    rand_type_number = int(rng.random() * len(type_list_without_blacklisted))
    chosen_type = type_list_without_blacklisted[rand_type_number]
    #print(chosen_type)
    chosen_relation = starting_entity.relations_in_white_list[rand_relation_number]
    #print(chosen_relation)

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
    #print(instantiated_nnqt)

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

    dict_to_return = {"type": chosen_type, "relation" : chosen_relation, "instantiated_nnqt": instantiated_nnqt,
                      "result" : temp_dict}
    return dict_to_return

# print(correct_sentence("which are the artists that have more than 2 birthplace"))
