import json
from isbnlib import to_isbn13, to_isbn10

def find_isbns(input_file, output_file, not_found_file):
    print("reached find_isbns")
    # Load ISBNs and their values into a dictionary
    with open("OpenAlex_isbn.jsonl", "r") as f:
        isbn_dict = {list(data.keys())[0]: list(data.values())[0] for data in map(json.loads, f)}

    # set of ISBNs for faster membership checks
    isbn_set = set(isbn_dict.keys())

    # Store the found ISBNs in a set
    found_isbn_set = set()

    with open(output_file, "w") as details_file, open(input_file, "r") as file:
        for line in file:
            try:
                json_str = line.split("\t")[-1]
                json_data = json.loads(json_str)
            except Exception as e:
                print(f"Error parsing JSON: {e}")
                continue

            isbn = None
            if json_data.get("isbn_13"):
                isbn = json_data.get("isbn_13")[0]
                if isbn in isbn_set:
                    found_isbn_set.add(isbn)
                    result = {"OpenAlex": isbn_dict[isbn], "ISBN": isbn, "edition": json_data["key"]}
                    details_file.write(json.dumps(result) + "\n")
            elif json_data.get("isbn_10"):
                isbn = to_isbn13(json_data.get("isbn_10")[0])
                if isbn in isbn_set:
                    found_isbn_set.add(isbn)
                    result = {"OpenAlex": isbn_dict[isbn], "ISBN": to_isbn10(isbn), "edition": json_data["key"]}
                    details_file.write(json.dumps(result) + "\n")

    # Create a dictionary of not found ISBNs and their values
    not_found_isbn_dict = {isbn: isbn_dict[isbn] for isbn in isbn_set - found_isbn_set}

    with open(not_found_file, "w") as not_found_file:
        for isbn, value in not_found_isbn_dict.items():
            not_found_file.write(json.dumps({"ISBN": isbn, "OpenAlex": value}) + "\n")
   