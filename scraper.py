from collections import defaultdict
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import re
import os

# ---------------------------------------------
# ----------------- GLOBALS -------------------
# ---------------------------------------------

WORD_COUNTS = defaultdict(int)
LONGEST_PAGE = {"page":  "", "count": 0}
SUBDOMAINS = defaultdict(int)
UNIQUE_PAGES = 0

STOPWORDS = {
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
}

ALLOWED_DOMAINS = {".ics.uci.edu", ".cs.uci.edu", ".informatics.uci.edu", ".stat.uci.edu", "today.uci.edu"}
ROBOTS_BLOCKED = {urlparse('https://cs.ics.uci.edu/people'), urlparse('http://kdd.ics.uci.edu'), urlparse('https://www.ics.uci.edu/people/'), urlparse('http://www.ics.uci.edu/happening/news'), urlparse('http://www.ics.uci.edu/people'), urlparse('http://intranet.ics.uci.edu')}
SERVER_SIDE_ERROR = {urlparse('http://www.ics.uci.edu/research.htm'), urlparse('http://cloudberry.ics.uci.edu/apps/twittermap'), urlparse('http://cloudberry.ics.uci.edu/demos/twittermap'), urlparse("http://www.ics.uci.edu/mailing_lists.html"), urlparse("http://www.ics.uci.edu/4_07social_activities.html"), urlparse("http://www.ics.uci.edu/2_3tutorial proposals.html"), urlparse("http://www.ics.uci.edu/teachingics.html")}
BAD_SUBDOMAINS = { "fano", "dblp", "jujube", "sli.ics.uci.edu", "computableplant.ics.uci.edu", "grape.ics.uci.edu" }

# ---------------------------------------------
# ----------------- HELPERS -------------------
# ---------------------------------------------
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
    

def scraper(url, resp):
    visited = set()
    norm = normalize_url(url)
    if norm in visited:
        return []
    visited.add(norm)
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]



def extract_next_links(url, resp):
    global UNIQUE_PAGES
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
    
    with open('./Logs/2xx.txt', 'a') as log:
        print(f'URL: {resp.url} | STATUS: <{resp.status}> | ERROR: "{resp.error}"', file=log)

    try:

        # ---------------------------------------------
        # ------------- LINK EXTRACTION ---------------
        # ---------------------------------------------
        soup = BeautifulSoup(resp.raw_response.content, "html.parser")

        # Remove script and style elements
        for script_or_style in soup(['script', 'style']):
            script_or_style.decompose()

        # Format text into space-separated lines for easier splitting
        page_text = soup.get_text(separator=' ', strip=True)
        # remove non-alphanumeric characters
        page_text = re.sub(r'[^a-zA-Z0-9\s]', '', page_text)
        # normalize text with lowercase and split into words
        words = page_text.lower().split()
        filtered_words = [word for word in words if word not in STOPWORDS] # skip stopwords

        
        #Extract links
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            absolute_url = urljoin(url, href)
            links.append(normalize_url(absolute_url))


        # ---------------------------------------------
        # ----------- UPDATE STATISTICS ---------------
        # ---------------------------------------------

        UNIQUE_PAGES += 1

        # check longest page
        if LONGEST_PAGE["count"] < len(words):
            LONGEST_PAGE["page"] = resp.url
            LONGEST_PAGE["count"] = len(words)
            print(f"NEW LONGEST PAGE: {len(words)}, {resp.url}")
        
        # Update words dict
        for word in filtered_words:
            if (len(word) > 2):
                WORD_COUNTS[word] += 1

        # Update subdomains dict
        parsed_url = urlparse(resp.url)
        SUBDOMAINS[parsed_url.netloc] += 1

        # ---------------------------------------------
        # --------- LOGGING ON OUR SIDE ---------------
        # ---------------------------------------------

        with open("./Logs/commonwords.txt", "w") as f:
            # Unique Pages stat
            print(f'UNIQUE PAGES FOUND: {UNIQUE_PAGES}\n', file=f)
            # Longest Page stat
            print(f"LONGEST PAGE: {LONGEST_PAGE['count']}, {LONGEST_PAGE['page']}\n", file=f)
            # Top 50 Words stat
            sorted_dict_desc = dict(sorted(WORD_COUNTS.items(), key=lambda item: item[1], reverse=True))
            i = 0
            for key in sorted_dict_desc:
                print(f"{key}: {sorted_dict_desc[key]}", file=f)
                if i > 49:
                    break
                i += 1
            print('\n', file=f)
            # Subdomains stat
            sorted_subdomains = dict(sorted(SUBDOMAINS.items(), key=lambda item: item[0]))
            for key in sorted_subdomains:
                print(f"{key}, {sorted_subdomains[key]}", file=f)

        # ---------------------------------------------
        # --------------- END LOGGING  ----------------
        # ---------------------------------------------

    except Exception as e:
        print(f"Error parsing {url}: {e}")
    
    return links


def is_valid(url):
   # Decide whether to crawl this url or not.
   # If you decide to crawl it, return True; otherwise return False.
   # There are already some conditions that return False.
    
    try:
        parsed = urlparse(url)

        path = parsed.path.split("/")[1:]

        # print(path)
        if parsed.scheme not in set(["http", "https"]):
            return False

        if not any(domain in parsed.netloc for domain in ALLOWED_DOMAINS):
            return False

        if any(parsed.netloc == url.netloc and parsed.path == url.path for url in ROBOTS_BLOCKED):
            return False
        
        if any(parsed.netloc == url.netloc and parsed.path == url.path for url in SERVER_SIDE_ERROR):
            return False

        # In the case that the authority is *today.uci.edu.SOMETHING
        # this domain is not up for some reason  
        

        # if not parsed.netloc.endswith(".uci.edu") and "today.uci.edu" not in parsed.netloc:
        #     return False

        if any(subdomain in parsed.netloc for subdomain in BAD_SUBDOMAINS):
            return False

        # MAYBE BLOCK https://grape.ics.uci.edu/wiki/asterix/timeline?from=2018   ?
        if (path):
            if 'fr.ics.uci.edu' in parsed.netloc:
                return False
            
            if 'today.uci.edu' in parsed.netloc:
                if parsed.path.startswith('department/information_computer_sciences'):
                    return True
                return False

            if ("~" in path[-1] and len(path) == 1):
                return False
            
            if (any("uploads" in el  for el in path)):
                return False

            # Avoid going down dates in the ICS Calendar
            # if parsed.netloc == 'ics.uci.edu':
            if (path[0] == "events" and len(path) > 1):
                return False
                
            if  "sli.ics.uci.edu" in parsed.netloc:
                return False
                # if path[0] == "Classes" or path[0] == "Pubs" or path[0] == "video":
                #     return False
            

            if ("flamingo" in parsed.netloc):
                if ("apache" in path[-1]):
                    return False
                
                if ("releases" in path and ("docs" in path or "src" in path)):
                    return False
                
                if (is_float(path[-1])):
                    return False
                
            if ("fuzzy" in path[-1] or (len(path) > 1 and "fuzzy" in path[-2])):
                return False

            # Prevents Trap in Homeland security page
            if ("EMWS09" in path):
                return False


            # upon a preliminary scrape, all urls belonging to either result in 4xx and 6xx errors respectively
            if (path[0] == "~thornton" or "drupal" in path or "~elzarki" in path):
                return False
            
            # overly large size that takes up compute
            if ("pdf" in path):
                return False
            
            if ("cert.ics.uci.edu" in parsed.netloc):
                if ("Nanda" in path):
                    return False

            # upon a preliminary scrape, all urls belonging to path including this string raise 4xx series errors
            if ("seminarseries" in path):
                return False
            
            if (path[0] == "~eppstein" ):
                # Too many urls matching following patterns that have little to no valuable textual information
                # Unintentional trap 
                if ("pix" in path or "pubs" in path):
                    return False
                if ("163" in path):
                    return False
                # Low on information in the rare case that 200s
                if len(path) > 1 and path[1] == "ca":
                    return False
                if len(path) > 1 and path[1].startswith("hw"):
                    return False
            
            # Low [quality] content site family
            if path[0] == '~irus':
                return False
                
            if path[0] == "~smyth":
                if len(path) > 1 and path[1] == 'courses':
                    return False
                
            if path[0] == "~dechter" and len(path) > 1:
                if path[1].startswith('r'):
                    return False
                # Low [quality] content site family
                if path[1] == 'publications':
                    return False
                
            
            # upon a preliminary scrape, all urls belonging to path including this string raise 4xx series errors
            if ("prof-david-redmiles" in path):
                return False
            
            if ("doku.php" in path):
                return False


        

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1|m|ma|nb|pd"
            + r"|thmx|mso|arff|rtf|jar|csv|shtml|htm"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz|war|img|mpg|apk"
            + r"|c|py|ipynb|h|cp|pov|lif|ppsx|pps)$", parsed.path.lower())


    except TypeError:
        print ("TypeError for ", parsed)
        raise