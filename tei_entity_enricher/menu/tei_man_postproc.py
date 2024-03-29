import streamlit as st
import xml.etree.ElementTree as ET
import os
import traceback
from streamlit_ace import st_ace
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.tei_ner_writer_map as tnw_map
import tei_entity_enricher.menu.tei_ner_map as tnm_map
import tei_entity_enricher.util.tei_writer as tei_writer
from tei_entity_enricher.util.helper import local_save_path, makedir_if_necessary
from tei_entity_enricher.interface.postprocessing.io import FileReader, FileWriter
from tei_entity_enricher.util.exceptions import FileNotFound, BadFormat
import tei_entity_enricher.menu.link_sug_cat as sparql
import tei_entity_enricher.menu.ner_task_def as ner_task
from tei_entity_enricher.util.components import (
    editable_multi_column_table,
    small_file_selector,
)
from tei_entity_enricher.util.helper import (
    transform_arbitrary_text_to_markdown,
    transform_xml_to_markdown,
    get_listoutput,
    replace_empty_string,
    add_markdown_link_if_not_None,
    menu_TEI_reader_config,
    menu_TEI_read_mapping,
    menu_TEI_write_mapping,
)
from tei_entity_enricher.interface.postprocessing.identifier import Identifier


class TEIManPP:
    def __init__(self, show_menu=True, entity_library=None):
        self.tei_mm_edit_options = [
            "Loop over the predicted tags and possibly enrich them with a reference link",
            "Modify a TEI File directly",
        ]
        self.search_options = [
            f"By {menu_TEI_write_mapping}",
            f"By {menu_TEI_read_mapping}",
            "By self-defined Tag configuration",
        ]
        self.tmp_link_choose_option_gnd = "GND id"
        self.tmp_link_choose_option_wikidata = "Wikidata id"
        self.tmp_base_ls_search_type_options = ["without specified type"]
        self.tmp_conf_link_attr_name = "link_attribute_name"
        self.check_one_time_attributes()
        self.entity_library = entity_library  # get_entity_library()
        if show_menu:
            if "tmp_ace_key_counter" not in st.session_state:
                st.session_state.tmp_ace_key_counter = 0
            self.tr = tei_reader.TEIReader(show_menu=False)
            self.tnm = tnm_map.TEINERMap(show_menu=False)
            self.tnw = tnw_map.TEINERPredWriteMap(show_menu=False)
            self.sds = sparql.LinkSugCat(show_menu=False)
            self.ntd = ner_task.NERTaskDef(show_menu=False)
            self.manPostProc_config = self.load_manPostProc_config();
            if "tmp_link_attr" not in st.session_state or st.session_state.tmp_link_attr is None:
                st.session_state.tmp_link_attr=self.manPostProc_config[self.tmp_conf_link_attr_name]
            self.show()

    def check_one_time_attributes(self):
        if "tmp_save_message" in st.session_state and st.session_state.tmp_save_message is not None:
            self.tmp_save_message = st.session_state.tmp_save_message
            st.session_state.tmp_save_message = None
        else:
            self.tmp_save_message = None
            if "tmp_save_message" not in st.session_state:
                st.session_state.tmp_save_message = None

        if "tmp_warn_message" in st.session_state and st.session_state.tmp_warn_message is not None:
            self.tmp_warn_message = st.session_state.tmp_warn_message
            st.session_state.tmp_warn_message = None
        else:
            self.tmp_warn_message = None
            if "tmp_warn_message" not in st.session_state:
                st.session_state.tmp_warn_message = None

        if "tmp_reload_aggrids" in st.session_state and st.session_state.tmp_reload_aggrids == True:
            self.tmp_reload_aggrids = True
            st.session_state.tmp_reload_aggrids = False
        else:
            self.tmp_reload_aggrids = False

    def load_manPostProc_config(self) -> None:
        default_filepath = os.path.join(local_save_path, "config", "postprocessing", "manPostProc_config.json")
        fr = FileReader(
            filepath=default_filepath, origin="local", internal_call=True, show_printmessages=False
        )
        result = None
        try:
            result = fr.loadfile_json()
        except FileNotFound:
            try:
                makedir_if_necessary(os.path.dirname(default_filepath))
                FileWriter(
                    data={
                        self.tmp_conf_link_attr_name: "ref",
                    },
                    filepath=default_filepath,
                    show_printmessages=False,
                ).writefile_json()
            except:
                return f"load_manPostProc_config(): could not create default manPostProc config in config folder."
            result = fr.loadfile_json()
        except BadFormat:
            return f"load_manPostProc_config(): could not load manPostProc_config.json from config folder, no valid json format."
        return result

    def save_manPostProc_config(self,manPostProc_config):
        default_filepath = os.path.join(local_save_path, "config", "postprocessing", "manPostProc_config.json")
        try:
            makedir_if_necessary(os.path.dirname(default_filepath))
            FileWriter(
                data=manPostProc_config,
                filepath=default_filepath,
                show_printmessages=False,
            ).writefile_json(do_if_file_exists="replace")
        except:
            return f"save_manPostProc_config(): could not create save manPostProc config in config folder."


    def show_editable_attr_value_def(self, tagname, tagbegin):
        st.markdown("Editable Attributes and Values for current search result!")
        entry_dict = {"Attributes": [], "Values": []}
        if tagbegin.endswith("/>"):
            end = -2
        else:
            end = -1
        if " " in tagbegin:
            attr_list = tagbegin[tagbegin.find(" ") + 1 : end].split(" ")
            for element in attr_list:
                if "=" in element:
                    attr_value = element.split("=")
                    entry_dict["Attributes"].append(attr_value[0])
                    entry_dict["Values"].append(attr_value[1][1:-1])
        answer = editable_multi_column_table(
            entry_dict,
            "tmp_loop_attr_value" + st.session_state.tmp_teifile + str(st.session_state.tmp_current_loop_element),
            openentrys=20,
            reload=self.tmp_reload_aggrids,
        )
        new_tagbegin = "<" + tagname
        attrdict = {}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in attrdict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            attrdict[answer["Attributes"][i]] = answer["Values"][i]
            new_tagbegin = new_tagbegin + " " + answer["Attributes"][i] + '="' + answer["Values"][i] + '"'
        if end == -2:
            new_tagbegin = new_tagbegin + "/>"
        else:
            new_tagbegin = new_tagbegin + ">"
        return new_tagbegin

    def show_sd_search_attr_value_def(self, attr_value_dict, name):
        st.markdown("Define optionally attributes with values which have to be mandatory for the search!")
        entry_dict = {"Attributes": [], "Values": []}
        for key in attr_value_dict.keys():
            entry_dict["Attributes"].append(key)
            entry_dict["Values"].append(attr_value_dict[key])
        answer = editable_multi_column_table(entry_dict, "tnw_attr_value" + name, openentrys=20)
        returndict = {}
        for i in range(len(answer["Attributes"])):
            if answer["Attributes"][i] in returndict.keys():
                st.warning(f'Multiple definitions of the attribute {answer["Attributes"][i]} are not supported.')
            returndict[answer["Attributes"][i]] = answer["Values"][i]
        return returndict

    def add_suggestion_link_to_tag_entry(self, link_to_add, tag_entry, attr_name):
        if attr_name is None or attr_name=="":
            attr_name="ref"
        entry_dict = {}
        if tag_entry["tagbegin"].endswith("/>"):
            end = -2
        else:
            end = -1
        if " " in tag_entry["tagbegin"]:
            attr_list = tag_entry["tagbegin"][tag_entry["tagbegin"].find(" ") + 1 : end].split(" ")
            for element in attr_list:
                if "=" in element:
                    attr_value = element.split("=")
                    entry_dict[attr_value[0]] = attr_value[1][1:-1]
        entry_dict[attr_name] = link_to_add
        new_tagbegin = "<" + tag_entry["name"]
        for attr in entry_dict.keys():
            new_tagbegin = new_tagbegin + " " + attr + '="' + entry_dict[attr] + '"'
        if end == -2:
            new_tagbegin = new_tagbegin + "/>"
        else:
            new_tagbegin = new_tagbegin + ">"
        tag_entry["tagbegin"] = new_tagbegin
        st.session_state.tmp_reload_aggrids = True

    def get_id_and_link_to_link_choose_option(self,suggestion,link_choose_option):
        if link_choose_option==self.tmp_link_choose_option_wikidata:
            return [suggestion["wikidata_id"]],[replace_empty_string(add_markdown_link_if_not_None(suggestion["wikidata_id"],"https://www.wikidata.org/wiki/" + suggestion["wikidata_id"]))]
        elif link_choose_option==self.tmp_link_choose_option_gnd:
            return [suggestion["gnd_id"]],[replace_empty_string(add_markdown_link_if_not_None(suggestion["gnd_id"], "http://d-nb.info/gnd/" + suggestion["gnd_id"]))]
        elif link_choose_option in st.session_state.tmp_further_ids_config.keys() and link_choose_option in suggestion["furtherIds"].keys() and len(suggestion["furtherIds"][link_choose_option])>0:
            if "{}" in st.session_state.tmp_further_ids_config[link_choose_option][1]:
                return suggestion["furtherIds"][link_choose_option],[replace_empty_string(add_markdown_link_if_not_None(id,st.session_state.tmp_further_ids_config[link_choose_option][1].replace("{}",id))) for id in suggestion["furtherIds"][link_choose_option]]
            else:
                return suggestion["furtherIds"][link_choose_option],[replace_empty_string(id) for id in suggestion["furtherIds"][link_choose_option]]
        else:
            return [None],[replace_empty_string(add_markdown_link_if_not_None(None,None))]

    def get_link_to_id(self,data_id,link_choose_option):
        if link_choose_option==self.tmp_link_choose_option_wikidata:
            return "https://www.wikidata.org/wiki/" + data_id
        elif link_choose_option==self.tmp_link_choose_option_gnd:
            return "http://d-nb.info/gnd/" + data_id
        elif link_choose_option in st.session_state.tmp_further_ids_config.keys() and data_id is not None:
            if "{}" in st.session_state.tmp_further_ids_config[link_choose_option][1]:
                return st.session_state.tmp_further_ids_config[link_choose_option][1].replace("{}",data_id)
            else:
                return data_id
        else:
            return ""

    def tei_edit_specific_entity(self, tag_entry, tr, index):
        col1, col2 = st.columns(2)
        with col1:
            if "tmp_edit_del_tag" + str(index) not in st.session_state:
                st.session_state["tmp_edit_del_tag" + str(index)] = True if "delete" in tag_entry and tag_entry["delete"] else False
            st.checkbox(
                "Remove this tag from the TEI-File",
                # tag_entry["delete"],
                key="tmp_edit_del_tag" + str(index),
                value=tag_entry["delete"] if "delete" in tag_entry else False,
                help="Set this checkbox if you want to remove this tag from the TEI-File.",
            )
            tag_entry["delete"] = st.session_state["tmp_edit_del_tag" + str(index)]
            if tag_entry["delete"]:
                st.write("This tag will be removed when saving the current changes.")
            else:
                tag_entry["name"] = st.text_input(
                    "Editable Tag Name",
                    tag_entry["name"],
                    # key="tmp_edit_ent_name",
                    help="Here you can change the name of the tag.",
                )
                # old_tagbegin=tag_entry["tagbegin"]
                tag_entry["tagbegin"] = self.show_editable_attr_value_def(tag_entry["name"], tag_entry["tagbegin"])
                if "tagend" in tag_entry.keys():
                    tag_entry["tagend"] = "</" + tag_entry["name"] + ">"
                # if old_tagbegin != tag_entry["tagbegin"]:
                #    # unfortunately an necessary workaround because in an aggrid component you can not use a placeholder,
                #    # thus you can not easily replace the widget itself like in the workaround for the other widgets
                #    st.experimental_rerun()
        with col2:
            st.markdown("### Textcontent of the tag:")
            if "pure_tagcontent" in tag_entry.keys():
                st.markdown(
                    transform_arbitrary_text_to_markdown(tei_writer.parse_xml_to_text(tag_entry["pure_tagcontent"]))
                )
            st.markdown("### Full tag in xml:")
            st.markdown(transform_xml_to_markdown(tei_writer.get_full_xml_of_tree_content(tag_entry)))
            st.markdown("### Surrounding text in the TEI File:")
            st.write(
                self.get_surrounded_text(
                    st.session_state.tmp_matching_tag_list[st.session_state.tmp_current_loop_element - 1]["tag_id"],
                    250,
                    tr,
                )
            )
        if self.entity_library.data is None:
            st.info("If you want to do search for link suggestions you have to initialize an Entity Library at first.")
        elif "pure_tagcontent" in tag_entry.keys():
            st.markdown("### Search for link suggestions")
            input_tuple = tag_entry["pure_tagcontent"], ""
            link_identifier = Identifier(input=[input_tuple])
            search_type_list = []
            search_type_list.extend(self.tmp_base_ls_search_type_options)
            search_type_list.extend(list(self.sds.lscdict.keys()))

            def change_search_type():
                st.session_state.tmp_matching_tag_list[st.session_state.tmp_current_loop_element - 1][
                    "default_sparql_query"
                ] = st.session_state.tmp_ls_search_type_sel_box

            st.session_state.tmp_ls_search_type_sel_box = tag_entry["default_sparql_query"]

            st.selectbox(
                label="Link suggestion search type",
                options=search_type_list,
                key="tmp_ls_search_type_sel_box",
                help="Define a search type for which link suggestions should be done!",
                on_change=change_search_type,
            )
            col1, col2, col3, col4 = st.columns([0.25, 0.25, 0.25, 0.25])
            if "link_suggestions" not in tag_entry.keys() or len(tag_entry["link_suggestions"]) == 0:
                simple_search = True
            else:
                simple_search = False
            full_search = col1.button(
                "Additional web Search",
                key="tmp_ls_full_search",
                help="Searches for link suggestions in the currently loaded entity library and additionaly in the web (e.g. from wikidata).",
            )

            def change_search_string(index):
                if "link_suggestions" in st.session_state.tmp_matching_tag_list[index]:
                    del st.session_state.tmp_matching_tag_list[index]["link_suggestions"]

            col2.text_input(
                label="Link suggestion search string",
                key="tmp_ls_search_string" + str(index),
                value=tag_entry["pure_tagcontent"],
                on_change=change_search_string,
                args=(index,),
                help=f'You can insert an alternative search string for link suggestions to the entity {tag_entry["pure_tagcontent"]} here.',
            )
            input_tuple = (
                st.session_state["tmp_ls_search_string" + str(index)],
                st.session_state.tmp_ls_search_type_sel_box,
            )
            link_identifier.input = [input_tuple]
            if simple_search or full_search:
                result = link_identifier.suggest(
                    self.entity_library,
                    do_wikidata_query=full_search,
                    wikidata_filter_for_correct_type=(
                        not search_type_list.index(tag_entry["default_sparql_query"]) == 0
                    ),
                    entity_library_filter_for_correct_type=(
                        not search_type_list.index(tag_entry["default_sparql_query"]) == 0
                    ),
                )
                if input_tuple in result.keys():
                    tag_entry["link_suggestions"] = result[input_tuple]
                else:
                    tag_entry["link_suggestions"] = []
            if "link_suggestions" in tag_entry.keys():
                suggestion_id = 0
                if len(tag_entry["link_suggestions"]) > 0:
                    col3.selectbox(
                        label="Choose links from",
                        options=st.session_state.tmp_link_choose_options,
                        help='Define the source where links should be added from when pressing an "Add link"-Button',
                        key="tmp_link_choose_option",
                    )
                    def save_tmp_link_attr():
                        if st.session_state.tmp_link_attr is None or st.session_state.tmp_link_attr=="":
                            self.manPostProc_config[self.tmp_conf_link_attr_name]="ref"
                        else:
                            self.manPostProc_config[self.tmp_conf_link_attr_name]=st.session_state.tmp_link_attr
                        self.save_manPostProc_config(self.manPostProc_config)

                    col4.text_input(label="Link or key attribute name",
                        key="tmp_link_attr",
                        value=self.manPostProc_config[self.tmp_conf_link_attr_name],
                        on_change=save_tmp_link_attr,
                        help='You can insert here the name of the attribute which is used to insert the link or key of a suggestion to the current entity.',
                    )
                    scol1, scol2, scol3, scol4, scol5, scol6 = st.columns(6)
                    scol1.markdown("### Name")
                    scol2.markdown("### Further Names")
                    scol3.markdown("### Description")
                    scol4.markdown(f"### {st.session_state.tmp_link_choose_option}")
                    scol5.markdown("### Use Suggestion")
                    scol6.markdown("### Entity Library")
                    for suggestion in tag_entry["link_suggestions"]:
                        # workaround: new column definition because of unique row height
                        scol1, scol2, scol3, scol4, scol5, scol6 = st.columns(6)
                        scol1.markdown(replace_empty_string(suggestion["name"]))
                        if len(suggestion["furtherNames"]) > 10:
                            further_names = suggestion["furtherNames"][:10] + ["..."]
                        else:
                            further_names = suggestion["furtherNames"]
                        scol2.markdown(replace_empty_string(get_listoutput(further_names)))
                        scol3.markdown(replace_empty_string(suggestion["description"]))
                        id_list, data_link_list = self.get_id_and_link_to_link_choose_option(suggestion,st.session_state.tmp_link_choose_option)
                        if len(id_list)>1:
                            used_id=scol4.selectbox(label='Choose a link',options=id_list,key="tmp_sel_link_" + str(suggestion_id) + "_" + str(st.session_state.tmp_current_loop_element) + "_" + st.session_state.tmp_link_choose_option,help='Choose a link to specify which of the links should be used.')
                        else:
                            used_id=id_list[0]
                        chosen_link=self.get_link_to_id(used_id,st.session_state.tmp_link_choose_option)
                        scol4.markdown(get_listoutput(data_link_list))

                        suggestion_id += 1

                        def add_link_as_attribute(suggestion, tag_entry):
                            self.add_suggestion_link_to_tag_entry(suggestion, tag_entry, st.session_state.tmp_link_attr)

                        scol5.button(
                            "Add link as attribute",
                            key="tmp" + str(suggestion_id),
                            on_click=add_link_as_attribute,
                            args=(
                                chosen_link,
                                tag_entry,
                            ),
                        )


                        if "origin" in suggestion.keys() and suggestion["origin"]=="wd":
                            def add_entity_to_library(suggestion):
                                if "origin" in suggestion.keys():
                                    del suggestion["origin"]
                                entity_to_add = suggestion
                                if (
                                    "type" in entity_to_add.keys()
                                    and entity_to_add["type"] == self.tmp_base_ls_search_type_options[0]
                                ):
                                    entity_to_add["type"] = ""

                                ret_value = self.entity_library.add_entities([suggestion])
                                if isinstance(ret_value, str):
                                    st.session_state.tmp_warn_message = ret_value
                                else:
                                    self.entity_library.save_library()
                                    if "pp_ace_el_editor_content" in st.session_state:
                                        del st.session_state["pp_ace_el_editor_content"]
                                    st.session_state.pp_ace_key_counter += 1
                                    st.session_state.tmp_save_message = f'The entity "{replace_empty_string(suggestion["name"])}" was succesfully added to the currently initialized entity library.'

                            scol6.button(
                                "Add to Entity Library",
                                key="tmp_el_" + str(suggestion_id),
                                on_click=add_entity_to_library,
                                args=(suggestion,),
                            )
                        else:
                            scol6.write("From Entity Library")

                else:
                    st.write("No link suggestions found!")
        return tag_entry

    def load_tei_file_content(self,teipath):
        with open(file=teipath, mode="r", encoding="utf8") as f:
            tei = f.read()
        st.session_state.tmp_last_loaded_direct_tei = tei
        st.session_state.tmp_direct_change_teifile_save = teipath
        return tei

    def tei_edit_environment(self):
        def edit_choice_change():
            if "tmp_matching_tag_list" in st.session_state:
                del st.session_state["tmp_matching_tag_list"]
            st.session_state.tmp_reload_aggrids = True
            if "tmp_ace_el_editor_content" in st.session_state:
                del st.session_state["tmp_ace_el_editor_content"]
            st.session_state.tmp_ace_key_counter += 1
        st.radio(label="TEI File Edit options",options=self.tei_mm_edit_options,key="tmp_manual_edit_choice",on_change=edit_choice_change, help='Choose an option, how you will edit a TEI. Warning! If you change the edit option, you loose unsaved changes.')

        if self.tei_mm_edit_options.index(st.session_state.tmp_manual_edit_choice)==0:
            #st.write(f"Loop manually over the predicted tags defined by a {menu_TEI_write_mapping}.")
            # self.tei_man_pp_params.tmp_selected_tr_name =
            st.selectbox(
                label=f"Select a {menu_TEI_reader_config}!",
                options=list(self.tr.configdict.keys()),
                key="tmp_selected_tr_name",
            )
            selected_tr = self.tr.configdict[st.session_state.tmp_selected_tr_name]
            tag_list, sparqllist = self.define_search_criterion()
            # self.tei_man_pp_params.tmp_teifile =
        small_file_selector(
            label="Choose a TEI File:",
            key="tmp_teifile",
            help="Choose a TEI file for manually manipulating its tags.",
        )
        if self.tei_mm_edit_options.index(st.session_state.tmp_manual_edit_choice)==0:
            if st.button(
                "Search Matching Entities in TEI-File:",
                key="tmp_search_entities",
                help="Searches all entities in the currently chosen TEI-File with respect to the chosen search criterion.",
            ):
                if "tmp_teifile" in st.session_state and os.path.isfile(st.session_state.tmp_teifile):
                    for key in st.session_state:
                        if key.startswith("tmp_edit_del_tag"):
                            st.session_state[key] = False
                    try:
                        tei = tei_writer.TEI_Writer(st.session_state.tmp_teifile, tr=selected_tr)
                        st.session_state.tmp_current_search_text_tree = tei.get_text_tree()
                        st.session_state.tmp_matching_tag_list = tei.get_list_of_tags_matching_tag_list(tag_list, sparqllist)
                        st.session_state.tmp_tr_from_last_search = selected_tr
                        if "tmp_current_loop_element" in st.session_state:
                            del st.session_state["tmp_current_loop_element"]
                        if "tmp_loop_number_input" in st.session_state:
                            del st.session_state["tmp_loop_number_input"]
                        if len(st.session_state.tmp_matching_tag_list) > 0:
                            self.tmp_reload_aggrids = True
                            st.session_state.tmp_current_loop_element = 1
                            if len(st.session_state.tmp_matching_tag_list) > 1:
                                st.session_state.tmp_loop_number_input = 1
                                st.session_state.tmp_loop_rerun_after_search = 1
                            st.session_state.tmp_teifile_save = st.session_state.tmp_teifile
                            self.enrich_search_list(st.session_state.tmp_tr_from_last_search)
                            st.session_state.tmp_link_choose_options = [self.tmp_link_choose_option_gnd, self.tmp_link_choose_option_wikidata]
                            if self.entity_library.data is None:
                                st.session_state.tmp_further_ids_config={}
                            else:
                                st.session_state.tmp_further_ids_config=self.entity_library.load_furtherIds_config()
                                st.session_state.tmp_link_choose_options.extend(list(st.session_state.tmp_further_ids_config.keys()))
                            keys_to_delete=[]
                            for key in st.session_state:
                                if key.startswith("tmp_sel_link_"):
                                    keys_to_delete.append(key)
                            for key in keys_to_delete:
                                print("del", key)
                                del st.session_state[key]
                    except Exception as ex:
                        error_stack=' \n \n' + f'{repr(ex)}' + '\n \n' + "\n".join(traceback.TracebackException.from_exception(ex).format())
                        st.error(f'The Following error occurs, when trying to process TEI-File {st.session_state.tmp_teifile} : {error_stack}')


                else:
                    st.session_state.tmp_matching_tag_list = []
                    st.warning("Please select a TEI file to be searched for entities.")

            if "tmp_matching_tag_list" not in st.session_state:
                st.info("Use the search button to loop through a TEI file for the entities specified above.")
            elif len(st.session_state.tmp_matching_tag_list) < 1:
                st.warning("The last search resulted in no matching entities.")
            else:
                if len(st.session_state.tmp_matching_tag_list) == 1:
                    st.write("One tag in the TEI-File matches the search conditions.")
                else:

                    def loop_slider_change():
                        st.session_state.tmp_loop_number_input = st.session_state.tmp_current_loop_element
                        st.session_state.tmp_reload_aggrids = True

                    def loop_number_input_change():
                        st.session_state.tmp_current_loop_element = st.session_state.tmp_loop_number_input
                        st.session_state.tmp_reload_aggrids = True

                    st.slider(
                        label=f"Matching tags in the TEI file (found {str(len(st.session_state.tmp_matching_tag_list))} entries) ",
                        min_value=1,
                        max_value=len(st.session_state.tmp_matching_tag_list),
                        key="tmp_current_loop_element",
                        on_change=loop_slider_change,
                    )
                    st.number_input(
                        "Goto Search Result with Index:",
                        min_value=1,
                        max_value=len(st.session_state.tmp_matching_tag_list),
                        key="tmp_loop_number_input",
                        on_change=loop_number_input_change,
                    )
                    if (
                        "tmp_loop_rerun_after_search" in st.session_state
                        and st.session_state.tmp_loop_rerun_after_search == 1
                    ):
                        st.session_state.tmp_loop_rerun_after_search = 0
                        st.experimental_rerun()

                st.markdown("### Modify manually!")
                st.session_state.tmp_matching_tag_list[
                    st.session_state.tmp_current_loop_element - 1
                ] = self.tei_edit_specific_entity(
                    tag_entry=st.session_state.tmp_matching_tag_list[st.session_state.tmp_current_loop_element - 1],
                    tr=st.session_state.tmp_tr_from_last_search,
                    index=st.session_state.tmp_current_loop_element - 1,
                )
                st.markdown("### Save the changes!")
                if self.validate_manual_changes_before_saving(st.session_state.tmp_matching_tag_list):

                    def save_changes():
                        self.save_manual_changes_to_tei(
                            st.session_state.tmp_teifile,
                            st.session_state.tmp_teifile_save,
                            st.session_state.tmp_matching_tag_list,
                            st.session_state.tmp_tr_from_last_search,
                        )
                        del st.session_state["tmp_matching_tag_list"]
                        st.session_state.tmp_save_message = (
                            f"Changes successfully saved to {st.session_state.tmp_teifile_save}!"
                        )
                        st.session_state.tmp_reload_aggrids = True

                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        st.button(
                            "Save to",
                            key="tmp_edit_save_changes_button",
                            help="Save the current changes to the the specified path.",
                            on_click=save_changes,
                        )
                    with col2:
                        st.text_input(
                            "Path to save the changes to:",
                            key="tmp_teifile_save",
                            value=st.session_state.tmp_teifile,
                        )
        else:
            if "tmp_teifile" in st.session_state and os.path.isfile(st.session_state.tmp_teifile):
                editor_init_content = (
                    st.session_state.tmp_ace_el_editor_content
                    if "tmp_ace_el_editor_content" in st.session_state
                    else self.load_tei_file_content(st.session_state.tmp_teifile)
                )
                st.session_state.tmp_ace_el_editor_content = st_ace(
                    value=editor_init_content,
                    height=500,
                    language="xml",
                    readonly=False,
                    key="tmp_ace_internal_key" + str(st.session_state.tmp_ace_key_counter),
                )
                #if "tmp_ace_el_editor_content" not in st.session_state:
                #     st.session_state.tmp_ace_el_editor_content = editor_content
                st.markdown("### Save the changes!")
                if self.validate_direct_tei_changes(st.session_state.tmp_ace_el_editor_content):
                    st.info("Don't forget to press CTRL+ENTER to apply the last changes you made before saving!")
                    def save_changes():
                        with open(file=st.session_state.tmp_direct_change_teifile_save, mode="w", encoding="utf8") as file:
                            file.write(st.session_state.tmp_ace_el_editor_content)
                        if "tmp_ace_el_editor_content" in st.session_state:
                            del st.session_state["tmp_ace_el_editor_content"]
                        st.session_state.tmp_ace_key_counter += 1
                        st.session_state.tmp_save_message = (
                            f"Changes successfully saved to {st.session_state.tmp_direct_change_teifile_save}!"
                        )

                    col1, col2 = st.columns([0.1, 0.9])
                    with col1:
                        st.button(
                            "Save to",
                            key="tmp_direct_edit_save_changes_button",
                            help="Save the current changes to the the specified path.",
                            on_click=save_changes,
                        )
                    with col2:
                        st.text_input(
                            "Path to save the changes to:",
                            key="tmp_direct_change_teifile_save",
                            value=st.session_state.tmp_teifile,
                        )
            else:
                if "tmp_ace_el_editor_content" in st.session_state:
                    del st.session_state["tmp_ace_el_editor_content"]
                st.session_state.tmp_ace_key_counter += 1
                st.warning("Please select a TEI-File to directly modify it.")

        if self.tmp_save_message is not None:
            st.success(self.tmp_save_message)
        if self.tmp_warn_message is not None:
            st.warning(self.tmp_warn_message)

    def get_surrounded_text(self, id, sliding_window, tr):
        if (
            "pure_tagcontent"
            in st.session_state.tmp_matching_tag_list[st.session_state.tmp_current_loop_element - 1].keys()
        ):
            marked_text = tei_writer.parse_xml_to_text(
                tei_writer.get_pure_text_of_tree_element(
                    st.session_state.tmp_current_search_text_tree, tr, id_to_mark=id
                )
            )
            splitted_text = marked_text.split("<marked_id>")
            if len(splitted_text) <= 1 and tr[self.tr.tr_config_attr_use_notes]:
                # Is the entity possibly in a note?
                marked_text, marked = tei_writer.get_pure_note_text_of_tree_element(
                    st.session_state.tmp_current_search_text_tree, tr, id_to_mark=id
                )
                if not marked:
                    return ""
                splitted_text = marked_text.split("<marked_id>")
            before_text = splitted_text[0]
            splitted_second_text = splitted_text[1].split("</marked_id>")
            entity_text = splitted_second_text[0]
            after_text = splitted_second_text[1]
            if len(before_text) >= sliding_window:
                before_text = "..." + before_text[-sliding_window:]
            if len(after_text) >= sliding_window:
                after_text = after_text[:sliding_window] + "..."
            return before_text + "$\\text{\\textcolor{red}{" + entity_text + "}}$" + after_text
        return ""

    def get_sparql_list_to_entity_list(self, ntd_name, entity_list):
        sparqllist = []
        for entity in entity_list:
            if entity in self.ntd.defdict[ntd_name][self.ntd.ntd_attr_lsc_map].keys():
                sparqllist.append(self.ntd.defdict[ntd_name][self.ntd.ntd_attr_lsc_map][entity])
            else:
                sparqllist.append(self.tmp_base_ls_search_type_options[0])
        return sparqllist

    def define_search_criterion(self):
        col1, col2 = st.columns(2)
        with col1:
            st.radio(label="Search Options", options=self.search_options, key="tmp_search_options")
        with col2:
            if self.search_options.index(st.session_state.tmp_search_options) == 0:
                st.selectbox(
                    label=f"Select a {menu_TEI_write_mapping} as search criterion!",
                    options=list(self.tnw.mappingdict.keys()),
                    key="tmp_selected_tnw_name",
                )
                tag_list, entity_list = tei_writer.build_tag_list_from_entity_dict(
                    self.tnw.mappingdict[st.session_state.tmp_selected_tnw_name]["entity_dict"], "tnw"
                )
                sparqllist = self.get_sparql_list_to_entity_list(
                    self.tnw.mappingdict[st.session_state.tmp_selected_tnw_name][self.tnw.tnw_attr_ntd][
                        self.ntd.ntd_attr_name
                    ],
                    entity_list,
                )
            elif self.search_options.index(st.session_state.tmp_search_options) == 1:
                st.selectbox(
                    label=f"Select a {menu_TEI_read_mapping} as search criterion!",
                    options=list(self.tnm.mappingdict.keys()),
                    key="tmp_selected_tnm_name",
                )
                tag_list, entity_list = tei_writer.build_tag_list_from_entity_dict(
                    self.tnm.mappingdict[st.session_state.tmp_selected_tnm_name]["entity_dict"], "tnm"
                )
                sparqllist = self.get_sparql_list_to_entity_list(
                    self.tnm.mappingdict[st.session_state.tmp_selected_tnm_name][self.tnm.tnm_attr_ntd][
                        self.ntd.ntd_attr_name
                    ],
                    entity_list,
                )
            else:
                st.text_input(
                    label="Define a Tag as search criterion",
                    key="tmp_sd_search_tag",
                    help="Define a Tag as a search criterion!",
                )
                st.session_state.tmp_sd_search_tag_attr_dict = self.show_sd_search_attr_value_def(
                    st.session_state.tmp_sd_search_tag_attr_dict
                    if "tmp_sd_search_tag_attr_dict" in st.session_state
                    else {},
                    "tmp_sd_search_tag_attr_dict",
                )
                tag_list = [[st.session_state.tmp_sd_search_tag, st.session_state.tmp_sd_search_tag_attr_dict]]
                sparqllist = [self.tmp_base_ls_search_type_options[0]]
        return tag_list, sparqllist

    def enrich_search_list(self, tr):
        index = 0
        for tag in st.session_state.tmp_matching_tag_list:
            tag["delete"] = False
            if "tagcontent" in tag.keys():
                tag["pure_tagcontent"] = tei_writer.get_pure_text_of_tree_element(tag["tagcontent"], tr)
                st.session_state["tmp_ls_search_string" + str(index)] = tag["pure_tagcontent"]
            index += 1

    def validate_direct_tei_changes(self,current_editor_content):
        val=True
        if st.session_state.tmp_last_loaded_direct_tei==current_editor_content:
            val=False
            if st.session_state.tmp_save_message is None:
                st.warning("Currently there are no changes to save. Don't forget to press CTRL+ENTER to apply your changes!")
        else:
            try:
                ET.fromstring(current_editor_content)
            except ET.ParseError as e:
                val=False
                if st.session_state.tmp_save_message is None:
                    st.error(f"Save not allowed. Your Changes lead to an syntactically incorrect XML-File. See the following parsing error: {e}")
        return val

    def validate_manual_changes_before_saving(self, changed_tag_list):
        val = True
        search_result_number = 0
        for tag_entry in changed_tag_list:
            search_result_number += 1
            if "delete" not in tag_entry.keys() or not tag_entry["delete"]:
                if tag_entry["name"] is None or tag_entry["name"] == "":
                    val = False
                    if st.session_state.tmp_save_message is None:
                        st.error(
                            f"Save is not allowed. See search result {search_result_number}. A Tag Name is not allowed to be empty!"
                        )
                entry_dict = {}
                if tag_entry["tagbegin"].endswith("/>"):
                    end = -2
                else:
                    end = -1
                if " " in tag_entry["tagbegin"]:
                    attr_list = tag_entry["tagbegin"][tag_entry["tagbegin"].find(" ") + 1 : end].split(" ")
                    for element in attr_list:
                        if "=" in element:
                            attr_value = element.split("=")
                            entry_dict[attr_value[0]] = attr_value[1][1:-1]
                for attr in entry_dict.keys():
                    if attr is None or attr == "":
                        val = False
                        if st.session_state.tmp_save_message is None:
                            st.error(
                                f"Save is not allowed. See search result {search_result_number}. You cannot define a value ({entry_dict[attr]}) for an empty attribute name!"
                            )
                    if entry_dict[attr] is None or entry_dict[attr] == "":
                        val = False
                        if st.session_state.tmp_save_message is None:
                            st.error(
                                f"Save is not allowed. See search result {search_result_number}. You cannot define a attribute ({attr}) without a value!"
                            )
        return val

    def save_manual_changes_to_tei(self, loadpath, savepath, changed_tag_list, tr):
        tei = tei_writer.TEI_Writer(loadpath, tr=tr)
        tei.include_changes_of_tag_list(changed_tag_list)
        tei.write_back_to_file(savepath)

    def show(self):
        st.subheader("Manual TEI Postprocessing")
        man_tei = st.expander("Manual TEI Postprocessing", expanded=True)
        with man_tei:
            self.tei_edit_environment()


# test/0732_101175.xml
