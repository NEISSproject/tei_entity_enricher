# TEI-Entity-Enricher
Software for Tagging Entities in TEI-Files automatically

# Install
activate virtualenv
cd <project_dir>  # contains tei_entity_enricher
pip install -e tei-entity-enricher
### Run main gui
ntee-start
### Run tests
activate virtualenv
pytest -v tei-entity-enricher/tei-entity-enricher/test

### Install ner_trainer
activate virtualenv

`cd <project_dir>`

`git clone https://github.com/NEISSproject/tf2_neiss_nlp.git`

`pip install tf2_neiss_nlp` (this will install tfaip and other dependencies)


