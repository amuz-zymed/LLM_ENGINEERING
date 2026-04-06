import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

# Headers to make requests look like a browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Referer': 'https://www.google.com/',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

def fetch_website_links(url):
    """
    Fetch all links from a website.
    Returns a list of relative and absolute links.
    """
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        links = []
        for a_tag in soup.find_all('a', href=True):
            link = a_tag['href']
            # Convert relative links to absolute
            full_link = urljoin(url, link)
            links.append(full_link)
        return links
    except Exception as e:
        print(f"Error fetching links from {url}: {e}")
        return []

def fetch_website_contents(url, retry_count=3):
    """
    Fetch the main content of a webpage with retry logic.
    Returns the text content.
    """
    for attempt in range(retry_count):
        try:
            response = requests.get(url, headers=HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.extract()
            
            # Get text
            text = soup.get_text()
            
            # Clean up whitespace
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)
            
            return text[:5000]  # Limit to 5000 characters
            
        except requests.exceptions.HTTPError as e:
            if response.status_code == 429:  # Too many requests
                wait_time = (2 ** attempt)  # Exponential backoff
                print(f"Rate limited. Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            elif response.status_code in [403, 503]:  # Forbidden or unavailable
                if attempt < retry_count - 1:
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                else:
                    return f"[Content blocked by {urlparse(url).netloc}]"
            else:
                return ""
        except requests.exceptions.Timeout:
            if attempt < retry_count - 1:
                time.sleep(2 ** attempt)
            else:
                return "[Request timeout]"
        except Exception as e:
            if attempt < retry_count - 1:
                time.sleep(1)
            else:
                return ""
    
    return ""