# TODO: say what this file does.
import json
from isbnlib import to_isbn13

def find_isbns(input_file, output_file, not_found_file):
    print("reached find_isbns")
    # Load ISBNs and their values into a dictionary
    # TODO: make this file an environment variable and update that commit.
    with open("OpenAlex_isbn.jsonl", "r") as f:
        openalex_isbn_dict = {list(data.keys())[0]: list(data.values())[0] for data in map(json.loads, f)}

    # Load ISBNdb metadata (in edition form, limited only to items in Open Alex), used to supplement
    # the metadata from OpenAlex
    with open("/home/scott/code/isbndb/openalex_isbndb_in_edition_form.jsonl") as f:
        isbndb_isbn_dict = {data["isbn_13"][0]: data for line in f if (data := json.loads(line))}

    # set of ISBNs for faster membership checks
    openalex_isbn_set = set(openalex_isbn_dict.keys())

    # Store the ISBNs found in both Open Library and Open Alex.
    overlapping_isbn_set = set()

    # Keep track of which editions we've seen, as we might see an edition under
    # multiple ISBN 13s, but we only need to record it as a hit/seen once, as we
    # only need to update the item with the OpenAlex ID once.
    seen_editions = set()

    # Look through the OpenLibrary dump for ISBNs from editions that are also
    # in OpenAlex.
    with open(output_file, "w") as details_file, open(input_file, "r") as ol_dump_file:
        for line in ol_dump_file:
            try:
                ol_json_str = line.split("\t")[-1]
                ol_json_data = json.loads(ol_json_str)
            except Exception as e:
                print(f"Error parsing OpenLibrary JSON: {e}")
                continue

            # Convert everything to an ISBN 13 and use those, even if Open Library
            # only records an ISBN 10. This is to easily dedupe ISBN 10 <-> ISBN 13.
            isbn_10s = ol_json_data.get("isbn_10", [])
            isbn_13s = ol_json_data.get("isbn_13", [])
            isbns = set(isbn_13s + [to_isbn13(isbn_10) for isbn_10 in isbn_10s])

            # Record overlapping ISBNs as ISBN 13.
            for isbn in isbns:
                if isbn not in openalex_isbn_set:
                    continue

                overlapping_isbn_set.add(isbn)

                ol_key = ol_json_data["key"]
                if ol_key not in seen_editions:
                    seen_editions.add(ol_key)
                    # ISBNdb seems to have better title data for some reason.
                    if isbndb_title := isbndb_isbn_dict.get("isbn", {}).get("title"):
                        merged_metadata = isbndb_isbn_dict.get("isbn", {}) | openalex_isbn_dict[isbn] | {"title": isbndb_title}
                    else:
                        merged_metadata = isbndb_isbn_dict.get("isbn", {}) | openalex_isbn_dict[isbn]

                    result = {"openalex_metadata_edition": merged_metadata, "OpenAlex": openalex_isbn_dict[isbn]["identifiers"].get("open_alex")[0], "ISBN": isbn, "edition_key": ol_key}
                    details_file.write(json.dumps(result) + "\n")

    # Record ISBNs (as ISBN 13) not in Open Library and the corresponding OpenAlex ID.
    # ISBNdb seems to have better title data for some reason.
    non_overlapping_isbns = {isbn: isbndb_isbn_dict.get(isbn, {}) | openalex_isbn_dict[isbn] | ({"title": isbndb_isbn_dict.get(isbn, {}).get("title")} if isbndb_isbn_dict.get(isbn, {}).get("title") else {}) for isbn in openalex_isbn_set - overlapping_isbn_set}

    with open(not_found_file, "w") as not_found_file:
        for isbn, value in non_overlapping_isbns.items():
            not_found_file.write(json.dumps({"openalex_metadata_edition": value, "ISBN": isbn, "OpenAlex": value["identifiers"].get("open_alex")[0]}) + "\n")
   
