import os
import urllib
import zipfile
from tei_entity_enricher.util.helper import makedir_if_necessary
import logging
logger = logging.getLogger(__name__)


def download(url: str, dest_filename: str):
    logging.info("Downloading template ner models. (This may take a while)");
    urllib.request.urlretrieve(url, dest_filename)

def install_template_models():
    dest_folder=os.path.join(os.path.abspath(os.path.join(os.getcwd(), os.pardir)),"ner_trainer","templates","models_ner")
    makedir_if_necessary(dest_folder)
    urllink="https://unibox.uni-rostock.de/dl/fi2SJcYwmX2oKXjRkaUrci89/.dir"
    try:
        download(urllink, dest_filename=os.path.join(dest_folder,"templates.zip"))
        logging.info("Extract ner template models.")
        with zipfile.ZipFile(os.path.join(dest_folder,"templates.zip"), 'r') as zip_ref:
            zip_ref.extractall(dest_folder)
        logging.info("Succesfully installed ner template models.")
    except urllib.error.HTTPError:
        logging.error(f"Couldn't download ner template models from {urllink}")


