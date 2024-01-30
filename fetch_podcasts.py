import requests
import hashlib
import time
import json
import argparse
from datetime import datetime
import pandas as pd
import logging
import os

LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
logging.basicConfig(filename=f'{os.path.basename(__file__)}.log', level=logging.INFO, format=LOG_FORMAT, datefmt='%Y-%m-%d %H:%M:%S', filemode='w')

def generate_auth_headers(api_key, api_secret):
    current_time = str(int(time.time()))
    auth_header = hashlib.sha1((api_key + api_secret + current_time).encode()).hexdigest()

    return {
        "User-Agent": "YourApp/1.0",  # Replace with your app's user agent
        "X-Auth-Key": api_key,
        "X-Auth-Date": current_time,
        "Authorization": auth_header
    }

def date_to_epoch(date_str):
    return int(datetime.strptime(date_str, "%Y-%m-%d").timestamp())

def fetch_podcasts(since, max_results, api_key, api_secret):
    url = "https://api.podcastindex.org/api/1.0/podcasts/trending"
    headers = generate_auth_headers(api_key, api_secret)
    params = {"since": since, "max": max_results, "lang":"en"}
    response = requests.get(url, headers=headers, params=params)
    print(response.text)
    return response.json()['feeds'] if response.status_code == 200 else []

def get_podcast_data(start_date, end_date, desired_n, api_key, api_secret, debug):
    print(start_date, end_date)
    start_epoch = date_to_epoch(start_date)
    end_epoch = date_to_epoch(end_date)

    if debug:  # Limit to one day of data for debugging
        end_epoch = start_epoch + 86400

    num_days = (datetime.fromtimestamp(end_epoch) - datetime.fromtimestamp(start_epoch)).days + 1
    avg_podcasts_per_day = max(desired_n // num_days, 1)

    podcasts = []
    current_epoch = start_epoch
    while current_epoch < end_epoch and len(podcasts) < desired_n:
        max_results = min(avg_podcasts_per_day, desired_n - len(podcasts))
        fetched_podcasts = fetch_podcasts(current_epoch, max_results, api_key, api_secret)
        podcasts.extend(fetched_podcasts)
        current_epoch += 86400

    return podcasts[:desired_n]

def main():
    parser = argparse.ArgumentParser(description="Fetch podcasts from the Podcast Index API.")
    parser.add_argument("--start_date", help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end_date", help="End date in YYYY-MM-DD format")
    parser.add_argument("--N", type=int, help="Number of podcasts to fetch")
    parser.add_argument("--debug", action="store_true", help="Debug mode (fetch only 1 day of data)")
    parser.add_argument("--pilot", action="store_true", help="Pilot mode")

    args = parser.parse_args()
    logging.info("Running with args ", str(args))


    with open('secrets.json', 'r') as file:
        secrets = json.load(file)
    api_key = secrets['podcast_api']
    api_secret = secrets['podcast_secret']

    podcasts = get_podcast_data(args.start_date, args.end_date, args.N, api_key, api_secret, args.debug)
    logging.info(f"Got podcasts, N= {len(podcasts)}")

    if args.debug:
        filename = "podcasts_debug.jsonl"
    else:
        filename = f"{'pilot_' if args.pilot else ''}_{args.start_date}_to_{args.end_date}_podcasts.jsonl"

    podcasts_df = pd.DataFrame(podcasts)
    podcasts_df['dataset_id'] = [f"podcast_{i}" for i in range(len(podcasts_df))]
    podcasts_df.to_json(filename, orient='records', lines=True)
    logging.info("Wrote to json")



if __name__ == "__main__":
    main()
