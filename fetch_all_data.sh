#!/bin/bash

my_start_date='2018-01-01'
my_end_date='2023-01-01'

python3 fetch_fiction.py --start_date "$my_start_date" --end_date "$my_end_date"
python3 fetch_startups.py --start_date "$my_start_date" --end_date "$my_end_date"
python3 fetch_osf_prerints.py --provider 'socarxiv' --start_date "$my_start_date" --end_date "$my_end_date" --max_results_per_month 1000
python3 fetch_osf_prerints.py --provider 'psyarxiv' --start_date "$my_start_date" --end_date "$my_end_date" --max_results_per_month 1000
