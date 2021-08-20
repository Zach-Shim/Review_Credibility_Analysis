# Python Imports
import spacy


text = "I have purchased this product many times. It is really high quality and will still be good after many uses."
nlp = spacy.load("en_core_web_sm")
doc = nlp(text)
filtered_tokens = [token for token in doc if not token.is_stop]
token_list = [
    token.lemma_ 
    for token in doc
    ]

print(token_list)


