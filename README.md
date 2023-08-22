# MarcBrainz
A reasonably easy way to create marc records for Music CDs

This is a python script which scans a text file containing barcodes and fetches details of the appropiate CDs using the MusicBrainz API. It returns results in both spreadsheet (csv) and marc record (mrc) formats.

## How to use

It requires installing python(3), and pip installing json, csv, datetime, requests and pymarc. [Version information to be added]

When you run the script it will assume the presence of a barcodes.txt file in the same directory.

You'll need to register a [user-agent](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting#Provide_meaningful_User-Agent_strings) with MusicBrainz to avoid [rate-limiting](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting). 



## Why the name?

[Back in 2010](https://www.libraryjournal.com/story/marc-must-die) Roy Tennant told us that "Marc must die" but still it lingers. Music CDs have seemingly been in terminal decline for years but are still used and purchased. These zombie technologies remain with us, and what do zombies love? ... Brainz! 

## Reading and references

- [Music CD Template](https://iflsweb.org/knowledge-base/music-cd-template/)
- [Best Practices for Music Cataloging](https://www.rdatoolkit.org/sites/default/files/rda_best_practices_for_music_cataloging-v1_0_1-140401.pdf)
