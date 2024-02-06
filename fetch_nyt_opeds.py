"""
Author: Joshua Ashkinaze
Date: 2024-01-16

Description: Fetches op-eds from the New York Times API
"""
import requests
import json
import argparse
import logging
from datetime import datetime
import os
from time import sleep
import random

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(filename=f'{os.path.basename(__file__)}.log', level=logging.INFO, format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S', filemode='w')

def parse_article(d):
    data = {
        'headline': d['headline']['main'],
        'abstract': d['abstract'],
        'web_url': d['web_url'],
        'lead_paragraph': d['lead_paragraph'],
        'snippet': d['snippet'],
        'date': d['pub_date'],
        'kw': parse_keywords(d['keywords']),
        'uri': d['uri'],
        'author': parse_byline(d['byline']),
        'document_type': d['document_type']
    }
    return data

def parse_keywords(keyword_list):
    reformatted_keywords = {}
    for keyword in keyword_list:
        keyword_type = keyword['name']
        if keyword_type not in reformatted_keywords:
            reformatted_keywords[keyword_type] = []
        reformatted_keywords[keyword_type].append(keyword['value'])
    return reformatted_keywords

def parse_byline(byline_data):
    parsed_byline = {'Original': byline_data.get('original', '')}
    people = [f"{person.get('lastname', '')} {person.get('firstname', '')}".strip()
              for person in byline_data.get('person', [])]
    parsed_byline['People'] = ', '.join(people)
    parsed_byline['Organizations'] = byline_data.get('organization', '')
    return parsed_byline

def get_nyt_headlines(api_key, start_date, end_date):
    results = []
    current_date = start_date

    while current_date <= end_date:
        sleep_for = random.uniform(1, 3)
        logging.info(f"Sleeping for {sleep_for} seconds for date {current_date}")
        logging.info("There are currently {} results".format(len(results)))
        sleep(sleep_for)
        year = current_date.year
        month = current_date.month
        url = f'https://api.nytimes.com/svc/archive/v1/{year}/{month}.json?api-key={api_key}'
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            for doc in data['response']['docs']:
                if doc['type_of_material'] == 'Op-Ed':
                    results.append(parse_article(doc))
        else:
            logging.error("Failed to retrieve data from the API")
        if month == 12:
            current_date = datetime(year + 1, 1, 1)
        else:
            current_date = datetime(year, month + 1, 1)
    return results

def read_api_key(filepath):
    with open(filepath, 'r') as file:
        secrets = json.load(file)
    return secrets.get('nyt_api', '')

def main():
    parser = argparse.ArgumentParser(description='fetch some metadata about NYT op-eds (does not include full op-ed)')
    parser.add_argument('--start_date', type=str, required=True, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', type=str, required=True, help='End date in YYYY-MM-DD format')
    parser.add_argument('--d', action='store_true', help='Debug mode')
    parser.add_argument('--pilot', action='store_true', help='Pilot run')
    args = parser.parse_args()
    logging.info("Args: " + str(args))
    api_key = read_api_key('secrets.json')
    if not api_key:
        logging.error('API key not found in secrets.json')
        return

    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')

    if args.d:
        logging.info('Running in debug mode')

    headlines = get_nyt_headlines(api_key, start_date, end_date)

    if args.pilot:
        filename = f"pilot_{args.start_date}_to_{args.end_date}_nyt_headlines.jsonl"
    else:
        filename = f"{args.start_date}_to_{args.end_date}_nyt_headlines.jsonl"

    with open(filename, 'w') as file:
        for headline in headlines:
            file.write(json.dumps(headline) + '\n')

    logging.info(f"NYT headlines (n={len(headlines)}) from {args.start_date} to {args.end_date} saved to {filename}")

if __name__ == "__main__":
    main()