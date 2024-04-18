import json
import os

from collections import namedtuple
from pathlib import Path
from typing import Final

from olclient.openlibrary import OpenLibrary
from requests import JSONDecodeError

BOT_USERNAME: Final = os.getenv("BOT_USERNAME", "openlibrary@example.com")
BOT_PASSWORD: Final = os.getenv("BOT_PASSWORD", "admin123")
OL_HOST: Final = os.getenv("OL_HOST", "http://localhost:8080")
ISBN_ENDPOINT_MISS_FILE: Final = os.getenv("ISBN_ENDPOINT_MISS_FILE")

Credentials = namedtuple("Credentials", ["username", "password"])
credentials = Credentials(BOT_USERNAME, BOT_PASSWORD)

def import_isbns(filename):
    with open(filename, "r") as f:
        isbn_dict = {data['ISBN']: data['OpenAlex'].split('/')[-1] for data in map(json.loads, f)}
    return isbn_dict

def add_identifiers(isbn_dict):
    
    ol = OpenLibrary(base_url=OL_HOST, credentials=credentials)

    for isbn, id in isbn_dict.items():
        record = ol.session.get(f"{OL_HOST}/isbn/{isbn}.json?high_priority=true")
        try:
            record = record.json()
        except JSONDecodeError:
            if ISBN_ENDPOINT_MISS_FILE:
                with Path(ISBN_ENDPOINT_MISS_FILE).open("a") as file:
                    file.write(json.dumps({"ISBN": isbn, "OpenAlex": id})+"\n")
            continue

        key = record.get("key").split("/")[-1]
        if not (edition := ol.Edition.get(key)):
            continue

        if "open_alex" not in edition.identifiers:
            edition.add_id("open_alex", id)
            edition.save("Add an OpenAlex identifier.")

def main(filename):
    isbn_dict = import_isbns(filename) # Hits.jsonl/Not_Found.jsonl
    add_identifiers(isbn_dict)
