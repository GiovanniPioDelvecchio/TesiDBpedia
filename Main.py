import EntityHandler
import QueryGeneration
import FileHandler


#"http://dbpedia.org/resource/Ubiale_Clanezzo" mostra un esempio di entità che non ha relazioni su cui effettuare
#aggregazioni, occorre stilare una whitelist di relazioni su cui è possibile aggregare, poi rifinire la whitelist
#di entità che rispettino anche questo criterio. Per ora le entità rispettano solo il criterio di avere più di
#2 tipi
#"http://dbpedia.org/resource/Quasieulia_jaliscana", con la relazione "Kingdom" mostra invece un esempio di query
#corretta che però ha result set vuoto
dict_to_serialize = {}
for i in range(0, 10):
    my_entity = EntityHandler.Entity(FileHandler.get_uri_from_file('files_to_add\entities_new.txt'))#uri="http://dbpedia.org/resource/Duck_Hunt")
    print("uri: " + my_entity.entity_URI)
    print("type list: " + str(my_entity.type_list))
    print("relations list: " + str(my_entity.relations_list))
    print("intersection with white list: " + str(my_entity.relations_in_white_list))
    # my_entity.get_objects(my_entity.relations_in_white_list[0])
    print(my_entity.type_list)
    #type_list_without_blacklisted = [x for x in my_entity.type_list if x not in FileHandler.get_type_blacklist()]
    #print(type_list_without_blacklisted)
    dict_to_serialize[i] = QueryGeneration.generate_group_by_query(my_entity)
FileHandler.serialize_query_set(dict_to_serialize)