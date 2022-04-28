import logging

import streamlit as st
import os
from tei_entity_enricher.menu.ner_prediction import NERPrediction
from tei_entity_enricher.__init__ import __version__

from tei_entity_enricher.menu.ner_trainer import NERTrainer
from tei_entity_enricher.menu.ner_resume import NERResumer
from tei_entity_enricher.menu.ner_evaluate import NEREvaluator
import tei_entity_enricher.menu.tei_reader as tr
import tei_entity_enricher.menu.ner_task_def as ntd
import tei_entity_enricher.menu.tei_ner_map as tnm
import tei_entity_enricher.menu.tei_ner_gb as tng
import tei_entity_enricher.menu.tei_ner_writer_map as tnw
import tei_entity_enricher.menu.tei_postprocessing as pp
import tei_entity_enricher.menu.link_sug_cat as lsc
from tei_entity_enricher.util.aip_interface.processmanger.train import get_train_process_manager
from tei_entity_enricher.util.helper import (
    load_images,
    menu_TEI_reader_config,
    menu_entity_definition,
    menu_postprocessing,
    menu_TEI_read_mapping,
    menu_groundtruth_builder,
    menu_TEI_write_mapping,
    menu_NER_trainer,
    menu_NER_resume,
    menu_NER_evaluate,
    menu_NER_prediction,
    menu_link_sug_cat,
)

logger = logging.getLogger(__name__)


class Main:
    def __init__(self, args):
        if "shut_down_ntee" not in st.session_state:
            st.session_state["shut_down_ntee"]=False

        self.show(args)
        self.train_process=None

    def show_main_menu_old(self, pages, args):
        # Define sidebar as radiobuttons
        st.sidebar.radio(
            label="Main Menu", options=tuple(pages.keys()), index=int(args.start_state), key="main_menu_page"
        )

    def show_main_menu(self, pages, args):
        st.sidebar.markdown("#### Main Menu")
        if "main_menu_page" not in st.session_state:
            if args.start_state in pages.keys():
                st.session_state.main_menu_page = args.start_state
            else:
                st.session_state.main_menu_page = list(pages.keys())[0]
            if st.session_state.main_menu_page in [
                menu_NER_trainer,
                menu_NER_prediction,
                menu_NER_resume,
                menu_NER_evaluate,
            ]:
                st.session_state["mm_main_page1"] = True
            elif st.session_state.main_menu_page == menu_postprocessing:
                st.session_state["mm_main_page2"] = True
            else:
                st.session_state["mm_main_page0"] = True

        def change_main_page(changed_page_number, pages):
            st.session_state.main_menu_page = list(pages.keys())[changed_page_number]
            for i in range(len(list(pages.keys()))):
                if i != changed_page_number:
                    st.session_state["mm_main_page" + str(i)] = False

        st.sidebar.checkbox(
            label="Configurations",
            key="mm_main_page0",
            on_change=change_main_page,
            args=(
                0,
                pages,
            ),
        )
        if st.session_state.mm_main_page0:
            col1, col2 = st.sidebar.columns([0.1, 0.9])
            conf_pages = pages.copy()
            del conf_pages[menu_NER_trainer]
            del conf_pages[menu_NER_resume]
            del conf_pages[menu_NER_evaluate]
            del conf_pages[menu_NER_prediction]
            del conf_pages[menu_postprocessing]
            col2.radio(label="Submenu:", options=conf_pages, key="mm_submenu_radio0")
            st.session_state.main_menu_page = st.session_state.mm_submenu_radio0
        st.sidebar.checkbox(
            label="Training and Prediction",
            key="mm_main_page1",
            on_change=change_main_page,
            args=(
                1,
                pages,
            ),
        )
        if st.session_state.mm_main_page1:
            col1, col2 = st.sidebar.columns([0.1, 0.9])
            conf_pages = {
                menu_NER_trainer: pages[menu_NER_trainer],
                menu_NER_resume: pages[menu_NER_resume],
                menu_NER_evaluate: pages[menu_NER_evaluate],
                menu_NER_prediction: pages[menu_NER_prediction],
            }
            col2.radio(label="Submenu:", options=conf_pages, key="mm_submenu_radio1")
            st.session_state.main_menu_page = st.session_state.mm_submenu_radio1
        st.sidebar.checkbox(
            label=menu_postprocessing,
            key="mm_main_page2",
            on_change=change_main_page,
            args=(
                2,
                pages,
            ),
        )
        if st.session_state.mm_main_page2:
            st.session_state.main_menu_page = menu_postprocessing

    def show(self, args):
        st.set_page_config(layout="wide")  # Hiermit kann man die ganze Breite des Bildschirms ausschöpfen
        pages = {
            menu_TEI_reader_config: self.tei_reader,
            menu_entity_definition: self.ner_task_def,
            menu_TEI_read_mapping: self.tei_ner_map,
            menu_groundtruth_builder: self.gt_builder,
            menu_TEI_write_mapping: self.tei_ner_writer,
            menu_NER_trainer: self.ner_trainer,
            menu_NER_resume: self.ner_resume,
            menu_NER_evaluate: self.ner_evaluate,
            menu_NER_prediction: self.ner_prediction,
            menu_link_sug_cat: self.sd_sparql,
            menu_postprocessing: self.ner_postprocessing,
        }
        logo_frame, heading_frame = st.sidebar.columns([1, 2])
        heading_frame.latex("\\text{\Huge{N-TEE}}")
        st.sidebar.latex("\\text{\large{\\textbf{N}EISS - \\textbf{T}EI \\textbf{E}ntity \\textbf{E}nricher}}")

        neiss_logo, eu_fonds, eu_esf, mv_bm = load_images()

        # Include NEISS Logo
        logo_frame.image(neiss_logo)
        st.sidebar.write("Version: " + __version__)

        self.show_main_menu(pages, args)

        st.sidebar.markdown("### Funded by")
        # Include EU Logos
        st.sidebar.image(eu_fonds)
        colesf, colbm = st.sidebar.columns(2)
        colesf.image(eu_esf)
        colbm.image(mv_bm)

        # Display Shutdown-Button
        if st.sidebar.button("Shutdown NTEE"):
            self.shutdown_NTEE()
        else:
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

    def ner_resume(self):
        NERResumer()

    def ner_evaluate(self):
        NEREvaluator()

    def ner_prediction(self):
        NERPrediction()

    def sd_sparql(self):
        lsc.LinkSugCat()

    def ner_postprocessing(self):
        pp.TEINERPostprocessing()

    def shutdown_NTEE(self):
        train_process_manger=NERTrainer(show_menu=False).get_train_process()
        if train_process_manger.has_process():
            train_process_manger.stop()
            train_process_manger.clear_process()
            logger.info("train process terminated")

        resume_process_manger=NERResumer(show_menu=False).get_resume_process()
        if resume_process_manger.has_process():
            resume_process_manger.stop()
            resume_process_manger.clear_process()
            logger.info("resume process terminated")

        eval_process_manger=NEREvaluator(show_menu=False).get_eval_process()
        if eval_process_manger.has_process():
            eval_process_manger.stop()
            eval_process_manger.clear_process()
            logger.info("eval process terminated")

        predict_process_manger=NERPrediction(show_menu=False).get_predict_process()
        if predict_process_manger.has_process():
            predict_process_manger.stop()
            predict_process_manger.clear_process()
            logger.info("predict process terminated")


        st.latex("\\text{\Huge{NTEE was shut down}}")
        logger.info("NTEE was terminated.")
        os._exit(0)
