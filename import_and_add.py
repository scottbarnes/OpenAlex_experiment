import json
import os

from typing import Final

from olclient.openlibrary import OpenLibrary
from collections import namedtuple

BOT_USERNAME: Final = os.getenv("BOT_USERNAME", "openlibrary@example.com")
BOT_PASSWORD: Final = os.getenv("BOT_PASSWORD", "admin123")
OL_HOST: Final = os.getenv("OL_HOST", "http://localhost:8080")

Credentials = namedtuple("Credentials", ["username", "password"])
credentials = Credentials(BOT_USERNAME, BOT_PASSWORD)

def import_isbns(filename):
    with open(filename, "r") as f:
        isbn_dict = {data['ISBN']: data['OpenAlex'].split('/')[-1] for data in map(json.loads, f)}
    return isbn_dict

def add_identifiers(isbn_dict):
    
    ol = OpenLibrary(base_url=OL_HOST, credentials=credentials)

    for isbn , id in isbn_dict.items():
        record = ol.session.get(f"{OL_HOST}/isbn/{isbn}.json")
        record = record.json()
        key = record.get("key").split("/")[-1]
        edition = ol.Edition.get(key)
        edition.add_id("OpenAlex",id)
        print(edition.identifiers)
        edition.save("edit adds an OpenAlex identifier.")

def main(filename):
    print("reached main")
    isbn_dict = import_isbns(filename) # Hits.jsonl/Not_Found.jsonl
    add_identifiers(isbn_dict)
