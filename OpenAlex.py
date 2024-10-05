# TODO: say what this file does.
from typing import Any
import requests
import json
import os

from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from isbnlib import NotValidISBNError, ISBNLibException
from isbnlib import get_canonical_isbn, to_isbn13


@dataclass
class OpenAlexItem:
    """
    Representation of an Open Alex API item. See, e.g.:
        https://api.openalex.org/works/W49327789
    """
    title: str
    openalex_id: str
    identifiers: dict[str, list[str]]
    isbn_13: list[str] | None
    publish_date: str | None
    authors: list[str] | None
    publishers: list[str] | None


def process_result(openalex_item: dict[str, Any]) -> dict[str, Any] | None:
    """
    Process an OpenAlex entry return a dictionary of the parsed metadata in the form:
        {isbn_13: {"title": "A Title", "isbn_13": ["012347689123"], "identifiers": {"open_alex": "W1234"}}, etc.
    fields: "title", "identifiers", "isbn_13", "publish_date", "authors"
    """
    edition_dict = {}

    # Try to get an ISBN 13 and an Open Alex ID, and exit if not possible.
    openalex_id = openalex_item["id"].rsplit("/", 1)[1]
    if doi := openalex_item.get("doi"):
        try:
            doi.split("/")[-1]
            if canonical_isbn := get_canonical_isbn(doi):
                isbn_13 = to_isbn13(canonical_isbn)
                edition_dict["isbn_13"] = [isbn_13]
                edition_dict["identifiers"] = {"open_alex": [openalex_id]}
            else:
                return

        except (NotValidISBNError, ISBNLibException) as e:
            print(f"Error processing ISBN: {e}")
            return
    else:
         return

    if publish_date := openalex_item.get("publication_year"):
         edition_dict["publish_date"] = str(publish_date)

    if title := openalex_item.get("title"):
         edition_dict["title"] = title

    if authorships := openalex_item.get("authorships"):
        authors = []
        for author in authorships:
            if author_name := author.get("author", {}).get("display_name"):
                authors.append(author_name)
        if authors:
            edition_dict["authors"] = authors

    return {edition_dict["isbn_13"]: edition_dict}

def fetch_books(max_records):
    next_cursor = "*"
    record_count = 0
    output_file = 'OpenAlex_isbn.jsonl'
    print("reached fetch_books")
    with requests.Session() as session, open(output_file, 'w') as f, ThreadPoolExecutor(max_workers=10) as executor:
        while True:
            open_alex = f"https://api.openalex.org/works?filter=type:book&sort=cited_by_count:desc&cursor={next_cursor}"
            try:
                response = session.get(open_alex)
                response.raise_for_status()  # Raises a HTTPError if the response status code is 4xx or 5xx
                data = response.json()
                next_cursor = data["meta"]["next_cursor"]
            except (requests.HTTPError, json.JSONDecodeError) as e:
                print(f"Error fetching or parsing data from OpenAlex: {e}")
                break

            if not data.get("results"):
                break

            results = list(executor.map(process_result, data["results"]))
            for result in results:
                if result is not None:
                    record_count += 1
                    if record_count > max_records:
                        break
                    else:
                        f.write(json.dumps(result) + '\n')

            if record_count > max_records:
                break

    print(f"Output file is saved at: {os.path.relpath(output_file)}")
