from SPARQLWrapper import SPARQLWrapper, JSON
import datetime


def normalize_date_to_year(date_to_normalize):
    return datetime.date(date_to_normalize.year, 1, 1)


def normalize_date_to_month(date_to_normalize):
    return datetime.date(date_to_normalize.year, date_to_normalize.month, 1)


def get_used_type(string_of_type):
    if len(string_of_type.split("-")) > 1:
        return datetime
    else:
        return int


def handle_dates(domain_increment_string):
    list_to_return = []
    normalize_to_month_flag = False
    do_not_normalize_flag = False
    splitted = domain_increment_string.split("_")
    starting_date = datetime.datetime.strptime(splitted[0], "%Y-%m-%d").date()
    ending_date = datetime.datetime.strptime(splitted[1], "%Y-%m-%d").date()
    unprocessed_increment = splitted[2].split("-")
    processed_increment = datetime.timedelta(days=0)
    if int(unprocessed_increment[0]) != 0:
        processed_increment += datetime.timedelta(days=366 * int(unprocessed_increment[0]))
    if int(unprocessed_increment[1]) != 0:
        normalize_to_month_flag = True
        processed_increment += datetime.timedelta(days=31 * int(unprocessed_increment[1]))
    if int(unprocessed_increment[2]) != 0:
        processed_increment += datetime.timedelta(days=int(unprocessed_increment[2]))
        do_not_normalize_flag = True

    while starting_date < ending_date:
        if starting_date.month < 10:
            str_month = "0" + str(starting_date.month)
        else:
            str_month = str(starting_date.month)
        if starting_date.day < 10:
            str_day = "0" + str(starting_date.day)
        else:
            str_day = str(starting_date.day)

        list_to_return.append("\""+str(starting_date.year)+"-" +
                              str_month+"-" +
                              str_day+"\"^^xsd:date")
        starting_date += processed_increment
        if not do_not_normalize_flag:
            if normalize_to_month_flag:
                starting_date = normalize_date_to_month(starting_date)
            else:
                starting_date = normalize_date_to_year(starting_date)
    return list_to_return


def handle_ints(domain_increment_string):
    list_to_return = []
    splitted = domain_increment_string.split("_")
    starting_num = int(splitted[0])
    ending_num = int(splitted[1])
    increment = int(splitted[2])
    while starting_num <= ending_num:
        list_to_return.append(str(starting_num))
        starting_num += increment
    return list_to_return


def get_list_of_values_given_range_increment(domain_increment_string):
    list_to_return = []
    found_type = get_used_type(domain_increment_string)
    if found_type == datetime:
        list_to_return = handle_dates(domain_increment_string)
    elif found_type == int:
        list_to_return = handle_ints(domain_increment_string)
    return list_to_return


#print(handle_dates("1960-01-01_1980-01-01_2-0-0"))
#print(get_list_of_values_given_range_increment("1960-01-01_1980-01-01_0-1-4"))