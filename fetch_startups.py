"""
Author: Joshua Ashkinaze
Date: November 2023

Description: Fetches ProductHunt data from the `time travel` page
"""

import json
import requests
import random
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import argparse
import logging
import time
from tenacity import retry, wait_fixed, stop_after_attempt
import os

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(filename=f'{os.path.basename(__file__)}.log', level=logging.INFO, format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S', filemode='w')

@retry(wait=wait_fixed(300), stop=stop_after_attempt(3))
def fetch_html(url):
    response = requests.get(url)
    #print(url)
    #print(response.text)
    response.raise_for_status()
    return response.text

def find_products(json_data):
    products = []
    if isinstance(json_data, dict):
        if 'name' in json_data and 'tagline' in json_data:
            product_info = {
                'name': json_data['name'],
                'desc': json_data['tagline'],
                'date': json_data.get('date')  # This will be set later
            }
            products.append(product_info)
        else:
            for value in json_data.values():
                products.extend(find_products(value))
    elif isinstance(json_data, list):
        for item in json_data:
            products.extend(find_products(item))
    return products

def fetch_product_hunt_data_for_date(current_date):
    #print(current_date)
    year = current_date.year
    month = current_date.month
    day = current_date.day
    logging.info(f"Fetching data for {year}-{month}-{day}")

    url = f"https://www.producthunt.com/leaderboard/daily/{year}/{month}/{day}/all"
    html_content = fetch_html(url)
    #print(html_content)
    if not html_content:
        return []

    soup = BeautifulSoup(html_content, 'html.parser')
    #print(soup)
    next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
    if next_data_script and next_data_script.string:
        try:
            next_data = json.loads(next_data_script.string)
            products = find_products(next_data)
            date_string = f"{year}-{month:02d}-{day:02d}"
            for product in products:
                product['date'] = date_string
            return products
        except Exception as e:
            logging.info(f"Error for {year}-{month}-{day}: {e}")
            return []
    else:
        logging.info(f"Found nothing for {year}-{month}-{day}")
        return []

def main():
    parser = argparse.ArgumentParser(description="Fetch product data from Product Hunt.")
    parser.add_argument('--start_date', type=str, nargs='?', default='2023-01-01',
                        help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', type=str, nargs='?', default='2023-02-01',
                        help='End date in YYYY-MM-DD format')
    parser.add_argument('--d', action='store_true', help='Run in debug mode (one day only)')
    parser.add_argument('--pilot', action='store_true', help='Whether to denote this run a pilot run')

    args = parser.parse_args()

    if args.d:
        logging.info("Running in debug mode")
        args.start_date = "2018-01-01"
        args.end_date = "2018-01-02"

    start_date_obj = datetime.strptime(args.start_date, "%Y-%m-%d")
    # Adjust end_date_obj to include the entire month following the original end month
    end_date_obj = datetime.strptime(args.end_date, "%Y-%m-%d")
    end_date_obj = (end_date_obj + timedelta(days=45)).replace(day=1) - timedelta(days=1)  # Move to next month and find last day
    date_range = [start_date_obj + timedelta(days=x) for x in range((end_date_obj - start_date_obj).days + 1)]

    flat_products_list = []
    for current_date in date_range:
        date_results = fetch_product_hunt_data_for_date(current_date)
        flat_products_list.extend(date_results)
        sleep_time = random.uniform(0.5, 1.5)
        if len(flat_products_list) % 1000 == 0:
            sleep_time = random.uniform(5, 30)
            logging.info("Sleeping for 5-30 seconds long sleep {}".format(sleep_time))
        logging.info(f"Sleeping for post-date {sleep_time}")
        time.sleep(sleep_time)

    products_range = pd.DataFrame(flat_products_list)
    products_range.columns = ['name', 'description', 'date']
    products_range = products_range.drop_duplicates(subset=['name', 'description'])
    products_range['dataset_id'] = [f"startup_{i}" for i in range(len(products_range))]
    fn = f"{'pilot_' if args.pilot else ''}{args.start_date}_to_{args.end_date}_startups.jsonl" if not args.d else "startups_debug.jsonl"
    logging.info(f"All done. Fetched {len(products_range)} items")
    products_range.to_json(fn, orient='records', lines=True)

if __name__ == "__main__":
    main()
