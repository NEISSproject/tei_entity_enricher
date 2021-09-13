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

    def scan_models(self, target_dir):
        possible_paths = []
        for root, subdirs, files in os.walk(target_dir):
            if self.path_check(root, subdirs, files):
                possible_paths.append(root)
        logger.debug(f"model possible_paths: {possible_paths}")
        self.possible_models = dict((os.path.relpath(x, target_dir), x) for x in possible_paths)
        logger.debug(f"model dict: {self.possible_models}")
        return 0 if possible_paths else -1

    def choose_model_widget(self, label="model", init=None, st_element=st):
        model_key = st_element.selectbox(
            f"Choose a {label}",
            tuple(self.possible_models.keys()),
            tuple(self.possible_models.keys()).index(init) if init in tuple(self.possible_models.keys()) else 0,
            key=f"select_{label}",
            help=f"Choose a {label}, which you want to use.",
        )
        self.model = self.possible_models[model_key]
