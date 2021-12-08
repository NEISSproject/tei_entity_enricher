import logging
import os
import shutil
from typing import Optional

import streamlit as st

from tei_entity_enricher.menu.menu_base import MenuBase
from tei_entity_enricher.util.aip_interface.resume_params import NERResumeParams, get_params
from tei_entity_enricher.util import config_io
from tei_entity_enricher.util.helper import (
    module_path,
    state_ok,
    menu_NER_resume,
)
from tei_entity_enricher.util.train_course_helper import extract_val_metrics_from_train_log, show_metric_line_chart,c_ef1,c_loss, c_epoch
from tei_entity_enricher.util.aip_interface.processmanger.resume import get_resume_process_manager

logger = logging.getLogger(__name__)


class NERResumer(MenuBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._wd: Optional[str] = None
        # self.training_state = None
        self._data_config_check = []
        self.selected_ner_model = None
        self.resume_process_manager = None
        self._check_list = []

        if self.show_menu:
            self.workdir()
            self.show()

    @property
    def _params(self) -> NERResumeParams:
        return get_params()

    def show_train_course(self):
        train_ev_expander = st.expander(f"Training course of {os.path.basename(self._params.model)}", expanded=False)
        with train_ev_expander:
            if os.path.isfile(os.path.join(self._params.model, "train.log")):
                metrics=extract_val_metrics_from_train_log(os.path.join(self._params.model, "train.log"))
                if len(metrics)==1:
                    st.info(f"There is no train course to show, because only one epoch was found with ({c_ef1}: {metrics[0][c_ef1]}; {c_loss}: {metrics[0][c_loss]})")
                elif len(metrics)>1:
                    st.markdown('#### Metrics on the validation set per Epoch')
                    col1,col2=st.columns(2)
                    with col1:
                        st.markdown('##### '+c_ef1)
                        show_metric_line_chart(metrics,c_ef1)
                    with col2:
                        st.markdown('##### '+c_loss)
                        show_metric_line_chart(metrics,c_loss)
                    epochlist=[]
                    epoch_to_ef1_dict={}
                    epoch_to_loss_dict={}
                    for metric in metrics:
                        epochlist.append(metric[c_epoch])
                        epoch_to_ef1_dict[metric[c_epoch]]=metric[c_ef1]
                        epoch_to_loss_dict[metric[c_epoch]]=metric[c_loss]
                    epochlist.sort()
                    min_epoch=min(epochlist)
                    max_epoch=max(epochlist)
                    if "rt_current_epoch" not in st.session_state:
                        st.session_state["rt_current_epoch"]=max(epochlist)
                    if "rt_last_epoch" not in st.session_state:
                        st.session_state["rt_last_epoch"]=st.session_state.rt_current_epoch
                    st.slider(
                        label=f"Show metrics to epoch: ",
                        min_value=min_epoch,
                        max_value=max_epoch,
                        key="rt_current_epoch",
                    )

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(c_epoch,st.session_state.rt_current_epoch,st.session_state.rt_current_epoch-st.session_state.rt_last_epoch,delta_color="off")
                    with col2:
                        st.metric(c_ef1,epoch_to_ef1_dict[st.session_state.rt_current_epoch],round(epoch_to_ef1_dict[st.session_state.rt_current_epoch]-epoch_to_ef1_dict[st.session_state.rt_last_epoch],4))
                    with col3:
                        st.metric(c_loss,epoch_to_loss_dict[st.session_state.rt_current_epoch],round(epoch_to_loss_dict[st.session_state.rt_current_epoch]-epoch_to_loss_dict[st.session_state.rt_last_epoch],4),delta_color="inverse")
                    st.markdown(f"Currently displayed: Epoch {str(st.session_state.rt_current_epoch)}. Previously displayed: Epoch {str(st.session_state.rt_last_epoch)}")
                    st.session_state.rt_last_epoch=st.session_state.rt_current_epoch
                else:
                    st.warning(f"Couldn't load training course of {os.path.basename(self._params.model)}.")
            else:
                st.warning(f"Couldn't load training course of {os.path.basename(self._params.model)}.")

    def check_model_change(self):
        if "rt_last_selected_model" in st.session_state:
            if st.session_state.rt_last_selected_model!=self._params.model:
                del st.session_state["rt_current_epoch"]
                del st.session_state["rt_last_epoch"]
        st.session_state.rt_last_selected_model=self._params.model

    def show_resume_config_options(self):
        self.select_model_dir()
        self.check_model_change()
        if self._params.model and os.path.isfile(os.path.join(self._params.model, "trainer_params.json")):
            self._params.trainer_params_json = config_io.get_config(
                os.path.join(self._params.model, "trainer_params.json")
            )
            st.info(
                f'The model {os.path.basename(self._params.model)} was already trained for {self._params.trainer_params_json["current_epoch"]} epochs. The highest entity-wise F1 score obtained so far from the best epoch on the validation set was {self._params.trainer_params_json["early_stopping"]["current"]}.'
            )
            self.show_train_course()
            if self._params.resume_to_epoch is None:
                self._params.resume_to_epoch={}
            if self._params.model not in self._params.resume_to_epoch.keys():
                self._params.resume_to_epoch[self._params.model] = self._params.trainer_params_json["epochs"]
            if self._params.trainer_params_json["current_epoch"] + 1 > self._params.resume_to_epoch[self._params.model]:
                self._params.resume_to_epoch[self._params.model] = self._params.trainer_params_json["current_epoch"] + 1
            self._params.resume_to_epoch[self._params.model] = st.number_input(
                label="Resume training until epoch",
                min_value=self._params.trainer_params_json["current_epoch"] + 1,
                value=self._params.resume_to_epoch[self._params.model],
                step=1,
                help="Define the epoch up to which the training should be continued.",
            )

    def show(self):
        st.latex("\\text{\Huge{" + menu_NER_resume + "}}")

        self.show_resume_config_options()

        if self._check_list:
            st.error(f"Pre-configuration failed. Please correct: {', '.join(self._check_list)}!")
            return -1
        if self._resume_manager() != 0:
            return -1

        st.latex(state_ok)

    def _resume_manager(self):
        self.resume_process_manager = get_resume_process_manager(workdir=self._wd)
        self.resume_process_manager.set_current_params(self._params)
        return_code = self.resume_process_manager.st_manager()
        return return_code

    def select_model_dir(self):
        label = "NER Model to resume"
        target_dir = os.path.join(self._wd, "models_ner")
        if self._params.scan_models(target_dir) != 0:
            self._params.possible_models = {f"no {label} found": None}
            self._check_list.append(f"no {label} found")
        self._params.choose_model_widget(label)
        # st.write(self._params.model)

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
