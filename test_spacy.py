import spacy

nlp = spacy.load("en_core_web_sm")
doc = nlp("This is a test.")
print([token.text for token in doc])
