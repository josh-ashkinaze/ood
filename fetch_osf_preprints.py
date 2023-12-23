"""
Author: Joshua Ashkinaze
Date: 2023-12-23

Description: Scrapes preprint data from OSF pre-print servers. Providers include:
- socarxiv
- psyarxiv

Note: To inspect pre-print objects look at this sample
https://api.osf.io/v2/preprints/4ztrp/

"""
import os
import requests
import pandas as pd
from datetime import datetime, timedelta
import argparse
import logging
import random
from time import sleep


def parse_osf_preprint(info):
    data = {
        'osf_id': info['id'],
        'title': info['attributes']['title'],
        'description': info['attributes']['description'],
        'tags': list(set(info['attributes']['tags'])),
        'date': info['attributes']['date_created'],
        'doi': info['attributes']['doi'],
        'subjects':extract_text_tags(info),
        'is_published': info['attributes']['is_published'],
    }
    for k in info['links'].keys():
        data[f'{k}_url'] = info['links'][k]
    return data

def extract_text_tags(info):
    tags = set()
    for subject_group in info['attributes']['subjects']:
        for subject in subject_group:
            tags.add(subject['text'])
    return list(tags)

def get_preprints(provider, start_date, end_date, max_results_per_month=50):
    base_url = f"https://api.osf.io/v2/preprint_providers/{provider}/preprints/"
    results = []

    # Iterate over each month in the range
    current_month_start = start_date
    while current_month_start < end_date:
        current_month_end = min(last_day_of_month(current_month_start), end_date)
        page = 1
        monthly_results = 0

        logging.info(f"Processing preprints for month: {current_month_start.strftime('%Y-%m')}")

        while monthly_results < max_results_per_month:
            params = {
                'filter[date_created][gte]': current_month_start.isoformat(),
                'filter[date_created][lte]': current_month_end.isoformat(),
                'sort': 'date_created',
                'page': page
            }

            response = requests.get(base_url, params=params)
            if response.status_code != 200:
                return response.status_code, response.json()

            data = response.json()['data']
            for preprint in data:
                if preprint['id'] not in [p['osf_id'] for p in results]:
                    try:
                        parsed_preprint = parse_osf_preprint(preprint)
                        results.append(parsed_preprint)
                        monthly_results += 1
                    except Exception as e:
                        logging.info(f"Error parsing preprint: {e}")
                        continue
                    if monthly_results >= max_results_per_month:
                        sleep(random.uniform(1, 3))
                        break

            next_page = response.json()['links']['next']
            if next_page is None or monthly_results >= max_results_per_month:
                break

            page += 1

        current_month_start = current_month_end + timedelta(days=1)

    results_df = pd.DataFrame(results)
    return results_df, results

def last_day_of_month(any_day):
    next_month = any_day.replace(day=28) + timedelta(days=4)  # this will never fail
    return next_month - timedelta(days=next_month.day)

def main():
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(filename=f'{os.path.basename(__file__)}.log', level=logging.INFO, format=LOG_FORMAT,
                        datefmt='%Y-%m-%d %H:%M:%S', filemode='w')

    parser = argparse.ArgumentParser(description='Scrapes preprint data from OSF pre-print servers.')


    parser.add_argument('--start_date', type=str,
                        help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', type=str,
                        help='End date in YYYY-MM-DD format')
    parser.add_argument('--provider', type=str, choices=['socarxiv', 'psyarxiv', 'medarxiv'], help='Preprint provider')
    parser.add_argument('--max_results_per_month', type=int, default=100, help='Maximum number of results to fetch')
    parser.add_argument('--d', action='store_true',
                        help='Use debug settings (socarxiv, 2021-01-01 to 2021-01-02, max_results=2)')

    args = parser.parse_args()
    logging.info(f"Scraping preprtings with parameters {str(args)}")

    # Handle debug settings
    if args.d:
        provider = "socarxiv"
        start_date = "2021-01-01"
        end_date =  "2022-01-01"
        max_results_per_month = 1
    else:
        provider = args.provider
        max_results_per_month = args.max_results_per_month
        start_date = args.start_date
        end_date = args.end_date

    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
    except ValueError:
        raise ValueError("Incorrect data format, should be YYYY-MM-DD")

    df, r = get_preprints(provider, start_date, end_date, max_results_per_month)
    df['dataset_id'] = [f"{provider}_{i}" for i in range(len(df))]
    fn = f"{args.start_date}_{args.end_date}_{provider}.csv" if not args.d else "debug.csv"
    df.to_csv(fn, index=False)

if __name__ == "__main__":
    main()