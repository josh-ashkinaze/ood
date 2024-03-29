#!/bin/bash

my_start_date='2017-01-01'
my_end_date='2024-02-01'

python3 fetch_fiction.py --start_date "$my_start_date" --end_date "$my_end_date"
python3 fetch_startups.py --start_date "$my_start_date" --end_date "$my_end_date"
python3 fetch_osf_preprints.py --provider 'socarxiv' --start_date "$my_start_date" --end_date "$my_end_date" --max_results_per_month 3000
python3 fetch_osf_preprints.py --provider 'psyarxiv' --start_date "$my_start_date" --end_date "$my_end_date" --max_results_per_month 3000
python3 fetch_podcasts  --start_date "$my_start_date" --end_date "$my_end_date" --N 50000

echo "All done!"