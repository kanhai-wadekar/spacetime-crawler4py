from collections import defaultdict
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os
WORD_COUNTS = defaultdict(int)
LONGEST_PAGE = {"page":  "", "count": 0}

stopwords = set({
         "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't", 
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't", 
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during", 
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having", "he", 
    "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how", "how's", 
    "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", 
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", 
    "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she", "she'd", "she'll", 
    "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the", "their", "theirs", "them", 
    "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", 
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", "we'd", "we'll", "we're", 
    "we've", "were", "weren't", "what", "what's", "when", "when's", "where", "where's", "which", "while", "who", 
    "who's", "whom", "why", "why's", "with", "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", 
    "you've", "your", "yours", "yourself", "yourselves"
    })


# 1. cant go to any people 
# 2. cant go to calendar 


SITE_DATA = {}


def scraper(url, resp):
    visited = set()
    norm = normalize_url(url)
    if norm in visited:
        return []
    visited.add(norm)
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]


def get_stopwords(file="./stopwords.txt"):
    """
    Read the stop words file and return it as a set.
    """
    stopwords = set()


    if not os.path.exists(file):
        print("You need a file of stopwords named stopwords.txt - this path does not exists!")
        return stopwords


    with open(file, 'r', encoding='utf-8') as f:
        for line in f:
            word = line.strip() 
            if word: 
                stopwords.add(word.lower())
    return stopwords

def normalize_url(url):
    parsed = urlparse(url)
    normalized = parsed._replace(fragment="").geturl()
    if normalized.endswith('/'):
        normalized = normalized[:-1]
    return normalized

def is_float(string):
    try:
        float(string)
        return True
    except ValueError:
        return False

def filterLinks(links, query):
    newLinks = [link for link in links if query not in link]
    return newLinks

def extract_next_links(url, resp):
   # Implementation required.
   # url: the URL that was used to get the page
   # resp.url: the actual url of the page
   # resp.status: the status code returned by the server. 200 is OK, you got the page. Other numbers mean that there was some kind of problem.
   # resp.error: when status is not 200, you can check the error here, if needed.
   # resp.raw_response: this is where the page actually is. More specifically, the raw_response has two parts:
   #         resp.raw_response.url: the url, again
   #         resp.raw_response.content: the content of the page!
   # Return a list with the hyperlinks (as strings) scrapped from resp.raw_response.content
    
    
    links = []


    if resp.status != 200:
        if resp.status < 400:
            with open('./Logs/3xx.txt', 'a') as log:
                print(f'URL: {resp.url} | STATUS: <{resp.status}> | ERROR: "{resp.error}"', file=log)
        elif resp.status < 500:
            with open('./Logs/4xx.txt', 'a') as log:
                print(f'URL: {resp.url} | STATUS: <{resp.status}> | ERROR: "{resp.error}"', file=log)
        elif resp.status < 600:
            with open('./Logs/5xx.txt', 'a') as log:
                print(f'URL: {resp.url} | STATUS: <{resp.status}> | ERROR: "{resp.error}"', file=log)
        elif resp.status < 700:
            with open('./Logs/6xx.txt', 'a') as log:
                print(f'URL: {resp.url} | STATUS: <{resp.status}> | ERROR: "{resp.error}"', file=log)


        return links  # return empty list if page did not load correctly
  
    try:
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")


        page_text = soup.get_text(separator=' ', strip=True)
        page_text = re.sub(r'[^a-zA-Z0-9\s]', '', page_text)  # remove non-alphanumeric characters
        words = page_text.lower().split()
        filtered_words = [word for word in words if word not in stopwords]

        # check longest page
        if LONGEST_PAGE["count"] < len(words):
            LONGEST_PAGE["page"] = resp.url
            LONGEST_PAGE["count"] = len(words)
            print(f"NEW LONGEST PAGE: {len(words)}, {resp.url}")
        
        with open("./Logs/commonwords.txt", "w") as f:
            print(f"LONGEST PAGE: {LONGEST_PAGE['count']}, {LONGEST_PAGE['page']}", file=f)
        
        # Update words dict
        for word in filtered_words:
            if (len(word) > 2):
                if word not in WORD_COUNTS:
                    WORD_COUNTS[word] += 1
                else:
                    WORD_COUNTS[word] += 1
        
        with open("./Logs/commonwords.txt", "a") as f:
            sorted_dict_desc = dict(sorted(WORD_COUNTS.items(), key=lambda item: item[1], reverse=True))
            i = 0
            for key in sorted_dict_desc:
                print(f"{key}: {sorted_dict_desc[key]}", file=f)
                if i > 49:
                    break
                i += 1

        with open("text.txt", "a", encoding="utf-8") as f:  #"a" to append
            f.write(f"URL: {url}\n")
            f.write(' '.join(filtered_words) + "\n\n")  # join words back into a string


        #Extract links
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            absolute_url = urljoin(url, href)
            links.append(normalize_url(absolute_url))

        links = [link for link in links if "thornton" not in link]

    except Exception as e:
        print(f"Error parsing {url}: {e}")
    
    return links


def is_valid(url):
   # Decide whether to crawl this url or not.
   # If you decide to crawl it, return True; otherwise return False.
   # There are already some conditions that return False.

    allowed_domains = set([".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu", "today.uci.edu"])
    
    try:
        parsed = urlparse(url)

        path = parsed.path.split("/")[1:]

        # print(path)
        if parsed.scheme not in set(["http", "https"]):
            return False

        if not any(domain in parsed.netloc for domain in allowed_domains):
            return False

        if not parsed.netloc.endswith(".uci.edu") and "today.uci.edu" not in parsed.netloc:
            return False
        
        if "fano" in parsed.netloc:
            return False
        
        if "dblp" in parsed.netloc:
            return False

        if "jujube" in parsed.netloc:
            return False
        
        

        if (path):
            if ("flamingo" in parsed.netloc):
                if ("apache" in path[-1]):
                    return False
                
                if ("releases" in path and ("docs" in path or "src" in path)):
                    return False
                
                if (is_float(path[-1])):
                    return False
                
                if ("fuzzy" in path[-1] or "fuzzy" in path[-2]):
                    return False


            # print(parsed)
            if (path[0] == "~thornton" or "drupal" in path):
                return False
            
            if ("pdf" in path):
                return False

            if ("seminarseries" in path):
                return False
            
            if (path[0] == "~eppstein" ):
                if ("pix" in path or "pubs"):
                    return False
                if ("163" in path and "s15-" in path):
                    return False
            


        

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|war|img|mpg|apk"
            + r"|c|py|ipynb|h|cp|pov)$", parsed.path.lower())


    except TypeError:
        print ("TypeError for ", parsed)
        raise