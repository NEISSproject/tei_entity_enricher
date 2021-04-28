#!/usr/bin/env python
# coding: utf-8
# todo:
# - in Cache-Class: write check_json_structure()
# - use specific person, organization and place schemata
# - abstract hardcoded handling of lobid apis way to encode type information

import os

import requests

# classes
from tei_entity_enricher.interface.gnd.io import FileReader, FileWriter, Cache
from tei_entity_enricher.util.helper import module_path


# In[88]:


class Connector:
    def __init__(self, gnd = None, apiindex = 0, checkConnectivity = True, showPrintMessages = True):
        self.showPrintMessages = showPrintMessages
        print("initializing connector..") if self.showPrintMessages else print("")
        self.gnd = gnd #str or list
        self.apiindex = apiindex #int
        self.apilist = FileReader(os.path.join(module_path, "util/apilist.json"), "local", True).loadfile_json()
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

        if type(self.gnd) == str:
            print("connector complete URL: {}".format(self.apilist[self.apiindex]["baseUrl"].format(self.gnd))) if self.showPrintMessages else print("")
            return 0
        elif type(self.gnd) == list:
            print("connector complete URL of gnd number {} in passed gnd list: {}".format(index + 1, self.apilist[self.apiindex]["baseUrl"].format(self.gnd[index]))) if self.showPrintMessages else print("")
            return 0
        else:
            print("connector error in print_complete_url(): no gnd number has been passed to connector object yet.") if self.showPrintMessages else print("")
            return -1

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




   


# In[89]:
#test 1: connect to different apis and get gnd data from them for three gnd numbers, filtered and unfiltered

if __name__ == "__main__":
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
    a = FileWriter(dataobj, "test2export.json")
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
    writer = FileWriter(persons, "test3export.json")
    print("data: {}\npath: {}".format(writer.data, writer.filepath))
    writer.writefile("replace")

    # In[94]:
    #test 4: get personnames for gnd-ids extracted from a BEACON-file out of the web (finished)
    print("\n\n##############################\ntest 4\n##############################\n\n")

    fr = FileReader("http://beacon.findbuch.de/downloads/zadik-beacon.txt", "web")
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
    wri = FileWriter(persons, "test4export.json")
    print("data: {}\npath: {}".format(wri.data, wri.filepath))
    wri.writefile("replace")