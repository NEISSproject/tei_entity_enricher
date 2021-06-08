import os
from os.path import join


class TEI_Writer:
    def __init__(self, filename, openfile=None, tr=None, tnw=None):
        self._space_codes = ["&#x2008;", "&#xA0;"]
        if openfile is not None:
            tei = openfile.getvalue().decode("utf-8")
        else:
            with open(filename, "r") as f:
                tei = f.read()
        begintextindex = tei.find("<text ")
        begintextindex2 = tei.find("<text>")
        if begintextindex < 0:
            begintextindex = begintextindex2
        endtextindex = begintextindex + tei[begintextindex:].find(">")
        self._begin = tei[0 : endtextindex + 1]
        self._end = "</text>" + tei[tei.find("</text>") + 7 :]
        self._text = tei[endtextindex + 1 : tei.find("</text>")]
        self._build_text_tree()
        # Tree building has to be independent of the tei_reader_config tr and the Prediction Writer Mapping tnw!
        if tr is not None:
            self._use_notes = tr["use_notes"]
            if self._use_notes:
                self._note_tags = tr["note_tags"]
            else:
                self._note_tags = []
            self._exclude_tags = tr["exclude_tags"]
        if tnw is not None:
            self._write_entity_dict = tnw["entity_dict"]
            self._fixed_tags = tnw["fixed_tags"]

    def _get_tag_name(self, cur_tag_content):
        spaceindex = cur_tag_content.find(" ")
        if spaceindex > 0:
            return cur_tag_content[:spaceindex]
        return cur_tag_content

    def _getinnersametagindex(self, cur_text, tag_name):
        innersametagindex = cur_text.find("<" + tag_name + " ")
        innersametagindex2 = cur_text.find("<" + tag_name + ">")
        if innersametagindex < 0 or (innersametagindex2 >= 0 and innersametagindex2 < innersametagindex):
            innersametagindex = innersametagindex2
        # Check that it is not part of a comment
        commentbeginindex = cur_text.find("<!--")
        if commentbeginindex > 0 and commentbeginindex < innersametagindex:
            commentendindex = commentbeginindex + 4 + cur_text[commentbeginindex + 4 :].find("-->")
            if commentendindex > innersametagindex:
                newinnersametagindex = self._getinnersametagindex(cur_text[commentendindex + 2 :], tag_name)
                if newinnersametagindex > 0:
                    innersametagindex = commentendindex + 2 + newinnersametagindex
                else:
                    innersametagindex = newinnersametagindex
        if innersametagindex >= 0:
            innersametagstopindex = innersametagindex + cur_text[innersametagindex:].find(">")
            if cur_text[innersametagstopindex - 1] == "/":
                newinnersametagindex = self._getinnersametagindex(cur_text[innersametagstopindex:], tag_name)
                if newinnersametagindex > 0:
                    innersametagindex = innersametagstopindex + newinnersametagindex
                else:
                    innersametagindex = newinnersametagindex
        return innersametagindex

    def _find_endstartindex(self, cur_text, tag_name):
        endstartindex = cur_text.find("</" + tag_name + ">")
        if endstartindex < 0:
            return -1
        innersametagindex = self._getinnersametagindex(cur_text, tag_name)
        # Relevant if the same tag is nested
        if innersametagindex >= 0 and innersametagindex < endstartindex:
            newstartindex = (
                innersametagindex + 2 + self._find_endstartindex(cur_text[innersametagindex + 2 :], tag_name)
            )
            return newstartindex + 2 + self._find_endstartindex(cur_text[newstartindex + 2 :], tag_name)
        return endstartindex

    def _extract_next_tag(self, cur_text):
        beginstartindex = cur_text.find("<")
        if beginstartindex >= 0:
            beginstopindex = cur_text.find(">")
            if beginstopindex < beginstartindex:
                print("Error: CheckSyntax")
                raise ValueError
            tag_name = self._get_tag_name(cur_text[beginstartindex + 1 : beginstopindex])
            if tag_name == "!--":
                beginstopindex = cur_text.find("-->") + 2
            endstartindex = beginstopindex + self._find_endstartindex(cur_text[beginstopindex:], tag_name)
            if cur_text[beginstopindex - 1] == "/" or tag_name == "!--":
                return tag_name, beginstartindex, beginstopindex, -1, -1
            if endstartindex < beginstopindex:
                print("Error: CheckSyntax")
                raise ValueError
            endstopindex = endstartindex + len(tag_name) + 2
            return tag_name, beginstartindex, beginstopindex, endstartindex, endstopindex

        else:
            return None, 0, 0, 0, 0

    def _build_subtexttaglist(self, cur_text):
        tag_name, beginstartindex, beginstopindex, endstartindex, endstopindex = self._extract_next_tag(cur_text)
        if tag_name is not None:
            returnlist = []
            if beginstartindex > 0:
                returnlist.append(cur_text[:beginstartindex])
            tag_dict = {
                "name": tag_name,
                "tagbegin": cur_text[beginstartindex : beginstopindex + 1],
                "tag_id": str(self._max_id),
            }
            self._max_id += 1
            if endstartindex > 0:
                tag_dict["tagend"] = cur_text[endstartindex : endstopindex + 1]
                if beginstopindex + 1 < endstartindex:
                    tag_dict["tagcontent"] = self._build_subtexttaglist(cur_text[beginstopindex + 1 : endstartindex])
                returnlist.append(tag_dict)
                if endstopindex + 1 < len(cur_text):
                    returnlist.append(self._build_subtexttaglist(cur_text[endstopindex + 1 :]))
            elif beginstopindex + 1 < len(cur_text):
                returnlist.append(tag_dict)
                returnlist.append(self._build_subtexttaglist(cur_text[beginstopindex + 1 :]))
            else:
                returnlist.append(tag_dict)
            return returnlist
        else:
            return cur_text

    def _build_text_tree(self):
        self._max_id = 0
        self._text_tree = self._build_subtexttaglist(self._text)

    def _get_full_xml_of_tree_content(self, cur_element):
        if isinstance(cur_element, dict):
            text = cur_element["tagbegin"]
            if "tagcontent" in cur_element.keys():
                text += self._get_full_xml_of_tree_content(cur_element["tagcontent"])
            if "tagend" in cur_element.keys():
                text += cur_element["tagend"]
            return text
        elif isinstance(cur_element, list):
            text = ""
            for element in cur_element:
                text = text + self._get_full_xml_of_tree_content(element)
            return text
        elif isinstance(cur_element, str):
            return cur_element

    def refresh_text_by_tree(self):
        self._text = self._get_full_xml_of_tree_content(self._text_tree)

    def get_tei_file_string(self):
        return self._begin + self._text + self._end

    def write_back_to_file(self, outputpath):
        self.refresh_text_by_tree()
        with open(outputpath, "w") as file:
            file.write(self.get_tei_file_string())

    def _merge_tags_to_insert(self, ins_tag, textstring):
        merged_tags = []
        last_tag = {"tag": "X", "begin": 0, "end": 0, "note":False}
        for tag in ins_tag:
            if "begin" in tag.keys():
                if last_tag["tag"] == tag["tag"] and last_tag["note"] == tag["note"] and (
                    last_tag["end"] == tag["begin"]
                    or (last_tag["end"] + 1 == tag["begin"] and textstring[last_tag["end"]] in (" ", "-"))
                ):
                    if "end" in tag.keys():
                        last_tag["end"] = tag["end"]
                    else:
                        del last_tag["end"]
                else:
                    if last_tag["tag"] != "X":
                        merged_tags.append(last_tag)
                    last_tag = tag
            else:
                last_tag = tag
        if last_tag["tag"] != "X":
            merged_tags.append(last_tag)
        return merged_tags

    def _get_new_tagged_string(self, tag, string_to_tag, with_begin=True, with_end=True):
        if tag in self._write_entity_dict.keys():
            new_tagged_string = "<" + self._write_entity_dict[tag][0]
            attr_string = " "
            for attr in self._write_entity_dict[tag][1].keys():
                attr_string += attr + '="' + self._write_entity_dict[tag][1][attr] + '" '
            attr_string = attr_string[:-1]
            if with_begin:
                new_tagged_string = new_tagged_string + attr_string + ">" + string_to_tag
            else:
                new_tagged_string = string_to_tag
            if with_end:
                new_tagged_string = new_tagged_string + "</" + self._write_entity_dict[tag][0] + ">"
        return new_tagged_string

    def _write_textstring(self, textstring, predicted_data, already_tagged, predicted_note_data, is_note):
        if "Harold Stassen" in textstring:
            print("Hier")
        if textstring is not None and textstring != "":
            ins_tag = []
            ignore_char_until = 0
            for i in range(len(textstring)):
                if i < ignore_char_until:
                    continue
                if is_note:
                    if self._notecontentindex < len(predicted_note_data) and len(self._cur_note_word) > len(
                        predicted_note_data[self._notecontentindex][self._notewordindex][0]
                    ):
                        print("Error: Predicted note data doesn't match TEI-File!")
                        raise ValueError
                    if textstring[i] == "&":  # Special handling for html unicode characters
                        unicode_end_index = textstring[i:].find(";")
                        ignore_char_until = i + unicode_end_index + 1
                        if textstring[i:ignore_char_until] not in self._space_codes:
                            self._cur_pred_note_index += 1
                            self._cur_note_word = (
                                self._cur_note_word + self._cur_pred_note_word[len(self._cur_note_word)]
                            )
                    elif textstring[i] == self._cur_pred_note_word[self._cur_pred_note_index]:
                        self._cur_pred_note_index += 1
                        self._cur_note_word = self._cur_note_word + textstring[i]
                    elif i > 0 and self._cur_pred_note_index > 0:
                        print("Error: Predicted note data doesn't match TEI-File!")
                        raise ValueError
                    if self._cur_note_word == self._cur_pred_note_word:
                        if (
                            already_tagged == False
                            and predicted_note_data[self._notecontentindex][self._notewordindex][1] != "O"
                        ):
                            if i - len(self._cur_pred_note_word) + 1 >= 0:
                                ins_tag.append(
                                    {
                                        "tag": predicted_note_data[self._notecontentindex][self._notewordindex][1],
                                        "begin": i - len(self._cur_pred_note_word) + 1,
                                        "end": i + 1,
                                        "note": True,
                                    }
                                )
                            else:
                                ins_tag.append(
                                    {
                                        "tag": predicted_note_data[self._notecontentindex][self._notewordindex][1],
                                        "end": i + 1,
                                        "note": True,
                                    }
                                )
                        if len(predicted_note_data[self._notecontentindex]) - 1 > self._notewordindex:
                            self._notewordindex += 1
                        else:
                            self._notewordindex = 0
                            self._notecontentindex += 1
                        self._cur_note_word = ""
                        if len(predicted_note_data) > self._notecontentindex:
                            self._cur_pred_note_word = predicted_note_data[self._notecontentindex][self._notewordindex][
                                0
                            ]
                        self._cur_pred_note_index = 0
                else:
                    if self._contentindex < len(predicted_data) and len(self._cur_word) > len(
                        predicted_data[self._contentindex][self._wordindex][0]
                    ):
                        print("Error: Predicted data doesn't match TEI-File!")
                        raise ValueError

                    if textstring[i] == "&":  # Special handling for html unicode characters
                        unicode_end_index = textstring[i:].find(";")
                        ignore_char_until = i + unicode_end_index + 1
                        if textstring[i:ignore_char_until] not in self._space_codes:
                            self._cur_pred_index += 1
                            self._cur_word = self._cur_word + self._cur_pred_word[len(self._cur_word)]
                    elif textstring[i] == self._cur_pred_word[self._cur_pred_index]:
                        self._cur_pred_index += 1
                        self._cur_word = self._cur_word + textstring[i]
                    elif i > 0 and self._cur_pred_index > 0:
                        print("Error: Predicted data doesn't match TEI-File!")
                        raise ValueError
                    if self._cur_word == self._cur_pred_word:
                        if already_tagged == False and predicted_data[self._contentindex][self._wordindex][1] != "O":
                            if i - len(self._cur_pred_word) + 1 >= 0:
                                ins_tag.append(
                                    {
                                        "tag": predicted_data[self._contentindex][self._wordindex][1],
                                        "begin": i - len(self._cur_pred_word) + 1,
                                        "end": i + 1,
                                        "note": False,
                                    }
                                )
                            else:
                                ins_tag.append(
                                    {
                                        "tag": predicted_data[self._contentindex][self._wordindex][1],
                                        "end": i + 1,
                                        "note": False,
                                    }
                                )

                        if len(predicted_data[self._contentindex]) - 1 > self._wordindex:
                            self._wordindex += 1
                        else:
                            self._wordindex = 0
                            self._contentindex += 1
                        self._cur_word = ""
                        if len(predicted_data) > self._contentindex:
                            self._cur_pred_word = predicted_data[self._contentindex][self._wordindex][0]
                        self._cur_pred_index = 0

        if len(self._cur_word) > 0:
            if already_tagged == False and predicted_data[self._contentindex][self._wordindex][1] != "O" and i - len(self._cur_pred_word) + 1 >=0:
                ins_tag.append(
                    {
                        "tag": predicted_data[self._contentindex][self._wordindex][1],
                        "begin": i - len(self._cur_word) + 1,
                        "note": False,
                    }
                )
        if len(self._cur_note_word) > 0:
            if already_tagged == False and predicted_note_data[self._notecontentindex][self._notewordindex][1] != "O"  and i - len(self._cur_pred_note_word) + 1 >=0:
                ins_tag.append(
                    {
                        "tag": predicted_note_data[self._notecontentindex][self._notewordindex][1],
                        "begin": i - len(self._cur_note_word) + 1,
                        "note": True,
                    }
                )
        if len(ins_tag) > 0:
            addindex = 0
            ins_tag = self._merge_tags_to_insert(ins_tag, textstring)
            for tag in ins_tag:
                if "begin" in tag.keys():
                    if "end" in tag.keys():
                        string_to_tag = textstring[tag["begin"] + addindex : tag["end"] + addindex]
                        new_tagged_string = self._get_new_tagged_string(tag["tag"], string_to_tag)
                        textstring = (
                            textstring[: tag["begin"] + addindex]
                            + new_tagged_string
                            + textstring[tag["end"] + addindex :]
                        )
                    else:
                        string_to_tag = textstring[tag["begin"] + addindex :]
                        new_tagged_string = self._get_new_tagged_string(tag["tag"], string_to_tag, with_end=False)
                        textstring = textstring[: tag["begin"] + addindex] + new_tagged_string
                else:
                    if "end" in tag.keys():
                        string_to_tag = textstring[: tag["end"] + addindex]
                        new_tagged_string = self._get_new_tagged_string(tag["tag"], string_to_tag, with_begin=False)
                        textstring = new_tagged_string + textstring[tag["end"] + addindex :]
                    else:
                        string_to_tag = textstring
                        new_tagged_string = self._get_new_tagged_string(
                            tag["tag"], string_to_tag, with_begin=False, with_end=False
                        )
                        textstring = new_tagged_string
                addindex = addindex + len(new_tagged_string) - len(string_to_tag)
        return textstring

    def _write_only_notes_in_contentlist(
        self, contentlist, predicted_data, already_tagged, predicted_note_data, is_note
    ):
        for contentindex in range(len(contentlist)):
            if isinstance(contentlist[contentindex], list):
                contentlist[contentindex] = self._write_only_notes_in_contentlist(
                    contentlist[contentindex], predicted_data, already_tagged, predicted_note_data, is_note
                )
            elif isinstance(contentlist[contentindex], dict):
                if (
                    contentlist[contentindex]["name"] in self._note_tags
                    and "tagcontent" in contentlist[contentindex].keys()
                ):
                    contentlist[contentindex] = self._write_tag_dict(
                        contentlist[contentindex], predicted_data, already_tagged, predicted_note_data, True
                    )
        return contentlist

    def _write_tag_dict(self, tag_dict, predicted_data, already_tagged, predicted_note_data, is_note):
        if tag_dict["name"] in self._note_tags and self._use_notes:
            is_note = True
        if tag_dict["name"] in self._exclude_tags or (self._use_notes == False and tag_dict["name"] in self._note_tags):
            return tag_dict
        else:
            if tag_dict["name"] in self._fixed_tags:
                tagged = True
            else:
                tagged = already_tagged
            if "tagcontent" in tag_dict.keys():
                if isinstance(tag_dict["tagcontent"], list):
                    tag_dict["tagcontent"] = self._write_contentlist(
                        tag_dict["tagcontent"], predicted_data, tagged, predicted_note_data, is_note
                    )
                elif isinstance(tag_dict["tagcontent"], dict):
                    tag_dict["tagcontent"] = self._write_tag_dict(
                        tag_dict["tagcontent"], predicted_data, tagged, predicted_note_data, is_note
                    )
                elif isinstance(tag_dict["tagcontent"], str):
                    tag_dict["tagcontent"] = self._write_textstring(
                        tag_dict["tagcontent"], predicted_data, tagged, predicted_note_data, is_note
                    )
        return tag_dict

    def _write_contentlist(self, contentlist, predicted_data, already_tagged, predicted_note_data, is_note):
        for contentindex in range(len(contentlist)):
            if isinstance(contentlist[contentindex], list):
                contentlist[contentindex] = self._write_contentlist(
                    contentlist[contentindex], predicted_data, already_tagged, predicted_note_data, is_note
                )
            elif isinstance(contentlist[contentindex], dict):
                contentlist[contentindex] = self._write_tag_dict(
                    contentlist[contentindex], predicted_data, already_tagged, predicted_note_data, is_note
                )
            elif isinstance(contentlist[contentindex], str):
                contentlist[contentindex] = self._write_textstring(
                    contentlist[contentindex], predicted_data, already_tagged, predicted_note_data, is_note
                )
        return contentlist

    def write_predicted_ner_tags(self, predicted_data, predicted_note_data):
        self._contentindex = 0
        self._notecontentindex = 0
        self._wordindex = 0
        self._notewordindex = 0
        self._cur_word = ""
        self._cur_note_word = ""
        self._cur_pred_word = predicted_data[0][0][0]
        if self._use_notes and len(predicted_note_data) > 0:
            self._cur_pred_note_word = predicted_note_data[0][0][0]
        else:
            self._cur_pred_note_word = ""
        self._cur_pred_index = 0
        self._cur_pred_note_index = 0
        self._write_contentlist(self._text_tree, predicted_data, False, predicted_note_data, False)
        if len(predicted_data) > self._contentindex:
            print("Error: Predicted Data does not match the text of the xml file")
            raise ValueError
        if self._use_notes:
            if len(predicted_note_data) > self._notecontentindex:
                print("Error: Predicted Note Data does not match the text of the notes of the xml file")
                raise ValueError

    def _is_tag_matching_tag_list(self, tag_content, tag_list):
        for tag_config in tag_list:
            if tag_config[0] == tag_content["name"]:
                return True
        return False

    def get_list_of_tags_matching_tag_list(self, tag_list):
        matching_tag_list = []
        self._loop_contentlist(matching_tag_list, self._text_tree, tag_list)
        return matching_tag_list

    def _loop_contentlist(self, matching_tag_list, contentlist, tag_list):
        for contentindex in range(len(contentlist)):
            if isinstance(contentlist[contentindex], list):
                contentlist[contentindex] = self._loop_contentlist(
                    matching_tag_list, contentlist[contentindex], tag_list
                )
            elif isinstance(contentlist[contentindex], dict):
                if self._is_tag_matching_tag_list(contentlist[contentindex], tag_list):
                    matching_tag_list.append(contentlist[contentindex])
                if "tagcontent" in contentlist[contentindex].keys():
                    contentlist[contentindex]["tagcontent"] = self._loop_contentlist(
                        matching_tag_list, contentlist[contentindex]["tagcontent"], tag_list
                    )
        return contentlist


def write_predicted_text_list_back_to_TEI(directory, origdirectory, outdirectory, tr, tnw):
    for filename in os.listdir(directory):
        if not filename.endswith(
            "_notes.json"
        ): # and '0191_060186.xml' in filename: #and '0048_060046.xml' not in filename:
            print(filename)
            with open(join(directory, filename)) as f:
                predicted_data = json.load(f)
            print(filename[5:-5])
            if tr["use_notes"]:
                with open(join(directory, filename[:-5] + "_notes.json")) as g:
                    predicted_note_data = json.load(g)
            else:
                predicted_note_data = []

            brief = TEI_Writer(join(origdirectory, filename[5:-5]), tr=tr, tnw=tnw)
            brief.write_predicted_ner_tags(predicted_data, predicted_note_data)
            brief.refresh_text_by_tree()
            brief.write_back_to_file(join(outdirectory, filename[5:-5]))


def build_tag_list_from_tnw(tnw):
    tag_list = []
    for entity in tnw["entity_dict"]:
        tag_list.append(tnw["entity_dict"][entity])
    return tag_list

def run_test(directory,tr):
    count=0
    for filename in os.listdir(directory):
        count+=1
        if 1==1: #'0191_060186.xml' not in filename and '0588_101040.xml' not in filename: #588 ist DD R -Beispiel
            print(join(directory, filename))
            print(count,len(os.listdir(directory)))
            tei_file=TEI_Writer(join(directory, filename),tr=tr)
    print(count)


if __name__ == "__main__":
    import json

    with open("tei_entity_enricher/tei_entity_enricher/templates/TR_Configs/UJA_Edition.json") as f:
        # with open("tei_entity_enricher/tei_entity_enricher/templates/TR_Configs/Arendt_Edition.json") as f:
        tr = json.load(f)
    # print(tr)
    with open("tei_entity_enricher/tei_entity_enricher/templates/TNW/UJA_Prediction_Writer.json") as f:
        # with open("../TNW/Arendt_Prediction_Writer.json") as f:
        tnw = json.load(f)
    #write_predicted_text_list_back_to_TEI(
    #    "../uwe_johnson_data/data_040520/predicted_data_with_notes",
    #    "../uwe_johnson_data/data_040520/briefe",
    #    "test",
    #    tr=tr,
    #    tnw=tnw,
    #)
    tei_file=TEI_Writer('test/0588_101040.xml',tr=tr)
    #run_test("test",tr)
