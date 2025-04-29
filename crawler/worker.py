from threading import Thread

from inspect import getsource
from utils.download import download
from utils import get_logger
import scraper
import time
import re
from bs4 import BeautifulSoup

from collections import defaultdict


class Worker(Thread):
    def __init__(self, worker_id, config, frontier, stopwords: set, wordcounts: defaultdict, longestpage: dict, subdomains: list):
        self.logger = get_logger(f"Worker-{worker_id}", "Worker")
        self.config = config
        self.frontier = frontier
        self.stop_words = stopwords
        self.word_counts = wordcounts
        self.longest_page = longestpage
        self.subdomains = subdomains
        # basic check for requests in scraper
        assert {getsource(scraper).find(req) for req in {"from requests import", "import requests"}} == {-1}, "Do not use requests in scraper.py"
        assert {getsource(scraper).find(req) for req in {"from urllib.request import", "import urllib.request"}} == {-1}, "Do not use urllib.request in scraper.py"
        super().__init__(daemon=True)


    def extract_words(self, resp):
        content = resp.raw_response.content
        soup = BeautifulSoup(content, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()
        
        # Get text from HTML
        text = soup.get_text()
        
        # Clean the text: lowercase, remove special chars, split into words
        words = re.findall(r'\b\w+\b', text.lower())

        # check longest page
        if self.longest_page["count"] < len(words):
            self.longest_page["page"] = resp.url
            self.longest_page["count"] = len(words)



        print(words)

        words = [word for word in words if word not in self.stop_words]
        for word in words:
            if word not in self.word_counts:
                self.word_counts[word] += 1
            else:
                self.word_counts[word] += 1
        
    def run(self):
        while True:
            tbd_url = self.frontier.get_tbd_url()
            if not tbd_url:
                self.logger.info("Frontier is empty. Stopping Crawler.")
                break
            resp = download(tbd_url, self.config, self.logger)
            # run statistics on current url
            self.extract_words(resp)
            self.logger.info(
                f"Downloaded {tbd_url}, status <{resp.status}>, "
                f"using cache {self.config.cache_server}.")
            # then fetch all new urls to be added to the frontier
            scraped_urls = scraper.scraper(tbd_url, resp)
            for scraped_url in scraped_urls:

                self.frontier.add_url(scraped_url)
            self.frontier.mark_url_complete(tbd_url)
            time.sleep(self.config.time_delay)
