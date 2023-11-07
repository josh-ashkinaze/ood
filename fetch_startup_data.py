"""
Author: Joshua Ashkinaze
Date: 2023-11-07

Description: Fetches ProductHunt data from the `time travel` page from `start_date` to `end_date`. Returns a dataframe like
[date, name, tagline]

usage: fetch_startup_data.py [-h] [--debug] [start_date] [end_date]

Fetch product data from Product Hunt.

positional arguments:
  start_date  Start date in YYYY-MM-DD format (default is 2019-01-01)
  end_date    End date in YYYY-MM-DD format (default is 2023-11-01)

optional arguments:
  -h, --help  show this help message and exit
  --debug     Run in debug mode (one day only)
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
from joblib import Parallel, delayed


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
            }
            products.append(product_info)
        else:
            for key, value in json_data.items():
                products.extend(find_products(value))
    elif isinstance(json_data, list):
        for item in json_data:
            products.extend(find_products(item))
    return products

def fetch_product_hunt_data_for_date(year, month, day):
    """
    Fetches product data from Product Hunt for a given date.

    Parameters:
    year (int): The year to fetch data for.
    month (int): The month to fetch data for.
    day (int): The day to fetch data for.

    Returns:
    list: A list of products with their information and the date as a field.
    """
    # Construct the URL
    logging.info(f"Trying to scrape data for {year}-{month}-{day}")
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
            logging.info(f"Fetched {len(products)}")
        except Exception as e:
            logging.info(f"Error for {year}-{month}-{day}: {e}")
            return []
    else:
        logging.info(f"Found nothing for {year}-{month}-{day}")
        return []

    # Add the date as a field to each product
    date_string = f"{year}-{month}-{day}"
    for product in products:
        product['date'] = date_string

    return products

def fetch_products_for_date_range(start_date, end_date):
    """
    Fetches product data from Product Hunt for a given date range.

    Parameters:
    start_date (str): The start date in 'YYYY-MM-DD' format.
    end_date (str): The end date in 'YYYY-MM-DD' format.

    Returns:
    list: A list of dictionaries of products
    """

    start_date_obj = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    date_range = [start_date_obj + timedelta(days=x) for x in range((end_date_obj - start_date_obj).days + 1)]

    # Use all available CPUs minus one
    num_cores = min(os.cpu_count() - 1, 5)

    # Execute the fetch_product_hunt_data_for_date function in parallel
    products_by_date = Parallel(n_jobs=num_cores)(
        delayed(fetch_product_hunt_data_for_date)(date.year, date.month, date.day) for date in date_range
    )

    # Flatten the list of lists into a single list
    products_flat_list = [product for sublist in products_by_date for product in sublist if sublist]
    return products_flat_list

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Fetch product data from Product Hunt.")
    parser.add_argument('start_date', type=str, nargs='?', default='2019-01-01',
                        help='Start date in YYYY-MM-DD format (default is 2019-01-01)')
    parser.add_argument('end_date', type=str, nargs='?', default='2023-11-01',
                        help='End date in YYYY-MM-DD format (default is 2023-11-01)')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode (one day only)')
    args = parser.parse_args()

    # If in debug mode, override dates
    if args.debug:
        logging.info("Running in debug mode")
        args.start_date = "2018-01-01"
        args.end_date = "2018-01-02"

    logging.info(f"Start date: {args.start_date}")
    logging.info(f"End date: {args.end_date}")

    # Fetch product data
    products_range = pd.DataFrame(fetch_products_for_date_range(args.start_date, args.end_date))
    logging.info(f"Fetched {len(products_range)} products")
    products_range.to_csv(f"{args.start_date}_{args.end_date}_producthunt.csv")

if __name__ == "__main__":
    main()
