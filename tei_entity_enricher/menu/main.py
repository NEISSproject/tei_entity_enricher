import logging

import streamlit as st

from tei_entity_enricher.menu.ner_trainer import NERTrainer
from tei_entity_enricher.util.SessionState import _get_state
from PIL import Image
import os
import tei_entity_enricher.menu.tei_reader as tr
import tei_entity_enricher.menu.ner_task_def as ntd
import tei_entity_enricher.menu.tei_ner_map as tnm
import tei_entity_enricher.menu.tei_ner_gb as tng
from tei_entity_enricher.util.helper import module_path

logger = logging.getLogger(__name__)


class Main:
    def __init__(self, args):
        self.state = None
        self.show(args)

    # def decode_arguments(self, args):
    #     for key_value in args:
    #         if

    def show(self, args):
        st.set_page_config(layout='wide')  # Hiermit kann man die ganze Breite des Bildschirms ausschöpfen
        self.state = _get_state()
        pages = {
            "TEI Reader Config": self.tei_reader,
            "NER Task Entity Definition": self.ner_task_def,
            "TEI NER Entity Mapping": self.tei_ner_map,
            "TEI NER Groundtruth Builder": self.gt_builder,
            "TEI NER Writer Config": self.tei_ner_writer,
            "NER Trainer": self.ner_trainer,
            "NER Prediction": self.ner_prediction,
        }
        logo_frame, heading_frame = st.sidebar.beta_columns([1, 2])
        heading_frame.latex('\\text{\Huge{N-TEE}}')
        st.sidebar.latex('\\text{\large{\\textbf{N}EISS - \\textbf{T}EI \\textbf{E}ntity \\textbf{E}nricher}}')

        # Include NEISS Logo
        neiss_logo = Image.open(os.path.join(module_path, 'images', 'neiss_logo_nn_pentagon01b2.png'))
        logo_frame.image(neiss_logo)

        # Define sidebar as radiobuttons
        self.state.page = st.sidebar.radio("Main Menu", tuple(pages.keys()),
                                           tuple(pages.keys()).index(self.state.page) if self.state.page else int(
                                               args.start_state))

        # Display the selected page with the session state
        pages[self.state.page]()

        # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
        self.state.sync()

    def tei_reader(self):
        tr.TEIReader(self.state)

    def ner_task_def(self):
        ntd.NERTaskDef(self.state)

    def tei_ner_map(self):
        tnm.TEINERMap(self.state)

    def gt_builder(self):
        tng.TEINERGroundtruthBuilder(self.state)

    def tei_ner_writer(self):
        st.latex('\\text{\Huge{TEI NER Writer Config}}')
        logger.info(self.state)

    def ner_trainer(self):
        NERTrainer(self.state)

    def ner_prediction(self):
        st.latex('\\text{\Huge{NER Prediction}}')
        logger.info(self.state)

# def page_dashboard(state):
#    st.title(":chart_with_upwards_trend: Dashboard page")
#    display_state_values(state)


# def page_settings(state):
#    st.title(":wrench: Settings")
#    display_state_values(state)

#    st.write("---")
#    options = ["Hello", "World", "Goodbye"]
#    state.input = st.text_input("Set input value.", state.input or "")
#    state.slider = st.slider("Set slider value.", 1, 10, state.slider)
#    state.radio = st.radio("Set radio value.", options, options.index(state.radio) if state.radio else 0)
#    state.checkbox = st.checkbox("Set checkbox value.", state.checkbox)
#    state.selectbox = st.selectbox("Select value.", options, options.index(state.selectbox) if state.selectbox else 0)
#    state.multiselect = st.multiselect("Select value(s).", options, state.multiselect)

#    # Dynamic state assignments
#    for i in range(3):
#        key = f"State value {i}"
#        state[key] = st.slider(f"Set value {i}", 1, 10, state[key])


# def display_state_values(state):
#    st.write("Input state:", state.input)
#    st.write("Slider state:", state.slider)
#    st.write("Radio state:", state.radio)
#    st.write("Checkbox state:", state.checkbox)
#    st.write("Selectbox state:", state.selectbox)
#    st.write("Multiselect state:", state.multiselect)

#    for i in range(3):
#        st.write(f"Value {i}:", state[f"State value {i}"])

#    if st.button("Clear state"):
#        state.clear()
