""""
Crawler for the search engine

Group 37

Authors:
- Farhan Syed
- Zi Yue Anna Yang
- David Tanudin 

"""
from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin
from collections import deque

def crawl(start_url, indexer, stopwords, max_pages):
    queue = deque([start_url])
    visited_urls = set()
    pages_indexed = 0

    # BFS for crawling
    while queue and pages_indexed < max_pages:
        current_url = queue.popleft()

        if current_url in visited_urls:
            continue

        print(f"Crawling: {current_url}")
        visited_urls.add(current_url)
        try:
            page = requests.get(current_url)
            soup = BeautifulSoup(page.content, 'html.parser')

            title = soup.title.string if soup.title else "No Title"
            content = soup.get_text()

            last_modified = page.headers.get('Last-Modified', 'Unknown')
            size = len(page.text)
            
            indexer.index_page(current_url, title, content, last_modified, size)
            indexer.index_keywords(current_url, content, stopwords, title)
            pages_indexed += 1 

            if pages_indexed >= max_pages:
                break

            for link in soup.find_all('a'):
                href = link.get('href')
                if href:
                    full_url = urljoin(current_url, href)

                    if full_url not in visited_urls:
                        queue.append(full_url)
                        indexer.index_link(current_url, full_url)

        except requests.exceptions.RequestException as e:
            print(f"Failed to crawl {current_url}: {e}")

    print(f"\nDone! Indexed {pages_indexed} pages")
