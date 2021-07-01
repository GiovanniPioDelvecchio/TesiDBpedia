import random as rng
from SPARQLWrapper import SPARQLWrapper, JSON
import string
import random as rng
import json
import os
import random as rng
import numpy as np

"""Package che si occupa di gestire i files utilizzati all'interno del progetto

L'obiettivo di questo package è esporre un'interfaccia con i files agli altri moduli, in modo
da non demandare ai singoli moduli l'accesso alle risorse esterne.
"""


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
    # print(raw_data)
    if raw_data == "":
        data = []
    else:
        data = json.loads(raw_data, strict="False")

    data.append(dict_to_serialize)
    to_serialize = data.copy()
    generated_file.close()
    generated_file = open(file_name, 'w', encoding="utf-8")
    generated_file.write(json.dumps(to_serialize, indent=4, sort_keys=True))
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


def acquire_file_name_number_queries(path_name="files_to_add/instances/"):
    """Si occupa di acquisire la lista di dizionari contenenti le query istanza e mostrare a video quante se ne hanno
    per ogni file

            Args:
                path_name: nome del percorso all'interno del quale si trovano i files con le istanze di query, di cui
                        si vuole sapere quante ce ne sono per ogni file.
    """
    dir_list = os.listdir(path_name)
    for current_dir in dir_list:
        queries_file = open(path_name + current_dir, "r", encoding="utf-8")
        data = json.load(queries_file, strict=False)
        queries_file.close()
        print(current_dir + " has " + str(len(data)) + " queries")


def get_n_percentage_of_all_queries(percentage=10, path_name="files_to_add/instances/", save_dir="chosen_queries.json"):
    dir_list = os.listdir(path_name)
    rng.seed(42)
    dict_to_serialize = {}
    temp_list = []
    for current_dir in dir_list:
        queries_file = open(path_name + current_dir, "r", encoding="utf-8")
        data = (json.load(queries_file, strict=False))["questions"]
        queries_file.close()
        indexes = (np.arange(0, len(data))).tolist()
        n_queries_percentage = int(percentage*len(data)/100)
        #print( current_dir + "  " + str(n_queries_percentage))
        print(current_dir + " " + str(len(data)))
        for i in range(0, n_queries_percentage):
            chosen_index, indexes = get_random_always_different(indexes)
            chosen_query = data[chosen_index]
            dict_to_add_in_list = {"id":chosen_query["id"], "id template":current_dir,
                                   "question":chosen_query["correct_NNQT_istance"],
                                   "query":chosen_query["query"], "result set":chosen_query["result_set"]}
            #print(dict_to_add_in_list["query"])
            #print(dict_to_add_in_list["query"].replace("\n", "").replace("\t",""))
            temp_list.append(dict_to_add_in_list)
    dict_to_serialize.update({"questions": temp_list})
    chosen_queries_file = open(save_dir, 'w', encoding="utf-8")
    chosen_queries_file.write(json.dumps(dict_to_serialize, indent=4, sort_keys=True))
    chosen_queries_file.close()


def get_random_always_different(list_where_choose):
    if len(list_where_choose)>0:
        index_to_return = int(rng.random() * len(list_where_choose))
        to_return = list_where_choose[index_to_return]
        list_where_choose.pop(index_to_return)
        return to_return, list_where_choose
    else:
        print("empty list")


def align_queries_to_MQALD_format(file_dir = "files_to_add/instances/places_with_highest_values.json", starting_id = 0):
    queries_file = open(file_dir, "r", encoding="utf-8")
    data = json.load(queries_file, strict=False)
    queries_file.close()
    dict_to_ser = {}
    temp_list = []
    for elem in data:
        elem.update({"id": starting_id})
        temp_list.append(elem)
        starting_id += 1
    dict_to_ser.update({"questions":temp_list})
    queries_file = open(file_dir, 'w', encoding="utf-8")
    queries_file.write(json.dumps(dict_to_ser, indent=4, sort_keys=True))
    queries_file.close()
    return starting_id


def align_all_to_MQALD(file_path = "files_to_add/instances/"):
    dir_list = os.listdir(file_path)
    print(dir_list)
    starting_id = 0
    for dir_name in dir_list:
        starting_id = align_queries_to_MQALD_format(file_path + dir_name, starting_id)
        print("done " + dir_name)




#align_queries_to_MQALD_format()
#align_all_to_MQALD()
get_n_percentage_of_all_queries()
