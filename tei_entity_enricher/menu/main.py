import logging

import streamlit as st
from tei_entity_enricher.menu.ner_prediction import NERPrediction

from tei_entity_enricher.menu.ner_trainer import NERTrainer
from tei_entity_enricher.util.SessionState import _get_state
from tei_entity_enricher.util.components import radio_widget
import tei_entity_enricher.menu.tei_reader as tr
import tei_entity_enricher.menu.ner_task_def as ntd
import tei_entity_enricher.menu.tei_ner_map as tnm
import tei_entity_enricher.menu.tei_ner_gb as tng
import tei_entity_enricher.menu.tei_ner_writer_map as tnw
import tei_entity_enricher.menu.tei_postprocessing as pp
from tei_entity_enricher.util.helper import load_images
from dataclasses import dataclass
from dataclasses_json import dataclass_json

logger = logging.getLogger(__name__)




@dataclass
@dataclass_json
class MainMenuParams:
    mm_page: str = None

@st.cache(allow_output_mutation=True)
def get_params() -> MainMenuParams:
    return MainMenuParams()


class Main:
    def __init__(self, args):
        self.state = None
        self.show(args)

    @property
    def main_menu_params(self) -> MainMenuParams:
        return get_params()

    def show(self, args):
        st.set_page_config(layout="wide")  # Hiermit kann man die ganze Breite des Bildschirms ausschöpfen
        self.state = _get_state()
        pages = {
            "TEI Reader Config": self.tei_reader,
            "NER Task Entity Definition": self.ner_task_def,
            "TEI Read NER Entity Mapping": self.tei_ner_map,
            "TEI NER Groundtruth Builder": self.gt_builder,
            "TEI NER Prediction Writer Mapping": self.tei_ner_writer,
            "NER Trainer": self.ner_trainer,
            "NER Prediction": self.ner_prediction,
            "NER Postprocessing": self.ner_postprocessing,
        }
        logo_frame, heading_frame = st.sidebar.beta_columns([1, 2])
        heading_frame.latex("\\text{\Huge{N-TEE}}")
        st.sidebar.latex("\\text{\large{\\textbf{N}EISS - \\textbf{T}EI \\textbf{E}ntity \\textbf{E}nricher}}")

        neiss_logo, eu_fonds, eu_esf, mv_bm = load_images()

        # Include NEISS Logo
        logo_frame.image(neiss_logo)

        # Define sidebar as radiobuttons
        self.main_menu_params.mm_page = radio_widget(
            "Main Menu",
            tuple(pages.keys()),
            tuple(pages.keys()).index(self.main_menu_params.mm_page) if self.main_menu_params.mm_page else int(args.start_state),
            st_element=st.sidebar
        )

        st.sidebar.markdown("### Funded by")
        # Include EU Logos
        st.sidebar.image(eu_fonds)
        colesf, colbm = st.sidebar.beta_columns(2)
        colesf.image(eu_esf)
        colbm.image(mv_bm)

        # Display the selected page with the session state
        pages[self.main_menu_params.mm_page]()

        # Mandatory to avoid rollbacks with widgets, must be called at the end of your app
        self.state.sync()

    def tei_reader(self):
        tr.TEIReader(state=self.state)

    def ner_task_def(self):
        ntd.NERTaskDef(state=self.state)

    def tei_ner_map(self):
        tnm.TEINERMap(state=self.state)

    def gt_builder(self):
        tng.TEINERGroundtruthBuilder(state=self.state)

    def tei_ner_writer(self):
        tnw.TEINERPredWriteMap(state=self.state)

    def ner_trainer(self):
        NERTrainer(state=self.state)

    def ner_prediction(self):
        NERPrediction(state=self.state)

    def ner_postprocessing(self):
        pp.TEINERPostprocessing(state=self.state)


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
