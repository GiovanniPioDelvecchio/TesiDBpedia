from SPARQLWrapper import SPARQLWrapper, JSON


def sparql_check_range(relation_uri, range_uri):
    """Controlla se una particolare relazione relation_uri ha range range_uri

            Args:
                relation_uri: relazione di cui si vuole sapere se il range è proprio range_uri
                range_uri: uri corrispondente ad un particolare tipo di entità, l'oggetto della relazione relation_uri
                    deve essere di tipo range_uri
            Returns:
                outcome: booleano vero se range_uri è il range della relazione relation_uri, falso altrimenti

    """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)
    # print(relation_uri)
    if relation_uri.split(":")[0] == "dbo":
        query = """ask where {""" + relation_uri + """ rdfs:range <""" + range_uri + """>}"""
    else:
        query = """ask where {<""" + relation_uri + """> rdfs:range <""" + range_uri + """>}"""
    sparql.setQuery(query)
    outcome = sparql.query().convert()["boolean"]
    return outcome


def sparql_check_subproperty(relation_uri, subproperty_uri):
    """Controlla se una particolare relazione relation_uri è sotto-proprietà di subproperty_uri

                Args:
                    relation_uri: relazione di cui si vuole sapere se la sottoproprietà è proprio subproperty_uri
                    subproperty_uri: uri corrispondente ad un particolare tipo di entità, la relazione relation_uri
                    deve essere una versione più specifica di questa relazione, dunque, deve essere una sotto-proprietà
                Returns:
                    outcome: booleano vero se relation_uri è sottoproprietà della relazione subproperty_uri,
                    falso altrimenti

        """
    sparql = SPARQLWrapper("http://dbpedia.org/sparql")
    sparql.addExtraURITag("timeout", "30000")
    sparql.setReturnFormat(JSON)
    # print(relation_uri)
    if relation_uri.split(":")[0] == "dbo":
        query = """ask where {""" + relation_uri + """ rdfs:subPropertyOf <""" + subproperty_uri + """>}"""
    else:
        query = """ask where {<""" + relation_uri + """> rdfs:subPropertyOf <""" + subproperty_uri + """>}"""
    sparql.setQuery(query)
    outcome = sparql.query().convert()["boolean"]
    return outcome


def apply_constraint(rel_list, constraint_value="num"):
    """Data una lista di uri corrispondenti a delle relazioni, chiamata rel_list, restituisce una nuova lista
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
    """
    list_to_return = rel_list.copy()
    if constraint_value == "num":
        for rel in rel_list:
            if not sparql_check_range(rel, "http://www.w3.org/2001/XMLSchema#double"):
                list_to_return.remove(rel)
    if constraint_value.split(" ")[0] == "is":
        for rel in rel_list:
            if rel != constraint_value.split(" ")[1]:
                list_to_return.remove(rel)
    if constraint_value == "hasLocation":
        for rel in rel_list:
            if not sparql_check_subproperty(rel, "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#hasLocation"):
                list_to_return.remove(rel)
    if constraint_value == "hasRole":
        for rel in rel_list:
            if not sparql_check_subproperty(rel, "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#sameSettingAs"):
                list_to_return.remove(rel)
    if constraint_value == "coparticipatesWith":
        for rel in rel_list:
            if not sparql_check_subproperty(rel, "http://www.ontologydesignpatterns.org/ont/dul/DUL.owl#coparticipatesWith"):
                list_to_return.remove(rel)
    if constraint_value == "date":
        for rel in rel_list:
            if not sparql_check_range(rel, "http://www.w3.org/2001/XMLSchema#date"):
                list_to_return.remove(rel)
    return list_to_return