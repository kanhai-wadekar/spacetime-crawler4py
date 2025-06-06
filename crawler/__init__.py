from utils import get_logger
from crawler.frontier import Frontier
from crawler.worker import Worker
from collections import defaultdict

class Crawler(object):
    def __init__(self, config, restart, frontier_factory=Frontier, worker_factory=Worker):
        self.stop_words = set()
        self.word_counts = defaultdict(int)
        self.longest_page = {'page': '', 'count': 0}
        self.subdomains = []
        with open('stopwords.txt', 'r') as f:
                    for word in f:
                        self.stop_words.add(word.strip())

        self.config = config
        self.logger = get_logger("CRAWLER")
        self.frontier = frontier_factory(config, restart)
        self.workers = list()
        self.worker_factory = worker_factory
        

    def start_async(self):
        self.workers = [
            self.worker_factory(worker_id, self.config, self.frontier, self.stop_words, self.word_counts, self.longest_page, self.subdomains)
            for worker_id in range(self.config.threads_count)]
        for worker in self.workers:
            worker.start()

    def start(self):
        self.start_async()
        self.join()

    def join(self):
        for worker in self.workers:
            worker.join()
