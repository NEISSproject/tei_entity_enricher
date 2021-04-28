# TEI-Entity-Enricher
Software for Tagging Entities in TEI-Files automatically

# Install
activate virtualenv
cd <project_dir>  # contains tei_entity_enricher
pip install -e tei_entity_enricher
### Run main gui
ntee-start
### Run tests
activate virtualenv
pytest -v tei_entity_enricher/test