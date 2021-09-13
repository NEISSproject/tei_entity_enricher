import logging

import streamlit as st
from tei_entity_enricher.menu.ner_prediction import NERPrediction

from tei_entity_enricher.menu.ner_trainer import NERTrainer
import tei_entity_enricher.menu.tei_reader as tr
import tei_entity_enricher.menu.ner_task_def as ntd
import tei_entity_enricher.menu.tei_ner_map as tnm
import tei_entity_enricher.menu.tei_ner_gb as tng
import tei_entity_enricher.menu.tei_ner_writer_map as tnw
import tei_entity_enricher.menu.tei_postprocessing as pp
from tei_entity_enricher.util.helper import load_images

logger = logging.getLogger(__name__)


class Main:
    def __init__(self, args):
        self.show(args)

    def show(self, args):
        st.set_page_config(layout="wide")  # Hiermit kann man die ganze Breite des Bildschirms ausschöpfen
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
        logo_frame, heading_frame = st.sidebar.columns([1, 2])
        heading_frame.latex("\\text{\Huge{N-TEE}}")
        st.sidebar.latex("\\text{\large{\\textbf{N}EISS - \\textbf{T}EI \\textbf{E}ntity \\textbf{E}nricher}}")

        neiss_logo, eu_fonds, eu_esf, mv_bm = load_images()

        # Include NEISS Logo
        logo_frame.image(neiss_logo)

        # Define sidebar as radiobuttons
        st.sidebar.radio(
            label="Main Menu", options=tuple(pages.keys()), index=int(args.start_state), key="main_menu_page"
        )

        st.sidebar.markdown("### Funded by")
        # Include EU Logos
        st.sidebar.image(eu_fonds)
        colesf, colbm = st.sidebar.columns(2)
        colesf.image(eu_esf)
        colbm.image(mv_bm)

        # Display the selected page
        pages[st.session_state.main_menu_page]()

    def tei_reader(self):
        tr.TEIReader()

    def ner_task_def(self):
        ntd.NERTaskDef()

    def tei_ner_map(self):
        tnm.TEINERMap()

    def gt_builder(self):
        tng.TEINERGroundtruthBuilder()

    def tei_ner_writer(self):
        tnw.TEINERPredWriteMap()

    def ner_trainer(self):
        NERTrainer()

    def ner_prediction(self):
        NERPrediction()

    def ner_postprocessing(self):
        pp.TEINERPostprocessing()
