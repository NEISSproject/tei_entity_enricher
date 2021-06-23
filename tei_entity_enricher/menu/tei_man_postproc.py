import streamlit as st
import tei_entity_enricher.menu.tei_reader as tei_reader
import tei_entity_enricher.menu.tei_ner_writer_map as tnw_map
import tei_entity_enricher.menu.tei_ner_map as tnm_map
import tei_entity_enricher.util.tei_writer as tei_writer
from tei_entity_enricher.util.components import editable_multi_column_table, small_file_selector
from tei_entity_enricher.util.helper import (
    transform_arbitrary_text_to_markdown,
    transform_xml_to_markdown,
    get_listoutput,
    replace_empty_string,
    add_markdown_link_if_not_None,
    local_save_path,
)
from tei_entity_enricher.interface.postprocessing.identifier import Identifier

# from tei_entity_enricher.menu.tei_postprocessing import get_entity_library


class TEIManPP:
    def __init__(self, state, show_menu=True, entity_library=None):
        self.state = state
        self.search_options = [
            "By TEI NER Prediction Writer Mapping",
            "By TEI Read NER Entity Mapping",
            "By self-defined Tag configuration",
        ]
        self.tmp_link_choose_option_gnd = "GND id"
        self.tmp_link_choose_option_wikidata = "Wikidata id"
        self.tmp_link_choose_options = [self.tmp_link_choose_option_gnd, self.tmp_link_choose_option_wikidata]
        self.tmp_base_ls_search_type_options = ["without specified type"]
        self.entity_library = entity_library  # get_entity_library()
        if show_menu:
            self.tr = tei_reader.TEIReader(state, show_menu=False)
            self.tnm = tnm_map.TEINERMap(state, show_menu=False)
            self.tnw = tnw_map.TEINERPredWriteMap(state, show_menu=False)
            self.show()

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
        answer = editable_multi_column_table(entry_dict, None, openentrys=20)
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

    def add_suggestion_link_to_tag_entry(self, suggestion, tag_entry):
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
        if self.state.tmp_link_choose_option == self.tmp_link_choose_option_wikidata:
            link_to_add = "https://www.wikidata.org/wiki/" + suggestion["wikidata_id"]
        else:
            # default gnd
            link_to_add = "http://d-nb.info/gnd/" + suggestion["gnd_id"]
        entry_dict["ref"] = link_to_add
        new_tagbegin = "<" + tag_entry["name"]
        for attr in entry_dict.keys():
            new_tagbegin = new_tagbegin + " " + attr + '="' + entry_dict[attr] + '"'
        if end == -2:
            new_tagbegin = new_tagbegin + "/>"
        else:
            new_tagbegin = new_tagbegin + ">"
        tag_entry["tagbegin"] = new_tagbegin

    def tei_edit_specific_entity(self, tag_entry, tr):
        col1, col2 = st.beta_columns(2)
        with col1:
            tag_entry["delete"] = st.checkbox(
                "Remove this tag from the TEI-File",
                tag_entry["delete"],
                key="tmp_edit_del_tag",
                help="Set this checkbox if you want to remove this tag from the TEI-File.",
            )
            if tag_entry["delete"]:
                st.write("This tag will be removed when saving the current changes.")
            else:
                tag_entry["name"] = st.text_input(
                    "Editable Tag Name",
                    tag_entry["name"],
                    key="tmp_edit_ent_name",
                    help="Here you can change the name of the tag.",
                )
                tag_entry["tagbegin"] = self.show_editable_attr_value_def(tag_entry["name"], tag_entry["tagbegin"])
                if "tagend" in tag_entry.keys():
                    tag_entry["tagend"] = "</" + tag_entry["name"] + ">"
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
                    self.state.tmp_matching_tag_list[self.state.tmp_current_loop_element - 1]["tag_id"], 250, tr
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
            search_type_list.extend(link_identifier.entity_types)
            tag_entry["ls_search_type"] = st.selectbox(
                label="Link suggestion search type",
                options=search_type_list,
                index=search_type_list.index(tag_entry["ls_search_type"])
                if "ls_search_type" in tag_entry.keys()
                else 0,
                key="tmp_ls_search_type_sel_box",
                help="Define a search type for which link suggestions should be done!",
            )
            input_tuple = tag_entry["pure_tagcontent"], tag_entry["ls_search_type"]
            link_identifier.input = [input_tuple]
            # tag_entry["ls_search_type"] = st.text_input(
            #    "Link suggestion search type",
            #    tag_entry["ls_search_type"] if "ls_search_type" in tag_entry.keys() else tag_entry["name"],
            #    help="Define a search type for which link suggestions should be done!",
            # )
            col1, col2, col3 = st.beta_columns([0.25, 0.25, 0.5])
            #simple_search = col1.button(
            #    "Simple Search",
            #    key="tmp_ls_simple_search",
            #    help="Searches for link suggestions only in the currently loaded entity library.",
            #)
            if "link_suggestions" not in tag_entry.keys() or len(tag_entry["link_suggestions"])==0:
                simple_search=True
            else:
                simple_search=False
            full_search = col1.button(
                "Additional web Search",
                key="tmp_ls_full_search",
                help="Searches for link suggestions in the currently loaded entity library and additionaly in the web (e.g. from wikidata).",
            )
            if simple_search or full_search:
                result = link_identifier.suggest(
                    self.entity_library,
                    do_wikidata_query=full_search,
                    wikidata_filter_for_correct_type=(not search_type_list.index(tag_entry["ls_search_type"]) == 0),
                    entity_library_filter_for_correct_type=(not search_type_list.index(tag_entry["ls_search_type"]) == 0),
                )
                if input_tuple in result.keys():
                    tag_entry["link_suggestions"] = result[input_tuple]
                else:
                    tag_entry["link_suggestions"] = []
            if "link_suggestions" in tag_entry.keys():
                suggestion_id = 0
                if len(tag_entry["link_suggestions"]) > 0:
                    self.state.tmp_link_choose_option = col3.selectbox(
                        "Choose links from",
                        self.tmp_link_choose_options,
                        self.tmp_link_choose_options.index(self.state.tmp_link_choose_option)
                        if self.state.tmp_link_choose_option
                        else self.tmp_link_choose_options.index(self.tmp_link_choose_option_gnd),
                        help='Define the source where links should be added from when pressing an "Add link"-Button',
                    )
                    scol1, scol2, scol3, scol4, scol5, scol6 = st.beta_columns(6)
                    scol1.markdown("### Name")
                    scol2.markdown("### Further Names")
                    scol3.markdown("### Description")
                    scol4.markdown("### Wikidata_Id")
                    scol5.markdown("### GND_id")
                    scol6.markdown("### Use Suggestion")
                    for suggestion in tag_entry["link_suggestions"]:
                        # workaround: new column definition because of unique row height
                        scol1, scol2, scol3, scol4, scol5, scol6 = st.beta_columns(6)
                        scol1.markdown(replace_empty_string(suggestion["name"]))
                        scol2.markdown(replace_empty_string(get_listoutput(suggestion["furtherNames"])))
                        scol3.markdown(replace_empty_string(suggestion["description"]))
                        scol4.markdown(replace_empty_string(add_markdown_link_if_not_None(suggestion["wikidata_id"],"https://www.wikidata.org/wiki/"+suggestion["wikidata_id"])))
                        scol5.markdown(replace_empty_string(add_markdown_link_if_not_None(suggestion["gnd_id"],"http://d-nb.info/gnd/"+suggestion["gnd_id"])))
                        suggestion_id += 1
                        if scol6.button("Add link as ref attribute!", key="tmp" + str(suggestion_id)):
                            self.add_suggestion_link_to_tag_entry(suggestion, tag_entry)
                else:
                    st.write("No link suggestions found!")
        return tag_entry

    def tei_edit_environment(self):
        st.write("Loop manually over the predicted tags defined by a TEI NER Prediction Writer Mapping.")
        self.state.tmp_selected_tr_name = st.selectbox(
            "Select a TEI Reader Config!",
            list(self.tr.configdict.keys()),
            index=list(self.tr.configdict.keys()).index(self.state.tmp_selected_tr_name)
            if self.state.tmp_selected_tr_name
            else 0,
            key="tmp_sel_tr",
        )
        selected_tr = self.tr.configdict[self.state.tmp_selected_tr_name]
        tag_list = self.define_search_criterion()
        self.state.tmp_teifile = small_file_selector(
            self.state,
            label="Choose a TEI File:",
            value=self.state.tmp_teifile if self.state.tmp_teifile else local_save_path,
            key="tmp_choose_tei_file",
            help="Choose a TEI file for manually manipulating its tags.",
        )
        if st.button(
            "Search Matching Entities in TEI-File:",
            key="tmp_search_entities",
            help="Searches all entities in the currently chosen TEI-File with respect to the chosen search criterion.",
        ):
            self.state.tmp_last_save_path = None
            if self.state.tmp_teifile or self.state.tmp_open_teifile:
                tei = tei_writer.TEI_Writer(
                    self.state.tmp_teifile, openfile=self.state.tmp_open_teifile, tr=selected_tr
                )
                self.state.tmp_current_search_text_tree = tei.get_text_tree()
                self.state.tmp_matching_tag_list = tei.get_list_of_tags_matching_tag_list(tag_list)
                self.state.tmp_tr_from_last_search = selected_tr
                self.state.tmp_current_loop_element = 1
                if len(self.state.tmp_matching_tag_list) > 0:
                    self.state.tmp_teifile_save = self.state.tmp_teifile
                    self.enrich_search_list(self.state.tmp_tr_from_last_search)
                    if self.entity_library:
                        self.enrich_search_list_with_link_suggestions()
            else:
                self.state.avoid_rerun()
                self.state.tmp_matching_tag_list = []
                st.warning("Please select a TEI file to be searched for entities.")

        if self.state.tmp_last_save_path:
            st.success(f"Changes are succesfully saved to {self.state.tmp_last_save_path}")
        elif self.state.tmp_matching_tag_list is None:
            st.info("Use the search button to loop through a TEI file for the entities specified above.")
        elif len(self.state.tmp_matching_tag_list) < 1:
            st.warning("The last search resulted in no matching entities.")
        else:
            if len(self.state.tmp_matching_tag_list) == 1:
                st.write("One tag in the TEI-File matches the search conditions.")
            else:
                self.state.tmp_current_loop_element = st.slider(
                    f"Matching tags in the TEI file (found {str(len(self.state.tmp_matching_tag_list))} entries) ",
                    1,
                    len(self.state.tmp_matching_tag_list),
                    self.state.tmp_current_loop_element if self.state.tmp_current_loop_element else 1,
                    key="tmp_loop_slider",
                )
                self.state.tmp_current_loop_element = st.number_input(
                    "Goto Search Result with Index:",
                    1,
                    len(self.state.tmp_matching_tag_list),
                    self.state.tmp_current_loop_element,
                )
            st.markdown("### Modify manually!")
            self.state.tmp_matching_tag_list[self.state.tmp_current_loop_element - 1] = self.tei_edit_specific_entity(
                self.state.tmp_matching_tag_list[self.state.tmp_current_loop_element - 1],
                self.state.tmp_tr_from_last_search,
            )
            st.markdown("### Save the changes!")
            col1, col2 = st.beta_columns([0.1, 0.9])
            with col1:
                save_button_result = st.button(
                    "Save to",
                    key="tmp_edit_save_changes_button",
                    help="Save the current changes to the the specified path.",
                )
            with col2:
                self.state.tmp_teifile_save = st.text_input(
                    "Path to save the changes to:",
                    self.state.tmp_teifile_save or "",
                    key="tmp_tei_file_save",
                )
            if save_button_result:
                if self.validate_manual_changes_before_saving(self.state.tmp_matching_tag_list):
                    self.save_manual_changes_to_tei(
                        self.state.tmp_teifile,
                        self.state.tmp_teifile_save,
                        self.state.tmp_matching_tag_list,
                        self.state.tmp_tr_from_last_search,
                    )
                    self.state.tmp_matching_tag_list = None
                    self.state.tmp_last_save_path = self.state.tmp_teifile_save
                else:
                    self.state.avoid_rerun()
            # st.write(self.state.tmp_matching_tag_list[self.state.tmp_current_loop_element-1])

    def get_surrounded_text(self, id, sliding_window, tr):
        if "pure_tagcontent" in self.state.tmp_matching_tag_list[self.state.tmp_current_loop_element - 1].keys():
            marked_text = tei_writer.parse_xml_to_text(
                tei_writer.get_pure_text_of_tree_element(self.state.tmp_current_search_text_tree, tr, id_to_mark=id)
            )
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

    def define_search_criterion(self):
        col1, col2 = st.beta_columns(2)
        with col1:
            self.state.tmp_search_options = st.radio(
                "Search Options",
                self.search_options,
                self.search_options.index(self.state.tmp_search_options) if self.state.tmp_search_options else 0,
            )
        with col2:
            if self.search_options.index(self.state.tmp_search_options) == 0:
                self.state.tmp_selected_tnw_name = st.selectbox(
                    "Select a TEI NER Prediction Writer Mapping as search criterion!",
                    list(self.tnw.mappingdict.keys()),
                    index=list(self.tnw.mappingdict.keys()).index(self.state.tmp_selected_tnw_name)
                    if self.state.tmp_selected_tnw_name
                    else 0,
                    key="tmp_sel_tnw",
                )
                tag_list = tei_writer.build_tag_list_from_entity_dict(
                    self.tnw.mappingdict[self.state.tmp_selected_tnw_name]["entity_dict"], "tnw"
                )
            elif self.search_options.index(self.state.tmp_search_options) == 1:
                self.state.tmp_selected_tnm_name = st.selectbox(
                    "Select a TEI Read NER Entity Mapping as search criterion!",
                    list(self.tnm.mappingdict.keys()),
                    index=list(self.tnm.mappingdict.keys()).index(self.state.tmp_selected_tnm_name)
                    if self.state.tmp_selected_tnm_name
                    else 0,
                    key="tmp_sel_tnm",
                )
                tag_list = tei_writer.build_tag_list_from_entity_dict(
                    self.tnm.mappingdict[self.state.tmp_selected_tnm_name]["entity_dict"], "tnm"
                )
            else:
                self.state.tmp_sd_search_tag = st.text_input(
                    "Define a Tag as search criterion",
                    self.state.tmp_sd_search_tag or "",
                    key="tmp_sd_search_tag",
                    help="Define a Tag as a search criterion!",
                )
                self.state.tmp_sd_search_tag_attr_dict = self.show_sd_search_attr_value_def(
                    self.state.tmp_sd_search_tag_attr_dict if self.state.tmp_sd_search_tag_attr_dict else {},
                    "tmp_sd_search_tag_attr_dict",
                )
                tag_list = [[self.state.tmp_sd_search_tag, self.state.tmp_sd_search_tag_attr_dict]]
        return tag_list

    def enrich_search_list(self, tr):
        for tag in self.state.tmp_matching_tag_list:
            tag["delete"] = False
            if "tagcontent" in tag.keys():
                tag["pure_tagcontent"] = tei_writer.get_pure_text_of_tree_element(tag["tagcontent"], tr)

    def enrich_search_list_with_link_suggestions(self):
        entitylist = []
        # for tag in self.state.tmp_matching_tag_list:
        #    if "pure_tagcontent" in tag.keys():
        #        input_tuple=tag["pure_tagcontent"],"person"
        #        entitylist.append(input_tuple)
        # link_identifier=Identifier(input=entitylist)
        # result=link_identifier.suggest(self.entity_library)
        # cur_el_index=0
        # for tag in self.state.tmp_matching_tag_list:
        #    if "pure_tagcontent" in tag.keys():
        #        tag["link_suggestions"]=result[entitylist[cur_el_index]]
        #        cur_el_index+=1

    def validate_manual_changes_before_saving(self, changed_tag_list):
        val = True
        search_result_number = 0
        for tag_entry in changed_tag_list:
            search_result_number += 1
            if "delete" not in tag_entry.keys() or not tag_entry["delete"]:
                if tag_entry["name"] is None or tag_entry["name"] == "":
                    val = False
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
                        st.error(
                            f"Save is not allowed. See search result {search_result_number}. You cannot define a value ({entry_dict[attr]}) for an empty attribute name!"
                        )
                    if entry_dict[attr] is None or entry_dict[attr] == "":
                        val = False
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
        man_tei = st.beta_expander("Manual TEI Postprocessing", expanded=True)
        with man_tei:
            self.tei_edit_environment()


# test/0732_101175.xml
