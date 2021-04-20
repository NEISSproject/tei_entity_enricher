#!/usr/bin/env python
# coding: utf-8
# todo:
# - in Cache-Class: write check_json_structure()
# - use specific person, organization and place schemata
# - abstract hardcoded handling of lobid apis way to encode type information

# In[84]:

#imports

import sys
import os
import re
import json
import requests

# In[88]:

#classes

class Connector:
    def __init__(self, gnd = None, apiindex = 0, checkConnectivity = True, showPrintMessages = True):
        self.showPrintMessages = showPrintMessages
        print("initializing connector..") if self.showPrintMessages else print("")
        self.gnd = gnd #str or list
        self.apiindex = apiindex #int
        self.apilist = Filereader("apilist.json", "local", True).loadfile_json()
        if self.apilist is None:
            print("connector error: could not find apilist.json. using standard settings...") if self.showPrintMessages else print("")
            self.apilist = [
                {
                    "name": "culturegraph",
                    "baseUrl": "https://hub.culturegraph.org/entityfacts/{}",
                    "baseAliases": {"type": ["@type", "str"], "name": ["preferredName", "str"], "furtherNames": ["variantName", ["str"]], "sameAs": ["sameAs", [{"@id": "str"}]]},
                    "personAliases": {},
                    "placeAliases": {},
                    "organizationAliases": {}
                },
                {
                    "name": "lobid",
                    "baseUrl": "http://lobid.org/gnd/{}",
                    "baseAliases": {"type": ["type", ["str"]], "name": ["preferredName", "str"], "furtherNames": ["variantName", ["str"]], "sameAs": ["sameAs", [{"id": "str"}]]},
                    "personAliases": {},
                    "placeAliases": {},
                    "organizationAliases": {}
                }
            ] #list with dicts
            self.apiindex = 0
        self.checkConnectivity = checkConnectivity #boolean
        self.connectionEstablished = False #boolean
        self.remainingApisToCheck = [i for i,_ in enumerate(self.apilist)] #list with apiindex values
        #connectivity check
        if self.checkConnectivity == True:
            self.connectivityCheck_loop()
        else:
            print("connector: initialization has been done without connectivity check.") if self.showPrintMessages else print("")
    def connectivityCheck_single(self, indexToTest, gndToTest = "118540238"):
        #preset test gnd: Goethe
        testReturnObject = requests.get(self.apilist[indexToTest]["baseUrl"].format(gndToTest))
        if testReturnObject.status_code == 200:
            try:
                testReturnObject.json()
            except:
                return False
            return True
        else:
            return False
    def connectivityCheck_loop(self):
        if self.checkConnectivity == False:
            self.checkConnectivity == True
        if len(self.remainingApisToCheck) > 0:
            if self.connectivityCheck_single(self.remainingApisToCheck[0]) == True:
                print("connectivity check passed: connection to {} api established.".format(self.apilist[self.remainingApisToCheck[0]]["name"])) if self.showPrintMessages else print("")
                self.apiindex = self.remainingApisToCheck[0]
                self.remainingApisToCheck = [i for i,_ in enumerate(self.apilist)]
                self.connectionEstablished = True
            else:
                print("connectivity check: {} api is currently not responding as expected. checking for alternatives...".format(self.apilist[self.remainingApisToCheck[0]]["name"])) if self.showPrintMessages else print("")
                self.remainingApisToCheck.remove(self.remainingApisToCheck[0])
                self.connectivityCheck_loop()
        else:
            print("connectivity check error: none of the listed apis is responding as expected.") if self.showPrintMessages else print("")
    def print_complete_url(self, index = 0):
        #todo: mögliche manuell erzeugte self.apiindex-fehldefinition händeln?
        if self.gnd is not None:
            if type(self.gnd) == str:
                print("connector complete URL: {}".format(self.apilist[self.apiindex]["baseUrl"].format(self.gnd))) if self.showPrintMessages else print("")
            elif type(self.gnd) == list:
                print("connector complete URL of gnd number {} in passed gnd list: {}".format(index + 1, self.apilist[self.apiindex]["baseUrl"].format(self.gnd[index]))) if self.showPrintMessages else print("")
        else:
            print("connector error in print_complete_url(): no gnd number has been passed to connector object yet.") if self.showPrintMessages else print("")
    def return_complete_url(self, index = 0):
        #todo: mögliche manuell erzeugte self.apiindex-fehldefinition händeln?
        if self.gnd is not None:
            if type(self.gnd) == str:
                return self.apilist[self.apiindex]["baseUrl"].format(self.gnd)
            elif type(self.gnd) == list:
                return self.apilist[self.apiindex]["baseUrl"].format(self.gnd[index])
        else:
            print("connector error in return_complete_url(): no gnd number has been passed to connector object yet.") if self.showPrintMessages else print("")
    def get_gnd_data(self, dataSelection = None):
        if self.checkConnectivity == False:
            print("connector note: connections to apis have not been checked yet. to do so manually execute connectivityCheck_loop() method of the current connector object. continuing attempt to receive gnd data from {} api...".format(self.apilist[self.apiindex]["name"])) if self.showPrintMessages else print("")
        elif self.connectionEstablished == False:
            print("connectivity error: after connectivity check no connection could has been established to any of the available apis. gnd data queries can not be executed at the moment.") if self.showPrintMessages else print("")
            return None
        result = {}
        if type(self.gnd) == str:
            try:
                source = requests.get(self.return_complete_url())
                source.json()
            except:
                print("connectivity error in get_gnd_data() method: could not load resource from api as expected.") if self.showPrintMessages else print("")
                return None
            self.connectionEstablished = True
            result[self.gnd] = source.json() #returns dict
            source.close()
            print("connector.get_gnd_data() status: data for gnd {} received.".format(self.gnd)) if self.showPrintMessages else print("")
        elif type(self.gnd) == list:
            for index, gnd in enumerate(self.gnd):
                try:
                    source = requests.get(self.return_complete_url(index))
                    source.json()
                except:
                    print("connectivity error in get_gnd_data() method: could not load resource from api as expected.") if self.showPrintMessages else print("")
                    return None
                result[gnd] = source.json() #returns dict
                source.close()
                print("connector.get_gnd_data() status: gnd {} ({}) of {} processed".format(index + 1, gnd, len(self.gnd))) if self.showPrintMessages else print("")
            self.connectionEstablished = True
        #build new dict with selected values, which should be returned (base = all base aliases from apilist definition. list = select specific aliases from base set)
        def filterReceivedData(gnd, mode):
            if mode == "base":
                try:
                    filteredType = result[gnd][self.apilist[self.apiindex]["baseAliases"]["type"][0]]
                except KeyError:
                    filteredType = []
                    print("connector.get_gnd_data() filtering note: could not find type information for {} in raw data. continuing processing...".format(gnd))
                #note: here is an hardcorded handling of specific lobid api way to represent type information
                #todo: abstract it
                if type(filteredType) == list and len(filteredType) > 0:
                    if "Person" in filteredType:
                        filteredType = "person"
                try:
                    filteredName = result[gnd][self.apilist[self.apiindex]["baseAliases"]["name"][0]]
                except KeyError:
                    filteredName = []
                    print("connector.get_gnd_data() filtering note: could not find name information for {} in raw data. continuing processing...").format(gnd)
                try:
                    filteredFurtherNames = result[gnd][self.apilist[self.apiindex]["baseAliases"]["furtherNames"][0]]
                except KeyError:
                    filteredFurtherNames = []
                    print("connector.get_gnd_data() filtering note: could not find furtherNames information for {} in raw data. continuing processing...".format(gnd))
                try:
                    filteredSameAs = result[gnd][self.apilist[self.apiindex]["baseAliases"]["sameAs"][0]]
                except KeyError:
                    filteredSameAs = []
                    print("connector.get_gnd_data() filtering note: could not find sameAs information for {} in raw data. continuing processing...".format(gnd))
                return {"type": filteredType, "name": filteredName, "furtherNames": filteredFurtherNames, "sameAs": filteredSameAs}
            elif type(mode) == list:
                returnedDict = {}
                if "type" in mode:
                    try:
                        returnedDict["type"] = result[gnd][self.apilist[self.apiindex]["baseAliases"]["type"][0]]
                    except KeyError:
                        returnedDict["type"] = []
                        print("connector.get_gnd_data() filtering note: could not find type information for {} in raw data. continuing processing...".format(gnd))
                    #note: here is an hardcorded handling of specific lobid api way to represent type information
                    #todo: abstract it
                    if type(returnedDict["type"]) == list and len(returnedDict["type"]) > 0:
                        if "Person" in returnedDict["type"]:
                            returnedDict["type"] = "person"
                if "name" in mode:
                    try:
                        returnedDict["name"] = result[gnd][self.apilist[self.apiindex]["baseAliases"]["name"][0]]
                    except KeyError:
                        returnedDict["name"] = []
                        print("connector.get_gnd_data() filtering note: could not find name information for {} in raw data. continuing processing...".format(gnd))
                if "furtherNames" in mode:
                    try:
                        returnedDict["furtherNames"] = result[gnd][self.apilist[self.apiindex]["baseAliases"]["furtherNames"][0]]
                    except KeyError:
                        returnedDict["furtherNames"] = []
                        print("connector.get_gnd_data() filtering note: could not find furtherNames information for {} in raw data. continuing processing...".format(gnd))
                if "sameAs" in mode:
                    try:
                        returnedDict["sameAs"] = result[gnd][self.apilist[self.apiindex]["baseAliases"]["sameAs"][0]]
                    except KeyError:
                        returnedDict["sameAs"] = []
                        print("connector.get_gnd_data() filtering note: could not find sameAs information for {} in raw data. continuing processing...".format(gnd))
                return returnedDict
        if dataSelection is not None:
            if type(self.gnd) == str:
                newDict = {list(result.keys())[0]: filterReceivedData(self.gnd, dataSelection)}
            elif type(self.gnd) == list:
                newDict = {}
                for key in result:
                    newDict[key] = filterReceivedData(key, dataSelection)
            result = newDict
        return result

class Filereader:
    def __init__(self, filepath = None, origin = None, internalCall = False, showPrintMessages = True):
        self.filepath = filepath
        self.origin = origin
        self.internalCall = internalCall
        self.showPrintMessages = showPrintMessages

    def loadfile_json(self):
        if (self.origin == "local"):
            try:
                with open(self.filepath) as loaded_file:
                    if (os.stat(self.filepath).st_size == 0):
                        #check if file exists but is empty
                        imported_data = "empty"
                    else:
                        imported_data = json.load(loaded_file)
                return imported_data
            except FileNotFoundError:
                if (self.internalCall == False):
                    print("error: file not found") if self.showPrintMessages else print("")
                return None
        elif (self.origin == "web"):
            try:
                response = requests.get(self.filepath)
                imported_data = response.json()
                return imported_data
            except ValueError:
                print("error: file not found or bad format") if self.showPrintMessages else print("")
                return None
        else:
            print("internal error: Filereader.origin not defined") if self.showPrintMessages else print("")
            return False

    def loadfile_beacon(self):
        if (self.origin == "local"):
            try:
                with open(self.filepath) as loaded_file:
                    return loaded_file
            except FileNotFoundError:
                print("error: file not found") if self.showPrintMessages else print("")
                return None
        elif (self.origin == "web"):
            try:
                response = requests.get(self.filepath)
                loaded_file = response.text
                return loaded_file
            except:
                print("error: couldn't get data due to connection or filepath issue") if self.showPrintMessages else print("")
                return None
        else:
            print("internal error: Filereader.origin not defined") if self.showPrintMessages else print("")
            return False

class Cache:
    def __init__(self, data = None, showPrintMessages = True):
        self.data = data
        self.showPrintMessages = showPrintMessages

    def print_cache(self):
        print(self.data) if self.showPrintMessages else print("")

    #redundancy check, used to compare existing files with cache data concerning gnd number and a category value:
    #example: is a gnd or a name of self.data already present in a file?
    #function can also be used as search routine for values in self.data
    def check_for_redundancy(self, gnd, category, value):
        gnd_is_redundant = False
        value_is_redundant = False
        for key in self.data:
            if (key == gnd):
                gnd_is_redundant = True
            if (self.data[key][category] == value):
                value_is_redundant = True
        return gnd_is_redundant, value_is_redundant

    def check_json_structure(self, custom_test_schema=None):
        #todo: write it (check, if self.data corresponds to json-file schema or custom_test_schema)
        #input: dict
        #output: boolean
        if custom_test_schema is not None:
            pass
        else:
            pass
        #wip: just temporary return clause
        return True

    def check_beacon_prefix_statement(self):
        regex_prefix_line = re.compile("#PREFIX:\s+http:\/\/d-nb.info\/gnd\/")
        regex_meta_lines = re.compile("^#")
        found = False
        lines = self.data.split("\n")
        for line in lines:
            if (re.search(regex_meta_lines, line) != None):
                if (re.search(regex_prefix_line, line) != None):
                    found = True
            else:
                break
        return found

    def get_gndids_of_beacon_file(self):
        if (self.check_beacon_prefix_statement() == True):
            regex_gndid = re.compile("^.{9,10}(?=\|)")
            lines = self.data.split("\n")
            result_list = []
            for line in lines:
                if (re.search(regex_gndid, line) != None):
                    result_list.append(re.search(regex_gndid, line).group(0))
            print("in beacon found gndids: {}\ndata: {}".format(len(result_list), result_list)) if self.showPrintMessages else print("")
            return result_list
        else:
            print("error: loaded beacon-file doesn't refer to gnd data or is corrupted") if self.showPrintMessages else print("")
    def get_items_with_specific_value_in_a_category(self, category, value, mode = "dict"):
        #get filtered cache.data-version returned as a reduced dict or returned as a list of gnd numbers of entities, whose categorys value matches the filter value
        if mode == "dict":
            result = {}
            for gnd in self.data:
                if self.data[gnd][category] == value:
                    result[gnd] = self.data[gnd]
            return result
        elif mode == "list":
            result = []
            for gnd in self.data:
                if self.data[gnd][category] == value:
                    result.append(self.data[gnd])
            return result
        else:
            print("cache.get_items_with_specific_value_in_a_category() error: no valid mode parameter has been passed to function") if self.showPrintMessages else print("")
            return None
   
class Filewriter:
    def __init__(self, data = None, filepath = None, showPrintMessages = True):
        self.data = data
        self.filepath = filepath
        self.showPrintMessages = showPrintMessages

    def writefile(self, doIfFileExists = "cancel"):
        #local definitions for a sort of switch-statement, based on dict "doIfFileExists_switch"
        def doIfFileExists_cancel():
            print("file already exists: cancel writing process") if self.showPrintMessages else print("")
            return False
        def doIfFileExists_replace():
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("file already exists: file successfully overwritten") if self.showPrintMessages else print("")
            return True
        def doIfFileExists_merge():
            if (already_existing_file_cache.check_json_structure() == False):
                #if already existing file doesn't match json-schema, tested by check_json_structure(), then cancel writing process
                print("file already exists: couldn't merge files due to incompatibility issue") if self.showPrintMessages else print("")
                return False
            else:
                #if one of the new gnd-ids or name-strings exists also in the already existing file, then cancel writing process
                for key in self.data:
                    _x = already_existing_file_cache.check_for_redundancy(key, "name", self.data[key]["name"])
                    if (any(_x)):
                        print("file already exists: couldn't merge files due to redundancy issue") if self.showPrintMessages else print("")
                        return False
                #merge new data with data from the already existing file and overwrite it
                already_existing_file_cache.data.update(self.data)
                with open(self.filepath, "w") as file:
                    json.dump(already_existing_file_cache.data, file, indent="\t")
                print("file already exists: files successfully merged") if self.showPrintMessages else print("")
                return True
        doIfFileExists_switch = {
            "cancel": doIfFileExists_cancel,
            "replace": doIfFileExists_replace,
            "merge": doIfFileExists_merge
        }
        #check for existance of a file with the same name as self.filepath using an instance of Filereader
        already_existing_file = Filereader(self.filepath, "local", True)
        already_existing_file_cache = Cache(already_existing_file.loadfile_json())
        if (already_existing_file_cache.data == None):
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("new file {} successfully created".format(self.filepath)) if self.showPrintMessages else print("")
            return True
        elif (already_existing_file_cache.data == "empty"):
            with open(self.filepath, "w") as file:
                json.dump(self.data, file, indent="\t")
            print("file already exists, but was empty: file successfully written") if self.showPrintMessages else print("")
            return True
        elif (already_existing_file_cache.data == False):
            print("internal error: cancel writing process") if self.showPrintMessages else print("")
            return False
        else:
            #switch-statement depending on doIfFileExists-parameter, in case a file with the same name as self.filepath aleady exists and is not empty
            returnvalue = doIfFileExists_switch.get(doIfFileExists)()
            return returnvalue                  

# In[89]:
#test 1: connect to different apis and get gnd data from them for three gnd numbers, filtered and unfiltered
print("\n\n##############################\ntest 1\n##############################\n\n")

gndlist = ["118629662", "11855817X", "4015796-9"]

print("###############\n1. initializing Connectors\n###############\n\n")
con_culturegraph = Connector(gndlist, 0, False)
con_culturegraph.print_complete_url()
con_lobid = Connector(gndlist, 1, False)
con_lobid.print_complete_url()

print("\n\n###############\n2. get raw json data from api culturegraph\n###############\n\n")
con_culturegraph_rawdata = con_culturegraph.get_gnd_data()
print("raw json data from culturegraph api saved in a dict object with gnd numbers which serve as keys:")
print(con_culturegraph_rawdata)

print("\n\n###############\n3. get raw json data from api lobid\n###############\n\n")
con_lobid_rawdata = con_lobid.get_gnd_data()
print("raw json data from lobid api saved in a dict object with gnd numbers which serve as keys:")
print(con_lobid_rawdata)

print("\n\n###############\n4. get filtered json data (type and name) from api culturegraph\n###############\n\n")
con_culturegraph_justTypeAndName = con_culturegraph.get_gnd_data(["type", "name"])
print("filtered json data from culturegraph api saved in a dict object with gnd numbers which serve as keys:")
print(con_culturegraph_justTypeAndName)

print("\n\n###############\n4. get filtered json data (type and name) from api lobid\n###############\n\n")
con_lobid_justTypeAndName = con_lobid.get_gnd_data(["type", "name"])
print("filtered json data from lobid api saved in a dict object with gnd numbers which serve as keys:")
print(con_lobid_justTypeAndName)

# In[92]:
#test 2: write json-file (test cases are: "cancel", "replace", "merge", file with the same name doesn't exist, empty file with the same name exists)
print("\n\n##############################\ntest 2\n##############################\n\n")
dataobj = {"123456X": {"name": "Max Mustermann"}, "145757753": {"name": "Maria Musterfrau"}}
a = Filewriter(dataobj, "test2export.json")
print("data: {}\npath: {}".format(a.data, a.filepath))
a.writefile("merge")

# In[93]:
#test 3: get prefiltered gnd_data of multiple gnd-ids, from the result extract gnd data of persons and save them in file
print("\n\n##############################\ntest 3\n##############################\n\n")

#weber: 118629662
#goetze: 117759473
#johnson: 11855817X
#storni: 1112297561
#goslar(stadt): 4021643-3

gndids = ["118629662","117759473","11855817X","1112297561", "4021643-3"]
con = Connector(gndids)
result_data = con.get_gnd_data(["type", "name", "furtherNames"])
result_data_cache = Cache(result_data)
result_data_cache.print_cache()
persons = result_data_cache.get_items_with_specific_value_in_a_category("type", "person")
writer = Filewriter(persons, "test3export.json")
print("data: {}\npath: {}".format(writer.data, writer.filepath))
writer.writefile("replace")

# In[94]:
#test 4: get personnames for gnd-ids extracted from a BEACON-file out of the web (finished)
print("\n\n##############################\ntest 4\n##############################\n\n")

fr = Filereader("http://beacon.findbuch.de/downloads/zadik-beacon.txt", "web")
beacon_cache = Cache(fr.loadfile_beacon())
in_beacon_found_gndids = beacon_cache.get_gndids_of_beacon_file()
print("\nconnecting to GND-API to receive all information about the found gndids\n(just used 10 out of the found 333 for testing purposes)")
con = Connector(in_beacon_found_gndids[:10])
gnd_data = con.get_gnd_data(["type", "name"])
print("\ngot following data for the gndids from api:\n", gnd_data)
gnd_data_cache = Cache(gnd_data)
persons = gnd_data_cache.get_items_with_specific_value_in_a_category("type", "person")
print("\nfiltered persons out of the found data:\n", persons)
print("\nsaving result to file...")
wri = Filewriter(persons, "test4export.json")
print("data: {}\npath: {}".format(wri.data, wri.filepath))
wri.writefile("replace")