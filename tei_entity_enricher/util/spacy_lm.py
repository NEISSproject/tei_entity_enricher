import spacy

lang_dict = {
    "German": "de_core_news_sm",
    "English": "en_core_web_sm",
    "Multilingual": "xx_ent_wiki_sm",
    "French": "fr_core_news_sm",
    "Spanish": "es_core_news_sm",
}


def get_spacy_lm(lang):
    if not spacy.util.is_package(lang_dict[lang]):
        spacy.cli.download(lang_dict[lang])
    nlp = spacy.load(lang_dict[lang])
    if lang == "Multilingual":
        nlp.add_pipe("sentencizer")
    return nlp
