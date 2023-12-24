"""
Author: Joshua Ashkinaze
Date: 2023-12-04

Description: Scrapes fiction book descriptions from FictionDB

Note: We scrape the first (max) pages for each month, sorting books in ascending order of date.
"""

import argparse
import requests
from bs4 import BeautifulSoup
import multiprocessing
import pandas as pd
import time
import random
import ftfy
import logging
import os


def generate_urls(start_date, end_date, max_pages=10):
    """Generate URLs for each month. Also scrape up to max_pages pages for each month so add page no to URL"""
    start_year, start_month, _ = map(int, start_date.split('-'))
    end_year, end_month, _ = map(int, end_date.split('-'))
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    urls = []
    for year in range(start_year, end_year + 1):
        start_m = start_month if year == start_year else 1
        end_m = end_month if year == end_year else 12
        for m in range(start_m, end_m + 1):
            month = months[m - 1]
            for pg in range(1, max_pages):
              url = f"https://www.fictiondb.com/new-releases/new-books-by-month.htm?date={month}-{year}&sort=da&s={pg}"
              urls.append(url)
    return urls

def get_book_description(link):
    """Return a book description given a link """
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(link, headers=headers)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            description_tag = soup.find('div', {'class': 'tab-pane fade show active', 'id': 'description'})
            if description_tag:
                description = description_tag.get_text(strip=True)
                return ftfy.fix_encoding(description)  # Fixing encoding issues
        return None
    except Exception as e:
        logging.info(f"Error fetching book description: {e}")
        return None

def scrape_books_for_month(url):
    logging.info(f"Scraping {url}")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            logging.info(f"Failed to fetch {url}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        book_rows = soup.find_all("tr", class_=["g", "p", "r"])
        books = []
        for row in book_rows:
            book = {}
            book["author"] = row.find("a", itemprop="author").get_text(strip=True)
            book_details_tag = row.find("a", itemprop="url")
            book["title"] = book_details_tag.find("span", itemprop="name").get_text(strip=True)
            book["link"] = book_details_tag['href'].replace("..", "https://www.fictiondb.com")
            book["genre"] = row.find("span", itemprop="genre").get_text(strip=True)
            book['genre'] = book['genre'].replace(" /", "")
            book["date"] = row.find("span", itemprop="datePublished").get_text(strip=True)
            series_tag = row.find("td", class_="d-none d-xl-table-cell")
            book["series"] = series_tag.get_text(strip=True) if series_tag else None
            book["description"] = get_book_description(book['link'])
            books.append(book)

        if len(books) % 10 == 0:
            time.sleep(random.uniform(0.5, 1.5))
        if books:
            logging.info(f"Scraped {len(books)} books for {url}")
        return books

    except Exception as e:
        logging.info(f"Error scraping {url}: {e}")
        return []

def main():
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s'
    logging.basicConfig(filename=f'{os.path.basename(__file__)}.log', level=logging.INFO, format=LOG_FORMAT,
                        datefmt='%Y-%m-%d %H:%M:%S', filemode='w')

    parser = argparse.ArgumentParser(description='Scrape FictionDB for book descriptions.')
    parser.add_argument('--start_date', default="2018-01-01", type=str, help='Start date in YYYY-MM-DD format')
    parser.add_argument('--end_date', default="2023-01-01", type=str, help='End date in YYYY-MM-DD format')
    parser.add_argument('--max_pages', default=15, type=int, help='Max pages to scrape for each month')
    parser.add_argument('--d', action='store_true', help='Debug mode: scrape only one page')
    args = parser.parse_args()

    logging.info(f"Scraping FictionDB with parameters {str(args)}")
    urls = generate_urls(args.start_date, args.end_date, args.max_pages)

    if args.d:
        urls = urls[:1]

    try:
        with multiprocessing.Pool(processes=min(len(urls), multiprocessing.cpu_count())) as pool:
            results = pool.map(scrape_books_for_month, urls)
            all_books = [book for monthly_books in results if monthly_books for book in monthly_books]
            df = pd.DataFrame(all_books)
            logging.info(f"All done. Fetched {len(df)} items")
            df['dataset_id'] = [f"book_{i}" for i in range(len(df))]
            fn = f"{args.start_date}_{args.end_date}_fiction.jsonl" if not args.d else "fiction_debug.jsonl"
            df.to_json(fn, orient='records', lines=True)
    except Exception as e:
        logging.error(f"Error during scraping or DataFrame creation: {e}")

if __name__ == "__main__":
  main()
