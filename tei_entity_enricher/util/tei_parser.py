from bs4 import BeautifulSoup
import re


class TEIFile:
    def __init__(
        self,
        filename,
        tr_config,
        entity_dict=None,
        nlp=None,
        openfile=None,
        with_position_tags=False,
    ):
        self._pagelist = []
        self._soup = None
        if self._soup is None:
            if openfile is not None:
                self._soup = BeautifulSoup(openfile.getvalue().decode("utf-8"), "xml")
            else:
                with open(file=filename, mode="r", encoding="utf8") as tei:
                    self._soup = BeautifulSoup(tei, "xml")  # 'html.parser' )#'lxml')

        self._note_list = []
        self._tagged_note_list = []
        self._note_statistics = {}
        self._with_position_tags = with_position_tags
        if tr_config["use_notes"]:
            self._note_tags = tr_config["note_tags"]
        else:
            self._note_tags = []
        self._exclude_tags = tr_config["exclude_tags"]
        self.init_tnm(entity_dict)
        (
            self._text,
            self._tagged_text,
            self._statistics,
            self._notes,
            self._tagged_notes,
        ) = self._get_text_and_statistics(filename)
        self._tagged_text_line_list = []
        self._tagged_note_line_list = []

        if nlp is not None:
            self._nlp = nlp
        # else:
        #    self._nlp=spacy.load('de_core_news_sm')

    def init_tnm(self, entity_dict):
        self._allowed_tags = {}
        if entity_dict is not None:
            for entity in entity_dict:
                if len(entity_dict[entity]) > 0 and isinstance(entity_dict[entity][0], str):
                    if entity_dict[entity][0] in self._allowed_tags.keys():
                        self._allowed_tags[entity_dict[entity][0]].append([entity, entity_dict[entity][1]])
                    else:
                        self._allowed_tags[entity_dict[entity][0]] = [[entity, entity_dict[entity][1]]]
                else:
                    for mapping_entry in entity_dict[entity]:
                        if mapping_entry[0] in self._allowed_tags.keys():
                            self._allowed_tags[mapping_entry[0]].append([entity, mapping_entry[1]])
                        else:
                            self._allowed_tags[mapping_entry[0]] = [[entity, mapping_entry[1]]]

    def get_entity_name_to_pagecontent(self, pagecontent):
        if pagecontent.name in self._allowed_tags.keys():
            for tag_entry in self._allowed_tags[pagecontent.name]:
                attrs_match = True
                for attr in tag_entry[1].keys():
                    if not (attr in pagecontent.attrs.keys() and pagecontent.attrs[attr] == tag_entry[1][attr]):
                        attrs_match = False
                if attrs_match:
                    return tag_entry[0]
        return None

    def _add_content_to_statistics(self, entity, statistics, content_text_list):
        tagtext = ""
        for i in range(len(content_text_list)):
            if i > 0:
                tagtext = tagtext + " "
            tagtext = tagtext + content_text_list[i]
        if entity not in statistics.keys():
            statistics[entity] = [1, [tagtext]]
        else:
            statistics[entity][0] += 1
            statistics[entity][1].append(tagtext)
        return statistics

    def _merge_statistics(self, firststatistics, secondstatistics):
        for key in secondstatistics.keys():
            if key in firststatistics.keys():
                firststatistics[key][0] += secondstatistics[key][0]
                firststatistics[key][1] += secondstatistics[key][1]
            else:
                firststatistics[key] = secondstatistics[key]
        return firststatistics

    def _get_text_from_contentlist(self, contentlist, is_already_note):
        text_list = []
        tagged_text_list = []
        statistics = {}

        for pagecontent in contentlist:
            if (
                (
                    (pagecontent.name not in ["lb", "pb"] and pagecontent.name not in self._note_tags)
                    or (pagecontent.name in self._note_tags and is_already_note)
                )
                and pagecontent.name not in self._exclude_tags
                and pagecontent != "\n"
                and str(pagecontent.__class__.__name__) != "Comment"
            ):
                if pagecontent.name == "closer" or pagecontent.name == "postscript":
                    text_list.append(" <linebreak>\n")
                    tagged_text_list.append(" <linebreak>\n")
                entity = self.get_entity_name_to_pagecontent(pagecontent)
                if pagecontent.name is not None and entity is None:
                    (
                        text_list_to_add,
                        tagged_text_list_to_add,
                        statistics_to_add,
                    ) = self._get_text_from_contentlist(pagecontent.contents, is_already_note)
                    #text_list = text_list + text_list_to_add
                    text_list.extend(text_list_to_add)
                    #tagged_text_list = tagged_text_list + tagged_text_list_to_add
                    tagged_text_list.extend(tagged_text_list_to_add)
                    statistics = self._merge_statistics(statistics, statistics_to_add)
                    if pagecontent.name == "address":
                        #text_list = text_list + [" <linebreak>\n"]
                        text_list.append(" <linebreak>\n")
                        #tagged_text_list = tagged_text_list + [" <linebreak>\n"]
                        tagged_text_list.append(" <linebreak>\n")
                elif pagecontent.name is None:
                    text_list.append(pagecontent)
                    tagged_text_list.append(pagecontent)
                else:
                    (
                        text_list_to_add,
                        tagged_text_list_to_add,
                        statistics_to_add,
                    ) = self._get_text_from_contentlist(pagecontent.contents, is_already_note)
                    #text_list = text_list + text_list_to_add
                    text_list.extend(text_list_to_add)
                    statistics = self._add_content_to_statistics(entity, statistics, text_list_to_add)
                    #tagged_text_list = (
                    #    tagged_text_list + [" <" + entity + "> "] + tagged_text_list_to_add + [" </" + entity + "> "]
                    #)
                    tagged_text_list.append(" <" + entity + "> ")
                    tagged_text_list.extend(tagged_text_list_to_add)
                    tagged_text_list.append(" </" + entity + "> ")
                    statistics = self._merge_statistics(statistics, statistics_to_add)
                if pagecontent.name == "opener":
                    text_list.append(" <linebreak>\n")
                    tagged_text_list.append(" <linebreak>\n")
            elif pagecontent.name in self._note_tags:
                (
                    note_list_to_add,
                    tagged_note_list_to_add,
                    note_statistics_to_add,
                ) = self._get_text_from_contentlist(pagecontent.contents, True)
                # print(note_list_to_add,tagged_note_list_to_add,note_statistics_to_add)
                #self._note_list = self._note_list + note_list_to_add + [" <linebreak>\n"]
                self._note_list.extend(note_list_to_add)
                self._note_list.append(" <linebreak>\n")
                #self._tagged_note_list = self._tagged_note_list + tagged_note_list_to_add + [" <linebreak>\n"]
                self._tagged_note_list.extend(tagged_note_list_to_add)
                self._tagged_note_list.append(" <linebreak>\n")
                self._note_statistics = self._merge_statistics(self._note_statistics, note_statistics_to_add)
            elif pagecontent.name not in ["lb", "pb"] and pagecontent.name not in self._exclude_tags:
                text_list.append(" ")
                tagged_text_list.append(" ")
        # text_list.append(" ")
        # tagged_text_list.append(" ")
        return text_list, tagged_text_list, statistics

    def _get_text_and_statistics(self, filename):
        textcontent = self._soup.find("text")
        text_list = []
        tagged_text_list = []
        statistics = {}
        self._note_list = []
        self._tagged_note_list = []
        self._note_statistics = {}
        # pages = textcontent.find_all(['opener','p','closer','postscript'])
        for page in textcontent.contents:
            if isinstance(page, str):
                content=[page]
            else:
                content=page.contents
            if page.name not in self._exclude_tags:
                self._pagelist.append({"name": page.name, "page": page})
                if page.name in self._note_tags:
                    (
                        note_list_to_add,
                        tagged_note_list_to_add,
                        note_statistics_to_add,
                    ) = self._get_text_from_contentlist(content, True)
                    # print(note_list_to_add,tagged_note_list_to_add,note_statistics_to_add)
                    #self._note_list = self._note_list + note_list_to_add + [" <linebreak>\n"]
                    self._note_list.extend(note_list_to_add)
                    self._note_list.append(" <linebreak>\n")
                    #self._tagged_note_list = self._tagged_note_list + tagged_note_list_to_add + [" <linebreak>\n"]
                    self._tagged_note_list.extend(tagged_note_list_to_add)
                    self._tagged_note_list.append(" <linebreak>\n")
                    self._note_statistics = self._merge_statistics(self._note_statistics, note_statistics_to_add)
                else:
                    (
                        new_text_list,
                        new_tagged_text_list,
                        new_statistics,
                    ) = self._get_text_from_contentlist(content, False)
                    #text_list = text_list + new_text_list + [" <linebreak>\n"]
                    text_list.extend(new_text_list)
                    text_list.append(" <linebreak>\n")
                    #tagged_text_list = tagged_text_list + new_tagged_text_list + [" <linebreak>\n"]
                    tagged_text_list.extend(new_tagged_text_list)
                    tagged_text_list.append(" <linebreak>\n")
                    statistics = self._merge_statistics(statistics, new_statistics)

        text = ""
        for element in text_list:
            text = text + str(element)
        text = " ".join(re.split(r"\s+", text))
        text = text.replace("<linebreak>", "\n")
        tagged_text = ""
        for element in tagged_text_list:
            tagged_text = tagged_text + str(element)
        tagged_text = " ".join(re.split(r"\s+", tagged_text))
        tagged_text = tagged_text.replace("<linebreak>", "\n")
        notes = ""
        for element in self._note_list:
            notes = notes + str(element)
        notes = " ".join(re.split(r"\s+", notes))
        notes = notes.replace("<linebreak>", "\n")
        tagged_notes = ""
        for element in self._tagged_note_list:
            tagged_notes = tagged_notes + str(element)
        tagged_notes = " ".join(re.split(r"\s+", tagged_notes))
        tagged_notes = tagged_notes.replace("<linebreak>", "\n")
        return text, tagged_text, statistics, notes, tagged_notes

    def build_tagged_text_line_list(self):
        cur_tag = "O"  # O is the sign for without tag
        tagged_text_lines = self.get_tagged_text().split("\n")
        # Build Mapping Word to Tag
        for tagged_text_line in tagged_text_lines:
            cur_line_list = []
            tagged_text_list = tagged_text_line.split(" ")
            for text_part in tagged_text_list:
                if text_part.startswith("<") and text_part.endswith(">"):
                    if text_part[1] == "/":
                        cur_tag = "O"  # O is the sign for without tag
                    else:
                        cur_tag = text_part[1:-1]
                        first_tag_element = True
                elif text_part is not None and text_part != "":
                    if self._with_position_tags and cur_tag != "O":
                        if first_tag_element:
                            modified_tag = "B-" + cur_tag
                            first_tag_element = False
                        else:
                            modified_tag = "I-" + cur_tag
                    else:
                        modified_tag = cur_tag
                    # Sentence extraction doesn't work for capitalized words, that is why we use the following
                    if text_part.upper() == text_part:
                        cur_line_list.append([text_part.lower(), modified_tag, 1])
                    else:
                        cur_line_list.append([text_part, modified_tag, 0])
            self._tagged_text_line_list.append(cur_line_list)
        # Seperate sentences with the help of spacy
        for i in range(len(self._tagged_text_line_list)):
            # print(self._tagged_text_line_list[i])
            cur_line_text = ""
            tokenlist=[]
            for j in range(len(self._tagged_text_line_list[i])):
                if j > 0:
                    #nlp sentence split has problems with strings whose length is longer than 1000000. That is why we use the following workaround
                    if len(cur_line_text)+len(self._tagged_text_line_list[i][j][0])>999000 and self._tagged_text_line_list[i][j][1]=="O":
                        tokenlist.append(self._nlp(cur_line_text))
                        cur_line_text = ""
                    else:
                        cur_line_text += " "
                cur_line_text += self._tagged_text_line_list[i][j][0]
            # print('cur line text: ',cur_line_text)
            tokenlist.append(self._nlp(cur_line_text))
            k = 0
            new_line_list = []
            cur_word = ""
            for tokens in tokenlist:
                for sent in tokens.sents:
                    space_before = False
                    for wordindex in range(len(sent)):
                        cur_tag_element = self._tagged_text_line_list[i][k]
                        cur_word += str(sent[wordindex])
                        word_to_insert = str(sent[wordindex])
                        if cur_tag_element[2] == 1:
                            word_to_insert = word_to_insert.upper()
                        if wordindex == 0 and not cur_tag_element[1].startswith("I-"):
                            new_line_list.append([word_to_insert, cur_tag_element[1], 2])
                        elif space_before:
                            new_line_list.append([word_to_insert, cur_tag_element[1], 0])
                        else:
                            new_line_list.append([word_to_insert, cur_tag_element[1], 1])
                        if cur_word == cur_tag_element[0]:
                            space_before = True
                            cur_word = ""
                            k += 1
                        else:
                            space_before = False
            self._tagged_text_line_list[i] = new_line_list
        # for line_list in self._tagged_text_line_list:
        #    print(line_list)
        return self._tagged_text_line_list

    def build_tagged_note_line_list(self):
        cur_tag = "O"  # O is the sign for without tag
        tagged_note_lines = self.get_tagged_notes().split("\n")
        # Build Mapping Word to Tag
        for tagged_note_line in tagged_note_lines:
            cur_line_list = []
            tagged_note_list = tagged_note_line.split(" ")
            for note_part in tagged_note_list:
                if note_part.startswith("<") and note_part.endswith(">"):
                    if note_part[1] == "/":
                        cur_tag = "O"  # O is the sign for without tag
                    else:
                        cur_tag = note_part[1:-1]
                        first_tag_element = True
                elif note_part is not None and note_part != "":
                    if self._with_position_tags and cur_tag != "O":
                        if first_tag_element:
                            modified_tag = "B-" + cur_tag
                            first_tag_element = False
                        else:
                            modified_tag = "I-" + cur_tag
                    else:
                        modified_tag = cur_tag
                    # Sentence extraction doesn't work for capitalized words, that is why we use the following
                    if note_part.upper() == note_part:
                        cur_line_list.append([note_part.lower(), modified_tag, 1])
                    else:
                        cur_line_list.append([note_part, modified_tag, 0])
            self._tagged_note_line_list.append(cur_line_list)
        # Seperate sentences with the help of spacy
        for i in range(len(self._tagged_note_line_list)):
            # print(self._tagged_text_line_list[i])
            cur_line_note = ""
            tokenlist=[]
            for j in range(len(self._tagged_note_line_list[i])):
                if j > 0:
                    #nlp sentence split has problems with strings whose length is longer than 1000000. That is why we use the following workaround
                    if len(cur_line_note)+len(self._tagged_note_line_list[i][j][0])>999000 and self._tagged_note_line_list[i][j][1]=="O":
                        tokenlist.append(self._nlp(cur_line_note))
                        cur_line_note = ""
                    else:
                        cur_line_note += " "
                cur_line_note += self._tagged_note_line_list[i][j][0]
            # print('cur line text: ',cur_line_text)
            tokenlist.append(self._nlp(cur_line_note))
            k = 0
            new_line_list = []
            cur_word = ""
            for tokens in tokenlist:
                for sent in tokens.sents:
                    space_before = False
                    for wordindex in range(len(sent)):
                        cur_tag_element = self._tagged_note_line_list[i][k]
                        cur_word += str(sent[wordindex])
                        word_to_insert = str(sent[wordindex])
                        if cur_tag_element[2] == 1:
                            word_to_insert = word_to_insert.upper()
                        if wordindex == 0 and not cur_tag_element[1].startswith("I-"):
                            new_line_list.append([word_to_insert, cur_tag_element[1], 2])
                        elif space_before:
                            new_line_list.append([word_to_insert, cur_tag_element[1], 0])
                        else:
                            new_line_list.append([word_to_insert, cur_tag_element[1], 1])
                        if cur_word == cur_tag_element[0]:
                            space_before = True
                            cur_word = ""
                            k += 1
                        else:
                            space_before = False
            self._tagged_note_line_list[i] = new_line_list
        # for line_list in self._tagged_text_line_list:
        #    print(line_list)
        return self._tagged_note_line_list

    def get_text(self):
        return self._text

    def get_tagged_text(self):
        return self._tagged_text

    def get_notes(self):
        return self._notes

    def get_tagged_notes(self):
        return self._tagged_notes

    def get_tagged_text_line_list(self):
        return self._tagged_text_line_list

    def get_tagged_note_line_list(self):
        return self._tagged_note_line_list

    def get_statistics(self):
        return self._statistics

    def print_statistics(self):
        for key in self._statistics.keys():
            print(key, self._statistics[key])

    def get_note_statistics(self):
        return self._note_statistics

    def print_note_statistics(self):
        for key in self._note_statistics.keys():
            print(key, self._note_statistics[key])


def split_into_sentences(tagged_text_line_list):
    cur_sentence = []
    sentence_list = []
    for text_part in tagged_text_line_list:
        for word in text_part:
            if word[2] == 2: # and len(cur_sentence)>100:
                if len(cur_sentence) > 0:
                    sentence_list.append(cur_sentence)
                cur_sentence = [word]
            else:
                cur_sentence.append(word)
    if len(cur_sentence) > 0:
        sentence_list.append(cur_sentence)
    return sentence_list


if __name__ == "__main__":
    import json

    with open("tei_entity_enricher/tei_entity_enricher/templates/TR_Configs/Standard.json") as f:
        # with open("tei_entity_enricher/tei_entity_enricher/templates/TR_Configs/Arendt_Edition.json") as f:
        tr = json.load(f)
    with open("TNM/Dehmel_Edition.json") as f:
        # with open("tei_entity_enricher/tei_entity_enricher/templates/TR_Configs/Arendt_Edition.json") as f:
        tnm = json.load(f)
    # print(tr)
    # brief=tei_file('../uwe_johnson_data/data_040520/briefe/0003_060000.xml')
    # Arendt Example: '../uwe_johnson_data/data_hannah_arendt/III-001-existenzPhilosophie.xml', '../uwe_johnson_data/data_hannah_arendt/III-002-zionismusHeutigerSicht.xml'
    # Sturm Example: '../uwe_johnson_data/data_sturm/briefe/Q.01.19140115.FMA.01.xml' '../uwe_johnson_data/data_sturm/briefe/Q.01.19150413.JVH.01.xml'
    #brief = TEIFile("../uwe_johnson_data/data_Dehmel_short/dehmel_groundtruth_build_test_daten.xml", tr_config=tr,entity_dict=tnm["entity_dict"],with_position_tags=True)
    #brief = TEIFile("../uwe_johnson_data/data_Dehmel/trainingsdaten_UTF8_ntee.xml", tr_config=tr,entity_dict=tnm["entity_dict"],with_position_tags=True,nlp=spacy.load('de_core_news_sm'))
    import spacy
    #brief = TEIFile("../uwe_johnson_data/Mareike_Fehler/_tei_writer_test_ohne-ab-wrapper-element_MINIMALVERSION.xml", tr_config=tr,nlp=spacy.load('de_core_news_sm'))
    brief = TEIFile("../uwe_johnson_data/Mareike_Fehler/draco_test.xml", tr_config=tr,nlp=spacy.load('de_core_news_sm'))
    #raw_ner_data = split_into_sentences(brief.build_tagged_text_line_list())
    #print(raw_ner_data)
    print(brief.get_text())

    # print(brief.get_notes())
