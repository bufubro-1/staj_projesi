#!/usr/bin/env python3
"""spaCy PER doğrulaması — .NET WebsiteScraper köprüsü."""
import sys

def main():
    if len(sys.argv) < 2:
        print("true")
        return

    text = sys.argv[1].strip()
    if not text:
        print("true")
        return

    try:
        import spacy
        nlp = spacy.load("xx_ent_wiki_sm")
        doc = nlp(text)
        if len(doc.ents) > 0 and not any(ent.label_ == "PER" for ent in doc.ents):
            print("false")
        else:
            print("true")
    except Exception:
        print("true")

if __name__ == "__main__":
    main()
