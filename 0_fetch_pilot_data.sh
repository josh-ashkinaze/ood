#!/bin/bash

# This script fetches a small amount of ideas for testing purposes
# and prompt engineering.

my_start_date='2023-01-01'
my_end_date='2023-02-01'

python3 fetch_fiction.py --start_date "$my_start_date" --end_date "$my_end_date" --pilot
python3 fetch_startups.py --start_date "$my_start_date" --end_date "$my_end_date" --pilot
python3 fetch_osf_preprints.py --provider 'socarxiv' --start_date "$my_start_date" --end_date "$my_end_date" --max_results_per_month 500 --pilot
python3 fetch_osf_preprints.py --provider 'psyarxiv' --start_date "$my_start_date" --end_date "$my_end_date" --max_results_per_month 500 --pilot
python3 fetch_nyt_opeds.py --start_date "$my_start_date" --end_date "$my_end_date" --pilot

echo "All done!"