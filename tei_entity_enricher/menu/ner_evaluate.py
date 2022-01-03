import logging
import os
import shutil
from typing import Optional

import streamlit as st

from tei_entity_enricher.menu.menu_base import MenuBase
from tei_entity_enricher.util.aip_interface.evaluate_params import NEREvaluateParams, get_params
import tei_entity_enricher.menu.tei_ner_gb as gb
from tei_entity_enricher.util.helper import (
    module_path,
    state_ok,
    menu_NER_evaluate,
)
from tei_entity_enricher.util.train_course_helper import extract_evaluations_to_model_path, c_ef1, c_tng

from tei_entity_enricher.util.aip_interface.processmanger.evaluate import get_evaluate_process_manager

logger = logging.getLogger(__name__)


class NEREvaluator(MenuBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._wd: Optional[str] = None
        self.resume_process_manager = None
        self._check_list = []

        if self.show_menu:
            self.tng = gb.TEINERGroundtruthBuilder(show_menu=False)
            self.workdir()
            self.show()

    @property
    def _params(self) -> NEREvaluateParams:
        return get_params()

    def build_eval_dict_list_tablestring(self, eval_dict_list):
        tablestring = f"Test set of Groundtruth | {c_ef1} \n -----|-------"
        for eval_dict in eval_dict_list:
            tablestring += "\n " + eval_dict[c_tng] + " | " + str(round(eval_dict[c_ef1], 4))
        return tablestring

    def show_model_evaluation(self):
        self.select_model_dir()
        if self._params.model:
            eval_dict_list = extract_evaluations_to_model_path(self._params.model)
            if len(eval_dict_list) > 0:
                eval_expander = st.expander(label=f"Existing evaluations of {os.path.basename(self._params.model)}:",expanded=True)
                with eval_expander:
                    st.markdown(self.build_eval_dict_list_tablestring(eval_dict_list))
                    st.markdown(" ")  # only for layouting reasons (placeholder)
            else:
                st.info(f"No evaluations for the model {os.path.basename(self._params.model)} found.")


    def show_evaluation_module(self):
        if self._params.model:
            if len(self.tng.tngdict.keys())==0:
                self._check_list.append(f"no Groundtruth found")
            else:
                st.selectbox(
                    label="Choose a Groundtruth for a new evaluation",
                    options=tuple(self.tng.tngdict.keys()),
                    key="ne_sel_tng_name",
                    help="Choose a Groundtruth whose test set you want to evaluate.",
                )
                trainlistfilepath, devlistfilepath, testlistfilepath = self.tng.get_filepath_to_gt_lists(
                    st.session_state.ne_sel_tng_name
                )
                self._params.current_test_list_path = testlistfilepath
            if self._check_list:
                st.error(f"Pre-configuration failed. Please correct: {', '.join(self._check_list)}!")
                return -1

            if self._evaluate_manager() != 0:
                return -1

            st.latex(state_ok)

    def show(self):
        st.latex("\\text{\Huge{" + menu_NER_evaluate + "}}")
        self.show_model_evaluation()
        return self.show_evaluation_module()

    def _evaluate_manager(self):
        self.evaluate_process_manager = get_evaluate_process_manager(workdir=self._wd)
        self.evaluate_process_manager.set_current_params(self._params)
        return_code = self.evaluate_process_manager.st_manager()
        return return_code

    def select_model_dir(self):
        label = "NER Model for Evaluation"
        target_dir = os.path.join(self._wd, "models_ner")
        if self._params.scan_models(target_dir) != 0:
            self._params.possible_models = {f"no {label} found": None}
            self._check_list.append(f"no {label} found")
        self._params.choose_model_widget(label)

    def workdir(self):
        if module_path.lower() != os.path.join(os.getcwd(), "tei_entity_enricher", "tei_entity_enricher").lower():
            if self.show_menu:
                st.error("Please run ntee-start from the directory which contains the git repos 'tei_entity_enricher'.")
            else:
                logging.error(
                    "Please run ntee-start from the directory which contains the git repos 'tei_entity_enricher'."
                )
            return -1
        self._wd = os.path.join(os.getcwd(), "ner_trainer")

        return 0
