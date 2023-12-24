"""
Author: Joshua Ashkinaze
Date: November 2023

Description: Fetches ProductHunt data from the `time travel` page
"""

import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
import argparse
import logging
from tenacity import retry, wait_fixed, stop_after_attempt
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(filename=f'{os.path.basename(__file__)}.log', level=logging.INFO, format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S', filemode='w')

# Retry configuration with tenacity
@retry(wait=wait_fixed(300), stop=stop_after_attempt(3))
def fetch_html(url):
    """
    Fetches the HTML content of a given URL with retries.

    Parameters:
        url (str): The URL to fetch the HTML content from.

    Returns:
        str: The HTML content of the page, or None if an error occurs.
    """
    response = requests.get(url)
    response.raise_for_status()
    return response.text

def find_products(json_data):
    """
    Recursively searches JSON data to find entries that resemble product information.

    Parameters:
        json_data (dict): The JSON data extracted from the __NEXT_DATA__ script tag.

    Returns:
        list: A list of dictionaries with product information.
    """
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
    """
    Fetches product data from Product Hunt for a single date.

    Parameters:
        current_date (datetime): The date for which to fetch the data.

    Returns:
        list: A list of product information for the given date.
    """
    year = current_date.year
    month = current_date.month
    day = current_date.day
    logging.info(f"Fetching data for {year}-{month}-{day}")

    # Construct the URL
    url = f"https://www.producthunt.com/time-travel/{year}/{month}/{day}"

    # Fetch the HTML content
    html_content = fetch_html(url)
    if not html_content:
        return []

    # Parse the HTML content
    soup = BeautifulSoup(html_content, 'html.parser')
    next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})

    if next_data_script and next_data_script.string:
        try:
            next_data = json.loads(next_data_script.string)
            products = find_products(next_data)
            # Add the date as a field to each product
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
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Fetch product data from Product Hunt.")
    parser.add_argument('--start_date', type=str, nargs='?', default='2017-01-01',
                        help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', type=str, nargs='?', default='2023-12-01',
                        help='End date in YYYY-MM-DD format')
    parser.add_argument('--d', action='store_true', help='Run in debug mode (one day only)')
    parser.add_argument('--pilot', action='store_true', help='Whether to denote this run a pilot run')

    args = parser.parse_args()

    # If in debug mode, override dates
    if args.d:
        logging.info("Running in debug mode")
        args.start_date = "2018-01-01"
        args.end_date = "2018-01-02"

    start_date_obj = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(args.end_date, "%Y-%m-%d")
    date_range = [start_date_obj + timedelta(days=x) for x in range((end_date_obj - start_date_obj).days + 1)]

    # Use ThreadPoolExecutor for parallel execution
    with ThreadPoolExecutor(max_workers=os.cpu_count()-1) as executor:
        # Submit all tasks to the executor
        future_to_date = {executor.submit(fetch_product_hunt_data_for_date, date): date for date in date_range}

        # Collect the results as they complete
        flat_products_list = []
        for future in as_completed(future_to_date):
            flat_products_list.extend(future.result())

    products_range = pd.DataFrame(flat_products_list)
    products_range.columns = ['name', 'description', 'date']
    products_range = products_range.drop_duplicates(subset=['name', 'description'])
    products_range['dataset_id'] = [f"startup_{i}" for i in range(len(products_range))]
    fn = f"{'pilot_' if args.pilot else ''}{args.start_date}_{args.end_date}_startups.jsonl" if not args.d else "startups_debug.jsonl"
    logging.info(f"All done. Fetched {len(products_range)} items")
    products_range.to_json(fn, orient='records', lines=True)

if __name__ == "__main__":
    main()
