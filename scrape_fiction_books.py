"""
Author: Joshua Ashkinaze
Date: 2023-12-04

Description: Scrapes fiction book descriptions from FictionDB

ToDo
- didnt run this for everything
- add argparse stuff
- add option to get custom dates 
"""


import requests
from bs4 import BeautifulSoup
import pandas as pd
from joblib import Parallel, delayed
from datetime import datetime
import time
import random
import ftfy

# Function to generate URLs for each month from 2019 to 2023
def generate_urls():
    start_year = 2019
    end_year = 2023
    months = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
    urls = []
    for year in range(start_year, end_year + 1):
        for month in months:
            url = f"https://www.fictiondb.com/new-releases/new-books-by-month.htm?date={month}-{year}"
            urls.append(url)
    return urls

# Function to get book description from its link
def get_book_description(link):
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
        print(f"Error fetching book description: {e}")
        return None

# Function to scrape books for a specific month
def scrape_books_for_month(url):
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {url}")
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        book_rows = soup.find_all("tr", class_=["g", "p", "r"])
        books = []

        for row in book_rows:
            book = {}
            book["author"] = row.find("a", itemprop="author").get_text(strip=True)
            book_details_tag = row.find("a", itemprop="url")
            book["title"] = book_details_tag.find("span", itemprop="name").get_text(strip=True)
            book["link"] = book_details_tag['href'].replace("..", "https://www.fictiondb.com/")
            book["genre"] = row.find("span", itemprop="genre").get_text(strip=True)
            book["date"] = row.find("span", itemprop="datePublished").get_text(strip=True)
            series_tag = row.find("td", class_="d-none d-xl-table-cell")
            book["series"] = series_tag.get_text(strip=True) if series_tag else None
            book["description"] = get_book_description(book['link'])

            books.append(book)
            time.sleep(random.uniform(1, 3))  # Random sleep between requests

        return books

    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return []

def main():
  urls = generate_urls()
  results = Parallel(n_jobs=-1)(delayed(scrape_books_for_month)(url) for url in urls)
  all_books = [book for monthly_books in results for book in monthly_books]
  df = pd.DataFrame(all_books)
  df.to_csv("fiction_books.csv", index=False)

if __name__ == "__main__":
  main()
