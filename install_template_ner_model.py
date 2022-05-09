import os
import urllib
import zipfile
from tei_entity_enricher.util.helper import makedir_if_necessary
from tei_entity_enricher.util import config_io
import logging
logger = logging.getLogger(__name__)


def download(url: str, dest_filename: str):
    logging.info("Downloading template ner models. (This may take a while)");
    urllib.request.urlretrieve(url, dest_filename)

def fix_template_path(dest_folder):
    def fix_tp_dict(tp_dict):
        if ("scenario" in tp_dict.keys()):
            if ("model" in tp_dict["scenario"].keys() and "tags_fn_" in tp_dict["scenario"]["model"].keys() and tp_dict["scenario"]["model"]["tags_fn_"]=="/home/ksperfeld/devel/projects/NTEE/data/tags/ner_germeval_wp.txt"):
                tp_dict["scenario"]["model"]["tags_fn_"]=os.path.join("templates","models_ner","germeval","best","resources","ner_germeval_wp.txt")
            if ("evaluator" in tp_dict["scenario"].keys() and "tags_fn" in tp_dict["scenario"]["evaluator"].keys() and tp_dict["scenario"]["evaluator"]["tags_fn"]=="/home/ksperfeld/devel/projects/NTEE/data/tags/ner_germeval_wp.txt"):
                tp_dict["scenario"]["evaluator"]["tags_fn"]=os.path.join("templates","models_ner","germeval","best","resources","ner_germeval_wp.txt")
        return tp_dict
    tp_file=os.path.join(dest_folder,"germeval","trainer_params.json")
    if os.path.isfile(tp_file):
        trainer_params=config_io.get_config(tp_file)
        config_io.set_config(fix_tp_dict(trainer_params))
    tp_file=os.path.join(dest_folder,"germeval","best","trainer_params.json")
    if os.path.isfile(tp_file):
        trainer_params=config_io.get_config(tp_file)
        config_io.set_config(fix_tp_dict(trainer_params))


def install_template_models():
    dest_folder=os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)),"ner_trainer","templates","models_ner")
    makedir_if_necessary(dest_folder)
    urllink="https://unibox.uni-rostock.de/dl/fiAHgWX9ku24ZdqSwhv6vT9v/.dir"
    try:
        download(urllink, dest_filename=os.path.join(dest_folder,"templates.zip"))
        logging.info("Extract ner template models.")
        with zipfile.ZipFile(os.path.join(dest_folder,"templates.zip"), 'r') as zip_ref:
            zip_ref.extractall(dest_folder)
        fix_template_path(dest_folder)
        logging.info("Succesfully installed ner template models.")
    except urllib.error.HTTPError:
        logging.error(f"Couldn't download ner template models from {urllink}")


