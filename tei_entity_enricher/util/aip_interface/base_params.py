import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict

from dataclasses_json import dataclass_json
import streamlit as st


logger = logging.getLogger(__name__)


@dataclass
@dataclass_json
class AIPBaseParams(ABC):
    params_json: Dict = None
    possible_models: Dict = None
    model: str = None

    @abstractmethod
    def path_check(self, root, subdirs, files):
        raise NotImplementedError

    def scan_models(self, target_dir, template_dir=None):
        possible_paths = []
        possible_template_paths = []
        for root, subdirs, files in os.walk(target_dir):
            if self.path_check(root, subdirs, files):
                possible_paths.append(root)
        logger.debug(f"model possible_paths: {possible_paths}")
        if template_dir is not None:
            for root, subdirs, files in os.walk(template_dir):
                if self.path_check(root, subdirs, files):
                    possible_template_paths.append(root)
            logger.debug(f"model possible_template_paths: {possible_template_paths}")

        self.possible_models = dict((os.path.relpath(x, target_dir), x) for x in possible_paths)
        if len(possible_template_paths)>0:
           for possible_template_path in possible_template_paths:
               self.possible_models[os.path.relpath(possible_template_path, template_dir)+" (Template)"]=possible_template_path
        logger.debug(f"model dict: {self.possible_models}")
        return 0 if possible_paths else -1

    def choose_model_widget(self, label="model", init=None, st_element=st):
        if init is not None and f"select_{label}" not in st.session_state and init in list(self.possible_models.keys()):
            st.session_state[f"select_{label}"]=init
        st_element.selectbox(
            label=f"Choose a {label}",
            options=tuple(self.possible_models.keys()),
            key=f"select_{label}",
            help=f"Choose a {label}, which you want to use.",
        )
        self.model = self.possible_models[st.session_state[f"select_{label}"]]
