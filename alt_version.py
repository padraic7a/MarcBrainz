```python
import requests
import json
import csv
from pymarc import Record, Field, MARCWriter, Subfield
from datetime import datetime
import logging
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

# Set up logging
logging.basicConfig(filename='marcbrainz.log', level=logging.INFO)

# Prompt the user for the User-Agent string
user_agent = input("Enter your User-Agent string: ")

# Prompt the user for the Discogs API token
discogs_token = input("Enter your Discogs API token: ")

base_url_musicbrainz = "https://musicbrainz.org/ws/2/"
base_url_discogs = "https://api.discogs.com/"

# Read barcodes from the text file
try:
    with open("barcodes.txt", "r") as file:
        barcodes = [line.strip() for line in file]
except FileNotFoundError:
    logging.error("barcodes.txt file not found.")
    raise

# Get current datetime
time_now = datetime.now().strftime("%y%m%d_%H%M")
str_time_now = str(time_now)

# Specify the MARC file and CSV file paths
marc_file = f"search_results_{str_time_now}.mrc"
csv_file = f"search_results_{str_time_now}.csv"

# Initialize a MARC writer and a CSV list
marc_records = []
csv_rows = []

# Set up a session with retry mechanism
session = requests.Session()
retry = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
adapter = HTTPAdapter(max_retries=retry)
session.mount("http://", adapter)
session.mount("https://", adapter)

for barcode in barcodes:
    logging.info(f"Processing barcode {barcode}")

    # Construct the URL for the MusicBrainz search request
    search_url_mb = f"{base_url_musicbrainz}release/?query=barcode:{barcode}&fmt=json"

    try:
        # Make the MusicBrainz API request
        headers = {"User-Agent": user_agent}
        response_mb = session.get(search_url_mb, headers=headers)
        response_mb.raise_for_status()
        data_mb = response_mb.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error: {e} for barcode {barcode}")
        continue
    except json.JSONDecodeError:
        logging.error(f"Failed to parse JSON response for barcode {barcode}")
        continue

    if "releases" in data_mb and data_mb["releases"]:
        release = data_mb["releases"]  # Assuming you want information about the first matching release
        tracklist_url_mb = f"{base_url_musicbrainz}release/{release['id']}?inc=recordings&fmt=json"
        
        try:
            tracklist_response_mb = session.get(tracklist_url_mb, headers=headers)
            tracklist_response_mb.raise_for_status()
            tracklist_data_mb = tracklist_response_mb.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error: {e} for release ID {release['id']}")
            continue
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON response for release ID {release['id']}")
            continue

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
        label_name = release["label-info"]["label"]["name"]
        marc_record.add_field(
            Field(
                tag="028",
                indicators=["0", "0"],
                subfields=[
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
        artist_name = release["artist-credit"]["artist"]["name"]
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
        label_name = release["label-info"]["label"]["name"]
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
        marc_record.add_field(
            Field(
                tag="300",
                indicators=[" ", " "],
                subfields=[
                    Subfield(code="a", value=release["media"]["format"]),
                    Subfield(code="b", value="digital, stereo"),
                    Subfield(code="c", value="120 mm"),
                ],
            )
        )

        # Add track info field (tag 505)
        track_info = " \n".join(
            [
                f"{track['position']}. {track['title']}"
                for track in tracklist_data_mb["media"]["tracks"]
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

        # Discogs API lookup for additional contributor roles
        discogs_search_url = f"{base_url_discogs}database/search?q={barcode}&token={discogs_token}&type=release"
        try:
            response_discogs = session.get(discogs_search_url, headers=headers)
            response_discogs.raise_for_status()
            data_discogs = response_discogs.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Network error: {e} for barcode {barcode} on Discogs")
            continue
        except json.JSONDecodeError:
            logging.error(f"Failed to parse JSON response for barcode {barcode} on Discogs")
            continue

        if "results" in data_discogs and data_discogs["results"]:
            discogs_release = data_discogs["results"]
            discogs_release_url = f"{base_url_discogs}releases/{discogs_release['id']}?token={discogs_token}"
            try:
                release_response_discogs = session.get(discogs_release_url, headers=headers)
                release_response_discogs.raise_for_status()
                release_data_discogs = release_response_discogs.json()
            except requests.exceptions.RequestException as e:
                logging.error(f"Network error: {e} for release ID {discogs_release['id']} on Discogs")
                continue
            except json.JSONDecodeError:
                logging.error(f"Failed to parse JSON response for release ID {discogs_release['id']} on Discogs")
                continue

            # Add producer and studio engineer roles (tag 700)
            if "extraartists" in release_data_discogs:
                for artist in release_data_discogs["extraartists"]:
                    if artist["role"].lower() in ["producer", "engineer"]:
                        marc_record.add_field(
                            Field(
                                tag="700",
                                indicators=["1", " "],
                                subfields=[
                                    Subfield(code="a", value=artist["name"]),
                                    Subfield(code="e", value=artist["role"]),
                                ],
                            )
                        )

        # Append the MARC record to the list
        marc_records.append(marc_record)

        # Add the row to the CSV list
        csv_rows.append(
            [release["title"], artist_name, release["date"], track_info, release["id"]]
        )
    else:
        logging.warning(f"No releases found for barcode {barcode}")

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
        writer.write
