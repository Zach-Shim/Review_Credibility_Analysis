# Python Imports
import spacy


text = "I bought these because they're cheap. Use these if you need something done fast, they aren't the greatest"
nlp = spacy.load("en_core_web_sm")
doc = nlp(text)
filtered_tokens = [token for token in doc if not token.is_stop]
token_list = [
    f"Token: {token}, lemma: {token.lemma_}" 
    for token in doc
    ]

print(token_list)
print(filtered_tokens[0].vector)


