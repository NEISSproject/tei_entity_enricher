# TEI-Entity-Enricher
Software for Tagging Entities in TEI-Files automatically

# Install
`activate virtualenv`

`cd <project_dir>` contains tei_entity_enricher

`pip install -e tei_entity_enricher`
### Run main gui
`ntee-start`
### Run tests
`activate virtualenv`

`pytest -v tei_entity_enricher/tei_entity_enricher/test`

### Install ner_trainer
`activate virtualenv`

`cd <project_dir>`

`git clone https://github.com/NEISSproject/tf2_neiss_nlp.git`

`pip install ./tf2_neiss_nlp` (for linux; this will install tfaip and other dependencies)
`pip install .\tf2_neiss_nlp` (for windows; this will install tfaip and other dependencies)


