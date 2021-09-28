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
from tei_entity_enricher.util.helper import load_images

logger = logging.getLogger(__name__)


class Main:
    def __init__(self, args):
        self.show(args)

    def show_main_menu(self,pages,args):
        # Define sidebar as radiobuttons
        st.sidebar.radio(
            label="Main Menu", options=tuple(pages.keys()), index=int(args.start_state), key="main_menu_page"
        )

    def show_main_menu_new(self,pages,args):
        if "main_menu_page" not in st.session_state:
            if args.start_state in pages.keys():
                st.session_state.main_menu_page=args.start_state
            else:
                st.session_state.main_menu_page=list(pages.keys())[0]
            st.session_state["mm_page"+str(list(pages.keys()).index(st.session_state.main_menu_page))]=True
        def change_page(changed_page_number,pages):
            st.session_state.main_menu_page=list(pages.keys())[changed_page_number]
            for i in range(len(list(pages.keys()))):
                if i!=changed_page_number:
                    st.session_state["mm_page"+str(i)]=False
        conf_expander = st.sidebar.expander("Configurations",expanded=True)
        with conf_expander:
            st.checkbox(label=list(pages.keys())[0],key='mm_page0',on_change=change_page, args=(0,pages,))
            st.checkbox(label=list(pages.keys())[1],key='mm_page1',on_change=change_page, args=(1,pages,))
            st.checkbox(label=list(pages.keys())[2],key='mm_page2',on_change=change_page, args=(2,pages,))
            st.checkbox(label=list(pages.keys())[3],key='mm_page3',on_change=change_page, args=(3,pages,))
            st.checkbox(label=list(pages.keys())[4],key='mm_page4',on_change=change_page, args=(4,pages,))
            st.checkbox(label=list(pages.keys())[7],key='mm_page7',on_change=change_page, args=(7 ,pages,))
        nn_expander = st.sidebar.expander("Training and Prediction",expanded=True)
        with nn_expander:
            st.checkbox(label=list(pages.keys())[5],key='mm_page5',on_change=change_page, args=(5,pages,))
            st.checkbox(label=list(pages.keys())[6],key='mm_page6',on_change=change_page, args=(6,pages,))
        pp_expander = st.sidebar.expander("Postprocessing",expanded=True)
        with pp_expander:
            st.checkbox(label=list(pages.keys())[8],key='mm_page8',on_change=change_page, args=(8,pages,))

    def show_main_menu_new2(self,pages,args):
        if "main_menu_page" not in st.session_state:
            if args.start_state in pages.keys():
                st.session_state.main_menu_page=args.start_state
            else:
                st.session_state.main_menu_page=list(pages.keys())[0]
            st.session_state["mm_page"+str(list(pages.keys()).index(st.session_state.main_menu_page))]=True
        def change_page(changed_page_number,pages):
            st.session_state.main_menu_page=list(pages.keys())[changed_page_number]
            for i in range(len(list(pages.keys()))):
                if i!=changed_page_number:
                    st.session_state["mm_page"+str(i)]=False
        st.sidebar.markdown("#### Configurations")
        st.sidebar.checkbox(label=list(pages.keys())[0],key='mm_page0',on_change=change_page, args=(0,pages,))
        st.sidebar.checkbox(label=list(pages.keys())[1],key='mm_page1',on_change=change_page, args=(1,pages,))
        st.sidebar.checkbox(label=list(pages.keys())[2],key='mm_page2',on_change=change_page, args=(2,pages,))
        st.sidebar.checkbox(label=list(pages.keys())[3],key='mm_page3',on_change=change_page, args=(3,pages,))
        st.sidebar.checkbox(label=list(pages.keys())[4],key='mm_page4',on_change=change_page, args=(4,pages,))
        st.sidebar.checkbox(label=list(pages.keys())[7],key='mm_page7',on_change=change_page, args=(7 ,pages,))
        st.sidebar.markdown("#### Training and Prediction")
        st.sidebar.checkbox(label=list(pages.keys())[5],key='mm_page5',on_change=change_page, args=(5,pages,))
        st.sidebar.checkbox(label=list(pages.keys())[6],key='mm_page6',on_change=change_page, args=(6,pages,))
        st.sidebar.markdown("#### Postprocessing")
        st.sidebar.checkbox(label=list(pages.keys())[8],key='mm_page8',on_change=change_page, args=(8,pages,))

    def show_main_menu_new3(self,pages,args):
        options=["Configurations","Training and Prediction","Postprocessing"]
        st.sidebar.selectbox(label='Main Menu',options=options,key='mm_main_selbox')
        if options.index(st.session_state.mm_main_selbox)==0:
            conf_pages=pages.copy()
            del conf_pages["NER Trainer"]
            del conf_pages["NER Prediction"]
            del conf_pages["NER Postprocessing"]
        elif options.index(st.session_state.mm_main_selbox)==1:
            conf_pages={"NER Trainer":pages["NER Trainer"],"NER Prediction":pages["NER Prediction"]}
        else:
            st.session_state.main_menu_page="NER Postprocessing"
        if options.index(st.session_state.mm_main_selbox)<2:
            st.sidebar.radio(label="Submenu",options=conf_pages,key='mm_submenu_radio'+str(options.index(st.session_state.mm_main_selbox)))
            st.session_state.main_menu_page=st.session_state['mm_submenu_radio'+str(options.index(st.session_state.mm_main_selbox))]

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
            "SparQL Queries": self.sd_sparql,
            "NER Postprocessing": self.ner_postprocessing,
        }
        logo_frame, heading_frame = st.sidebar.columns([1, 2])
        heading_frame.latex("\\text{\Huge{N-TEE}}")
        st.sidebar.latex("\\text{\large{\\textbf{N}EISS - \\textbf{T}EI \\textbf{E}ntity \\textbf{E}nricher}}")

        neiss_logo, eu_fonds, eu_esf, mv_bm = load_images()

        # Include NEISS Logo
        logo_frame.image(neiss_logo)

        self.show_main_menu_new3(pages, args)

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
