import json
import logging
import os
import shutil

import streamlit as st

from tei_entity_enricher.util import config_io
from tei_entity_enricher.util.helper import module_path

logger = logging.getLogger(__name__)


class NERTrainer(object):
    def __init__(self, state, show_menu=True,):
        self._workdir_path = None
        self.state = state
        if self.workdir() != 0:
            return
        logger.info("load trainer params")
        if self.load_trainer_params() != 0:
            st.error("Failed to load trainer_params.json")
            return
        if self.data_configuration() != 0:
            st.error("Failed to run data_configuration")
            return

    def load_trainer_params(self):
        if not os.path.isfile("trainer_params.json"):
            logger.info("copy trainer_params.json from template")
            shutil.copy(os.path.join(module_path, "templates", "trainer", "trainer_params.json"), os.getcwd())
        self.trainer_params_json = config_io.get_config("trainer_params.json")
        return 0

    def data_configuration(self):
        print(json.dumps(self.trainer_params_json, indent=2))
        st.text_input("train.lists", value=self.trainer_params_json["gen"]["train"]["lists"])
        # state.input = st.text_input("Set input value.", state.input or "")
        # st.write("Page state:", state.page)
        # if st.button("Jump to Pred"):
        #     state.page = "NER Prediction"
        #     st.experimental_rerun()

        # uploaded_file = st.file_uploader("Load session config")
        # if uploaded_file is not None:
        #     config_content = uploaded_file.getvalue()
        #     st.write(json.loads(config_content))

    def workdir(self):
        start_config_path = os.path.join(module_path, "templates", "trainer", "start_config.state")
        start_config = config_io.get_config(start_config_path)
        st_workdir_path, st_wdp_status = st.beta_columns([10, 1])

        if start_config and os.path.isdir(start_config["workdir"]):
            workdir_path = start_config["workdir"]
        else:
            workdir_path = os.getcwd()

        wdp_status = st_wdp_status.latex(r"\huge\color{orange}\bigcirc")
        self._workdir_path = st_workdir_path.text_input("Workdir:", value=workdir_path, help="absolute path to working directory")
        wdp_status = wdp_status.latex(r"\checkmark")
        # wdp_button = st_wdp_button.button("Set")
        if os.path.isfile(os.path.join(self._workdir_path, "trainer_params.json")):
                wdp_status = wdp_status.latex(r"\huge\color{green}\checkmark")
        if st_workdir_path:
            if os.path.isdir(self._workdir_path):
                config_io.set_config({"workdir": self._workdir_path, "config_path": start_config_path})
                if not os.path.isfile(os.path.join(self._workdir_path,"trainer_params.json")):
                    shutil.copy(os.path.join(module_path, "templates", "trainer", "trainer_params.json"), self._workdir_path)
            else:
                wdp_status = wdp_status.latex(r"\huge\color{red}X")
                return -1
        return 0

