# TEIEntityEnricher
Software for Tagging Entities in TEI-Files automatically

# Install
activate virtualenv
cd <project_dir>  # contains TEIEntityEnricher
pip install -e TEIEntityEnricher
### Run main gui
ntee-start
### Run tests
activate virtualenv
pytest -v TEIEntityEnricher/test