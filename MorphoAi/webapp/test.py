import spacy

nlp = spacy.load("nl_core_news_sm")

def get_number(word):
    doc = nlp(word)
    for token in doc:
        return token.morph.get("Number")[0] if token.morph.get("Number") else "Unknown"

words = ["kat", "katten", "huis", "huizen", "auto's"]
for word in words:
    print(f"{word}: {get_number(word)}")
