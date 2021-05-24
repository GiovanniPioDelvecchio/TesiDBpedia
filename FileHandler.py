import random as rng
from SPARQLWrapper import SPARQLWrapper, JSON
import string
import random as rng
import json

"""Package che si occupa di gestire i files utilizzati all'interno del progetto

L'obiettivo di questo package è esporre un'interfaccia con i files agli altri moduli, in modo
da non demandare ai singoli moduli l'accesso alle risorse esterne.
"""


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

