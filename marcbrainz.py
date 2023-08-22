import requests
import json
import csv
from pymarc import Record, Field, MARCWriter, Subfield
from datetime import datetime

# Prompt the user for the User-Agent string
user_agent = input("Enter your User-Agent string: ")

base_url = "https://musicbrainz.org/ws/2/"

# Read barcodes from the text file
barcodes = [line.strip() for line in open("barcodes.txt", "r")]

# get current datetime
time_now = datetime.now().strftime("%y%m%-d_%H%-M")
str_time_now = str(time_now)

# Specify the MARC file and CSV file paths
marc_file = "search_results" + str_time_now + ".mrc"
csv_file = "search_results" + str_time_now + ".csv"

# Initialize a MARC writer and a CSV list
marc_records = []
csv_rows = []

for barcode in barcodes:
    # Construct the URL for the search request
    search_url = f"{base_url}release/?query=barcode:{barcode}&fmt=json"

    # Make the API request
    headers = {"User-Agent": user_agent}
    response = requests.get(search_url, headers=headers)

    # Parse the JSON response
    data = response.json()

    if "releases" in data and data["releases"]:
        release = data["releases"][
            0
        ]  # Assuming you want information about the first matching release
        tracklist_url = f"{base_url}release/{release['id']}?inc=recordings&fmt=json"
        tracklist_response = requests.get(tracklist_url, headers=headers)
        tracklist_data = tracklist_response.json()

        # Create a new MARC record
        marc_record = Record()

        # Add barcode field (tag 024)
        marc_record.add_field(
            Field(
                tag="024",
                indicators=["1", " "],
                subfields=[Subfield(code="", value=barcode)],
            )
        )

        # Add Publisher / label_name (tag 028)
        # catalog_nu = release["catalog-number"]
        label_name = release["label-info"][0]["label"]["name"]
        marc_record.add_field(
            Field(
                tag="028",
                indicators=["0", "0"],
                subfields=[
                    #           Subfield(code="a", value=catalog_nu),
                    Subfield(code="b", value=label_name),
                ],
            )
        )

        # Add Bibliographic data field (tag 040)
        marc_record.add_field(
            Field(
                tag="040",
                indicators=[" ", " "],
                subfields=[
                    Subfield(code="a", value="Musicbrainz.org MBID " + release["id"]),
                    Subfield(code="d", value="Marcbrainz"),
                ],
            )
        )

        # Add artist field (tag 100)
        artist_name = release["artist-credit"][0]["artist"]["name"]
        marc_record.add_field(
            Field(
                tag="100",
                indicators=["1", " "],
                subfields=[Subfield(code="a", value=artist_name)],
            )
        )

        # Add title field (tag 245)
        title = release["title"]
        marc_record.add_field(
            Field(
                tag="245",
                indicators=["0", "0"],
                subfields=[Subfield(code="a", value=title)],
            )
        )

        # Add year field (tag 260) a = country, b = label_name, c = date
        label_name = release["label-info"][0]["label"]["name"]
        marc_record.add_field(
            Field(
                tag="260",
                indicators=[" ", " "],
                subfields=[
                    Subfield(code="a", value=release["country"]),
                    Subfield(code="b", value=label_name),
                    Subfield(code="c", value=release["date"]),
                ],
            )
        )

        # Add physical description field (tag 300)
        # this is more or less a placeholder. I think geting more details on numbers of discs requires an MBID search
        marc_record.add_field(
            Field(
                tag="300",
                indicators=[" ", " "],
                subfields=[
                    Subfield(code="a", value=release["media"][0]["format"]),
                    Subfield(code="b", value="digital, stereo"),
                    Subfield(code="c", value="120 mm"),
                ],
            )
        )

        # Add track info field (tag 505)
        track_info = " \n".join(
            [
                f"{track['position']}. {track['title']}"
                for track in tracklist_data["media"][0]["tracks"]
            ]
        )
        marc_record.add_field(
            Field(
                tag="505",
                indicators=["0", "0"],
                subfields=[Subfield(code="a", value=track_info)],
            )
        )

        # Add language note (tag 546)
        language = release["text-representation"]["language"]
        marc_record.add_field(
            Field(
                tag="546",
                indicators=[" ", " "],
                subfields=[Subfield(code="a", value=language)],
            )
        )

        # Append the MARC record to the list
        marc_records.append(marc_record)

        # Add the row to the CSV list
        csv_rows.append(
            [release["title"], artist_name, release["date"], track_info, release["id"]]
        )
    else:
        # Create a MARC record for 'Not found'
        marc_record = Record()
        marc_record.add_field(
            Field(
                tag="245",
                indicators=["0", "0"],
                subfields=[Subfield(code="a", value="Not found")],
            )
        )
        marc_records.append(marc_record)

        # Add a 'Not found' row to the CSV list
        csv_rows.append(["Not found", "N/A", "N/A", "N/A", "N/A"])

# Write the MARC records to the MARC file
with open(marc_file, "wb") as marc_output:
    writer = MARCWriter(marc_output)
    for marc_record in marc_records:
        writer.write(marc_record)

# Write the CSV rows to the CSV file
with open(csv_file, "w", newline="", encoding="utf-8") as csvfile:
    csvwriter = csv.writer(csvfile)
    csvwriter.writerow(
        ["Title", "Artist", "Release Date", "Track Info", "ID"]
    )  # CSV header
    csvwriter.writerows(csv_rows)

print(f"Results written to {marc_file} and {csv_file}")
