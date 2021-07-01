import logging
import os
import sys
import json
from typing import Optional

import streamlit as st

from tei_entity_enricher.util.processmanger.base import ProcessManagerBase
from tei_entity_enricher.util.processmanger.ner_prediction_params import NERPredictionParams, get_params
from tei_entity_enricher.util.spacy_lm import get_spacy_lm
import tei_entity_enricher.util.tei_parser as tp

logger = logging.getLogger(__name__)
ON_POSIX = "posix" in sys.builtin_module_names
predict_option_json = "Predict a JSON-File"
predict_option_tei = "Predict Text of TEI-Files"
predict_option_single_tei = "Predict a single TEI-File"
predict_option_tei_folder = "Predict all TEI-Files of a folder"


@st.cache(allow_output_mutation=True)
def get_predict_process_manager(workdir):
    return PredictProcessManager(workdir=workdir, name="prediction_process_manager", params=get_params())


class PredictProcessManager(ProcessManagerBase):
    def __init__(self, params: NERPredictionParams, **kwargs):
        super().__init__(**kwargs)
        self._params: NERPredictionParams = params
        self._predict_script_path = os.path.join(
            self.work_dir, "tf2_neiss_nlp", "tfaip_scenario", "nlp", "ner", "scripts", "prediction_ner.py"
        )

    def process_command_list(self):
        return [
            "python",
            self._predict_script_path,
            "--export_dir",
            self._params.ner_model_dir,
            "--input_json",
            self._params.input_json_file,
            "--out",
            self._params.prediction_out_dir,
        ]

    def do_before_start_process(self):
        if self._params.predict_conf_option == predict_option_tei:
            message_placeholder = st.empty()
            self.message("Preprocessing TEI-Files.", st_element=message_placeholder)
            tei_filelist = []
            if self._params.predict_conf_tei_option == predict_option_single_tei:
                tei_filelist.append(self._params.input_tei_file)
            elif self._params.predict_conf_tei_option == predict_option_tei_folder:
                tei_filelist = [
                    os.path.join(self._params.input_tei_folder, filepath) for filepath in os.listdir(self._params.input_tei_folder) if filepath.endswith(".xml")
                ]
            if len(tei_filelist) < 1:
                message_placeholder.empty()
                return "With the given Configuration no TEI-Files where found!"
            # TODO Sprachauswahl in GUI einbauen
            nlp = get_spacy_lm("German")
            all_data = []
            file_name_dict = {}
            for fileindex in range(len(tei_filelist)):
                self.message(f"Preprocess file {tei_filelist[fileindex]}...", st_element=message_placeholder)
                brief = tp.TEIFile(
                    filename=tei_filelist[fileindex],
                    tr_config=self._params.predict_tei_reader,
                    nlp=nlp,
                    with_position_tags=True,
                )
                raw_ner_data = tp.split_into_sentences(brief.build_tagged_text_line_list())
                old_length=len(all_data)
                all_data.extend(raw_ner_data)
                file_name_dict[tei_filelist[fileindex]]={"begin":old_length,"end":len(all_data)}
                if self._params.predict_tei_reader["use_notes"]:
                    raw_ner_note_data = tp.split_into_sentences(brief.build_tagged_note_line_list())
                    all_data.extend(raw_ner_note_data)
                    file_name_dict[tei_filelist[fileindex]]["note_end"]=len(all_data)
            with open(os.path.join(self._params.prediction_out_dir,"data_to_predict.json"),"w+") as h:
                json.dump(all_data, h)
            with open(os.path.join(self._params.prediction_out_dir,"predict_file_dict.json"),"w+") as h2:
                json.dump(file_name_dict, h2)
            self._params.input_json_file=os.path.join(self._params.prediction_out_dir,"data_to_predict.json")
            message_placeholder.empty()
        return None

    def do_after_finish_process(self):
        print("Finish Trigger")
        return None
