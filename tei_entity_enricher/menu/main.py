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
import tei_entity_enricher.menu.sd_sparql as sparQL
from tei_entity_enricher.util.helper import (
    load_images,
    menu_TEI_reader_config,
    menu_entity_definition,
    menu_postprocessing,
    menu_TEI_read_mapping,
    menu_groundtruth_builder,
    menu_TEI_write_mapping,
    menu_NER_trainer,
    menu_NER_prediction,
    menu_sparql_queries,
)

logger = logging.getLogger(__name__)


class Main:
    def __init__(self, args):
        self.show(args)

    def show_main_menu(self, pages, args):
        # Define sidebar as radiobuttons
        st.sidebar.radio(
            label="Main Menu", options=tuple(pages.keys()), index=int(args.start_state), key="main_menu_page"
        )

    def show_main_menu_new(self, pages, args):
        if "main_menu_page" not in st.session_state:
            if args.start_state in pages.keys():
                st.session_state.main_menu_page = args.start_state
            else:
                st.session_state.main_menu_page = list(pages.keys())[0]
            st.session_state["mm_page" + str(list(pages.keys()).index(st.session_state.main_menu_page))] = True

        def change_page(changed_page_number, pages):
            st.session_state.main_menu_page = list(pages.keys())[changed_page_number]
            for i in range(len(list(pages.keys()))):
                if i != changed_page_number:
                    st.session_state["mm_page" + str(i)] = False

        conf_expander = st.sidebar.expander("Configurations", expanded=True)
        with conf_expander:
            st.checkbox(
                label=list(pages.keys())[0],
                key="mm_page0",
                on_change=change_page,
                args=(
                    0,
                    pages,
                ),
            )
            st.checkbox(
                label=list(pages.keys())[1],
                key="mm_page1",
                on_change=change_page,
                args=(
                    1,
                    pages,
                ),
            )
            st.checkbox(
                label=list(pages.keys())[2],
                key="mm_page2",
                on_change=change_page,
                args=(
                    2,
                    pages,
                ),
            )
            st.checkbox(
                label=list(pages.keys())[3],
                key="mm_page3",
                on_change=change_page,
                args=(
                    3,
                    pages,
                ),
            )
            st.checkbox(
                label=list(pages.keys())[4],
                key="mm_page4",
                on_change=change_page,
                args=(
                    4,
                    pages,
                ),
            )
            st.checkbox(
                label=list(pages.keys())[7],
                key="mm_page7",
                on_change=change_page,
                args=(
                    7,
                    pages,
                ),
            )
        nn_expander = st.sidebar.expander("Training and Prediction", expanded=True)
        with nn_expander:
            st.checkbox(
                label=list(pages.keys())[5],
                key="mm_page5",
                on_change=change_page,
                args=(
                    5,
                    pages,
                ),
            )
            st.checkbox(
                label=list(pages.keys())[6],
                key="mm_page6",
                on_change=change_page,
                args=(
                    6,
                    pages,
                ),
            )
        pp_expander = st.sidebar.expander(menu_postprocessing, expanded=True)
        with pp_expander:
            st.checkbox(
                label=list(pages.keys())[8],
                key="mm_page8",
                on_change=change_page,
                args=(
                    8,
                    pages,
                ),
            )

    def show_main_menu_new2(self, pages, args):
        if "main_menu_page" not in st.session_state:
            if args.start_state in pages.keys():
                st.session_state.main_menu_page = args.start_state
            else:
                st.session_state.main_menu_page = list(pages.keys())[0]
            st.session_state["mm_page" + str(list(pages.keys()).index(st.session_state.main_menu_page))] = True

        def change_page(changed_page_number, pages):
            st.session_state.main_menu_page = list(pages.keys())[changed_page_number]
            for i in range(len(list(pages.keys()))):
                if i != changed_page_number:
                    st.session_state["mm_page" + str(i)] = False

        st.sidebar.markdown("#### Configurations")
        st.sidebar.checkbox(
            label=list(pages.keys())[0],
            key="mm_page0",
            on_change=change_page,
            args=(
                0,
                pages,
            ),
        )
        st.sidebar.checkbox(
            label=list(pages.keys())[1],
            key="mm_page1",
            on_change=change_page,
            args=(
                1,
                pages,
            ),
        )
        st.sidebar.checkbox(
            label=list(pages.keys())[2],
            key="mm_page2",
            on_change=change_page,
            args=(
                2,
                pages,
            ),
        )
        st.sidebar.checkbox(
            label=list(pages.keys())[3],
            key="mm_page3",
            on_change=change_page,
            args=(
                3,
                pages,
            ),
        )
        st.sidebar.checkbox(
            label=list(pages.keys())[4],
            key="mm_page4",
            on_change=change_page,
            args=(
                4,
                pages,
            ),
        )
        st.sidebar.checkbox(
            label=list(pages.keys())[7],
            key="mm_page7",
            on_change=change_page,
            args=(
                7,
                pages,
            ),
        )
        st.sidebar.markdown("#### Training and Prediction")
        st.sidebar.checkbox(
            label=list(pages.keys())[5],
            key="mm_page5",
            on_change=change_page,
            args=(
                5,
                pages,
            ),
        )
        st.sidebar.checkbox(
            label=list(pages.keys())[6],
            key="mm_page6",
            on_change=change_page,
            args=(
                6,
                pages,
            ),
        )
        st.sidebar.markdown(f"#### {menu_postprocessing}")
        st.sidebar.checkbox(
            label=list(pages.keys())[8],
            key="mm_page8",
            on_change=change_page,
            args=(
                8,
                pages,
            ),
        )

    def show_main_menu_new3(self, pages, args):
        options = ["Configurations", "Training and Prediction", menu_postprocessing]
        st.sidebar.selectbox(label="Main Menu", options=options, key="mm_main_selbox")
        if options.index(st.session_state.mm_main_selbox) == 0:
            conf_pages = pages.copy()
            del conf_pages[menu_NER_trainer]
            del conf_pages[menu_NER_prediction]
            del conf_pages[menu_postprocessing]
        elif options.index(st.session_state.mm_main_selbox) == 1:
            conf_pages = {menu_NER_trainer: pages[menu_NER_trainer], menu_NER_prediction: pages[menu_NER_prediction]}
        else:
            st.session_state.main_menu_page = menu_postprocessing
        if options.index(st.session_state.mm_main_selbox) < 2:
            st.sidebar.radio(
                label="Submenu",
                options=conf_pages,
                key="mm_submenu_radio" + str(options.index(st.session_state.mm_main_selbox)),
            )
            st.session_state.main_menu_page = st.session_state[
                "mm_submenu_radio" + str(options.index(st.session_state.mm_main_selbox))
            ]

    def show_main_menu_new4(self, pages, args):
        st.sidebar.markdown("#### Main Menu")
        if "main_menu_page" not in st.session_state:
            if args.start_state in pages.keys():
                st.session_state.main_menu_page = args.start_state
            else:
                st.session_state.main_menu_page = list(pages.keys())[0]
            if st.session_state.main_menu_page in [menu_NER_trainer, menu_NER_prediction]:
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
            del conf_pages[menu_NER_prediction]
            del conf_pages[menu_postprocessing]
            col2.radio(label="", options=conf_pages, key="mm_submenu_radio0")
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
            conf_pages = {menu_NER_trainer: pages[menu_NER_trainer], menu_NER_prediction: pages[menu_NER_prediction]}
            col2.radio(label="", options=conf_pages, key="mm_submenu_radio1")
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
            menu_NER_prediction: self.ner_prediction,
            menu_sparql_queries: self.sd_sparql,
            menu_postprocessing: self.ner_postprocessing,
        }
        logo_frame, heading_frame = st.sidebar.columns([1, 2])
        heading_frame.latex("\\text{\Huge{N-TEE}}")
        st.sidebar.latex("\\text{\large{\\textbf{N}EISS - \\textbf{T}EI \\textbf{E}ntity \\textbf{E}nricher}}")

        neiss_logo, eu_fonds, eu_esf, mv_bm = load_images()

        # Include NEISS Logo
        logo_frame.image(neiss_logo)

        self.show_main_menu_new4(pages, args)

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

    def sd_sparql(self):
        sparQL.SparQLDef()

    def ner_postprocessing(self):
        pp.TEINERPostprocessing()
