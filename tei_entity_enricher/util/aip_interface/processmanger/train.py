import logging
import sys, os
from queue import Empty

import streamlit as st

from tei_entity_enricher.util.aip_interface.processmanger.base import ProcessManagerBase
from tei_entity_enricher.util import config_io
from tei_entity_enricher.util.helper import remember_cwd

logger = logging.getLogger(__name__)
ON_POSIX = "posix" in sys.builtin_module_names


@st.cache(allow_output_mutation=True)
def get_train_process_manager(workdir):
    return TrainProcessManager(workdir=workdir, name="train_process_manager")


class TrainProcessManager(ProcessManagerBase):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._current_epoch: str = ""

    def clear_process(self):
        super().clear_process()
        self._current_epoch = ""

    def process_command_list(self):
        return [
            "tfaip-train-from-params",
            "trainer_params.json",
            "--trainer.progress_bar_mode=2",
            "--trainer.progbar_delta_time=1",
        ]

    def read_progress(self):
        try:
            while True:
                line = self.std_queue.get_nowait().decode("utf-8")  # or q.get(timeout=.1)
                if str(line).startswith("Epoch"):
                    self._current_epoch = line
                elif str(line).startswith("Field"):
                    pass
                elif line != "":
                    self._progress_content = line
                # logging.info(f"progress line: {self._progress_content}")
        except Empty:
            pass

        return f"{self._current_epoch}step:{self._progress_content}"

    def set_current_params(self,params):
        self._params=params

    def build_lst_files_if_necessary(self):
        if (
            st.session_state.nt_train_option == "Self-Defined"
            and st.session_state.nt_train_list_option == "From Folder"
        ):
            if os.path.isdir(self._params.nt_train_dir):
                trainfilelist = [
                    os.path.join(self._params.nt_train_dir, filepath + "\n")
                    for filepath in os.listdir(self._params.nt_train_dir)
                    if filepath.endswith(".json")
                ]
                with open(
                    os.path.join(
                        self._params.trainer_params_json["output_dir"],
                        "train.lst",
                    ),
                    "w+",
                ) as htrain:
                    htrain.writelines(trainfilelist)
                self._params.trainer_params_json["gen"]["train"]["lists"] = [
                    os.path.join(
                        self._params.trainer_params_json["output_dir"],
                        "train.lst",
                    )
                ]
            if os.path.isdir(self._params.nt_val_dir):
                valfilelist = [
                    os.path.join(self._params.nt_val_dir, filepath + "\n")
                    for filepath in os.listdir(self._params.nt_val_dir)
                    if filepath.endswith(".json")
                ]
                with open(
                    os.path.join(
                        self._params.trainer_params_json["output_dir"],
                        "val.lst",
                    ),
                    "w+",
                ) as hval:
                    hval.writelines(valfilelist)
                self._params.trainer_params_json["gen"]["val"]["lists"] = [
                    os.path.join(
                        self._params.trainer_params_json["output_dir"],
                        "val.lst",
                    )
                ]

    def do_before_start_process(self):
        self.save_train_params()

    def save_train_params(self):
        self.build_lst_files_if_necessary()
        with remember_cwd():
            os.chdir(self.work_dir)
            config_io.set_config(self._params.trainer_params_json)
        return 0
