import EntityHandler
from SPARQLWrapper import SPARQLWrapper, JSON
import random as rng
import language_tool_python
import FileHandler
import itertools
from RelationsConstraints import apply_constraint

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


"""def sparql_check_range(relation_uri, range_uri):"""


"""def apply_constraint(rel_list, constraint_value="num"):
    #Data una lista di uri corrispondenti a delle relazioni, chiamata rel_list, restituisce una nuova lista
    list_to_return contenente solo le relazioni di rel_list che rispettano un particolare vincolo specificato dalla
    stringa constraint_value

                Args:
                    rel_list: lista di cui si vuole conoscere quali sono le relazioni che rispettano il vincolo
                        espresso da constraint_value
                    constraint_value: stringa corrispondente ad un particolare vincolo su una relazione sparql,
                        i controlli sui vincoli fin ora possibili sono:
                        -"num", controlla se il range delle relazioni è "http://www.w3.org/2001/XMLSchema#double"
                        -"is _uri_", controlla se una relazione ha proprio uri pari ad _uri_
                Returns:
                    list_to_return: lista contenente solo le relazioni che rispettano il vincolo specificato da
                        contraint_value
    #
    list_to_return = rel_list.copy()
    if constraint_value == "num":
        for rel in rel_list:
            if not sparql_check_range(rel, "http://www.w3.org/2001/XMLSchema#double"):
                list_to_return.remove(rel)
    if constraint_value.split(" ")[0] == "is":
        for rel in rel_list:
            if rel != constraint_value.split(" ")[1]:
                list_to_return.remove(rel)
    return list_to_return"""


def generate_queries():
    """Si occupa di istanziare le query a partire dai templates contenuti nel file specificato.
        L'istanza di ogni query avviene nella seguente maniera:
        -si considera un template;
        -si considera la lista di tipi validi per una variabile di tipo;
        -per ciascuna variabile di tipo si considerano le entità appartenenti ai sottotipi del tipo specificato;
        -per ogni entità considerata si controlla se, tra le relazioni, esistono relazioni che rispettano i vincoli
        specificati per le variabili relative alle relazioni;
        -dopo aver ottenuto i tipi validi e le relazioni valide si sostituisce al posto delle variabili del template
        e si ottiene una istanza di query;
        -l'istanza di query viene serializzata assieme al result set ed ai valori di istanza all'interno del file
        di output specificato nel template.
    """
    templates_list = FileHandler.acquire_query_templates_list()
    for template_entry in templates_list:
        type_variables_dict = map_valid_types_to_entities(template_entry["valid_types"])
        list_of_lists = []
        for key in type_variables_dict.keys():
            list_of_lists.append(type_variables_dict.get(key))
        for entity_tuple in itertools.product(*list_of_lists):
            dict_to_instantiate = map_dict_keys_tuple(type_variables_dict.keys(), entity_tuple)
            #print("voglio istanziare: " + str(dict_to_instantiate))
            instantiate_single_query(dict_to_instantiate, template_entry)


def instantiate_single_query(entity_tuple, template_entry):
    """Si occuopa di generare le istanze di query valide per una particolare tupla di entità di tipo valido rispetto
    al template specificato.

                Args:
                    entity_tuple: dizionario avente per chiavi i nomi delle variabili di tipo e come valori le
                        entità valide associate;
                    template_entry: dizionario contenente le informazioni relative al template di cui si vogliono
                        generare le istanze.
    """
    dict_in_query = {}
    just_printed_flag = False
    for current_type_variable in entity_tuple.keys():
        considered_entity = EntityHandler.Entity(entity_tuple.get(current_type_variable))
        type_list_with_whitelisted = [x for x in considered_entity.type_list
                                      if x in EntityHandler.get_subclasses_of(
                template_entry["valid_types"][current_type_variable])]
        if len(type_list_with_whitelisted) != 0:
            rand_type_number = int(rng.random() * len(type_list_with_whitelisted))
            chosen_type = type_list_with_whitelisted[rand_type_number]
            dict_in_query.update({current_type_variable: chosen_type})
            relations_found = find_relations_with_constraints(considered_entity, template_entry)
            for relation_variable in relations_found.keys():
                for correct_relation in relations_found.get(relation_variable):
                    dict_in_query.update({relation_variable: correct_relation})
                    if try_to_print_query(dict_in_query, template_entry):
                        just_printed_flag = True

            if not just_printed_flag:
                try_to_print_query(dict_in_query, template_entry)


def try_to_print_query(dict_in_query, template_entry):
    """Si occupa di inserire sul file designato le istanze valide per il template scelto.
        Args:
            dict_in_query: dizionario avente per chiavi le variabili del template (relative a tipi e relazioni) e
                per valori i corrispondenti valori da inserire all'interno della query template e della NNQT
            template_entry: entry del dizionario contenente tutte le informazioni sul template corrente
        return:
            True se l'operazione è stata completata con successo, perché dict_in_query conteneva tutte le variabili
            necessarie, con i valori validi, False altrimenti
    """
    if len(dict_in_query.keys()) >= (
            len(template_entry["valid_types"].keys()) + len(template_entry["relation_constraints"].keys())):
        query = template_entry["template"] % dict_in_query
        NNQT = istantiate_NNQT(dict_in_query, template_entry)
        sparql = SPARQLWrapper("http://dbpedia.org/sparql")
        sparql.addExtraURITag("timeout", "30000")
        sparql.setReturnFormat(JSON)
        sparql.setQuery(query)
        result_set = sparql.query().convert()
        if len(result_set["results"]["bindings"]) == 0:
            return False
        print(query)
        dict_to_ser = {"istances":dict_in_query,"query": query, "result_set": result_set,
                       "NNQT_istance":NNQT}
        FileHandler.serialize_query_set(dict_to_ser, template_entry["save_name"])
        return True
    else:
        return False


def istantiate_NNQT(dict_in_query, template_entry):
    """Si occupa di effettuare l'istanza dell'NNQT presente in template_entry
        Args:
            dict_in_query: dizionario avente per chiavi le variabili del template (relative a tipi e relazioni) e
                per valori i corrispondenti valori da inserire all'interno della NNQT
        Returns:
             to_return: istanza di NNQT contenente i valori di dict_in_query
    """
    to_return = ""
    new_dict_to_use = {}
    for current_variable in dict_in_query.keys():
        uri_unsplitted = dict_in_query.get(current_variable)
        uri_splitted = uri_unsplitted.split("/")
        value_to_add = uri_splitted[len(uri_splitted)-1].lower()
        new_dict_to_use.update({current_variable: value_to_add})
    to_return = template_entry["NNQT"] % new_dict_to_use
    #to_return = correct_sentence(to_return) sta dando problemi con java, urge trovare un correttore migliore
    return to_return


def find_relations_with_constraints(considered_entity, template_entry):
    """Data una particolare entità considered_entity, restituisce un dizionario avvalorato con chiavi pari
    alle variabili relative alle relazioni del template template_entry e valori pari alle relazioni
    di considered_entity che rispettano i vincoli stabiliti nel template per quelle particolari variabili.

        Args:
            considered_entity: entità da considerare per poter ritrovare le relazioni che soddisfino i vincoli
            specificati in template_entry sulle variabili relative alle relazioni
            template_entry: dizionario relativo ad un template, contenente tutte le informazioni sullo stesso
        Returns:
            dict_to_return: dizionario contenente chiavi pari ai nomi delle variabili corrispondenti alle relazioni
            in template_entry e valori pari alle relazioni di considered_entity che soddisfano i vincoli specificati
    """
    dict_to_return = {}  # dizionario con chiavi = variabili corrispondenti alle relazioni e valori = liste di
    # relazioni che soddisfano i vincoli scelti
    dict_of_constraints = template_entry["relation_constraints"]
    for rel_variable in dict_of_constraints:
        valid_list = apply_constraint(considered_entity.relations_list, dict_of_constraints.get(rel_variable))
        if len(valid_list) != 0:
            dict_to_return.update({rel_variable: valid_list})
    return dict_to_return


def map_dict_to_subclasses(dict_to_map):
    """Sostituisce tutti i valori di dict_to_map con le sottoclassi dei valori, restituendo un nuovo dizionario
    e lasciando dict_to_map invariato

        Args:
            dict_to_map: dizionario in cui vanno sostituiti i valori con le liste di sottotipi di quei valori
        Returns:
            dict_to_return: dizionario contenente le stesse chiavi di dict_to_map e come valori liste di sottotipi
            dei valori di dict_to_map
    """
    dict_to_return = dict_to_map.copy()
    for key in dict_to_return.keys():
        dict_to_return.update({key: EntityHandler.get_subclasses_of(dict_to_map.get(key))})
    return dict_to_return


def map_dict_to_entities(dict_to_map):
    """dict_to_map è un dizionario che ha come chiavi delle stringhe e come valori delle liste di tipi di DBpedia.
    Questa funzione restituisce un nuovo dizionario dict_to_return, avente stesse chiavi di dict_to_map e come
    valori liste di entità di tipo corrispondente ai tipi specificati nei valori di dict_to_map

            Args:
                dict_to_map: dizionario in cui vanno sostituiti i valori con le liste di entità
            Returns:
                dict_to_return: dizionario contenente le stesse chiavi di dict_to_map e come valori liste di entità
    """
    dict_to_return = {}
    for key in dict_to_map.keys():
        entity_list_to_add = []
        for current_type in dict_to_map.get(key):
            uri = EntityHandler.get_entity_with_most_relations(current_type)
            if uri != "":
                entity_list_to_add.append(uri)      #se volessi scegliere un'entità diversa dal primo risultato,
                                                    #dovrei modificare questo
        dict_to_return.update({key: entity_list_to_add})
    return dict_to_return


def map_valid_types_to_entities(dict_to_map):
    """Prodotto di composizione funzionale tra map_dict_to_entities e map_dict_to_subclasses"""
    return map_dict_to_entities(map_dict_to_subclasses(dict_to_map))


def map_dict_keys_tuple(keys, some_tuple):
    """Genera un dizionario dict_to_return che ha gli i-esimi valori di keys e some_tuple come chiavi e valori,
    rispettivamente

        Args:
            keys: lista di chiavi da inserire nel dizionario
            some_tuple: lista di entità, l'i-esimo valore di some_tuple sarà il valore per l'i-esima chiave di keys
            per il dizionario dict_to_return
        Returns:
            dict_to_return: restituisce un dizionario avente come chiavi keys e come valori gli analoghi valori di
            some_tuple
    """
    dict_to_return = {}
    i = 0
    for key in keys:
        dict_to_return.update({key: some_tuple[i]})
        i += 1
    return dict_to_return



