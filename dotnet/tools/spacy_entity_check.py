#!/usr/bin/env python3
"""spaCy PER/ORG kontrolü — SerpAPI başlık doğrulama köprüsü."""
import json
import sys


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"is_per": False, "is_org": False}))
        return

    text = sys.argv[1].strip()
    if not text:
        print(json.dumps({"is_per": False, "is_org": False}))
        return

    try:
        import spacy
        nlp = spacy.load("xx_ent_wiki_sm")
        doc = nlp(text)
        is_per = any(ent.label_ == "PER" for ent in doc.ents)
        is_org = any(ent.label_ == "ORG" for ent in doc.ents)
        print(json.dumps({"is_per": is_per, "is_org": is_org}))
    except Exception:
        print(json.dumps({"is_per": False, "is_org": False}))


if __name__ == "__main__":
    main()
