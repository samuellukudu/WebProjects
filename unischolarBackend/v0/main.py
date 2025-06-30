import pandas as pd
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser
import time
from duckduckgo_search import DDGS # <-- Added required import

def search_and_save(query: str, filename: str = "search_results.csv"):
    """
    Performs a DuckDuckGo search for a given query,
    and saves the results (title, abstract, url) to a CSV file.
    """
    print(f"Performing search for: '{query}'...")
    results = []
    with DDGS() as ddgs:
        # Fetching a few more results to get a richer source list
        for r in ddgs.text(query, max_results=30):
            results.append({
                'title': r.get('title'),
                'abstract': r.get('body'),
                'url': r.get('href')
            })

    if not results:
        print("No results found for your query.")
        return

    df = pd.DataFrame(results)
    df.to_csv(filename, index=False, encoding='utf-8')
    print(f"Successfully saved {len(df)} initial search results to {filename}")


def extract_and_validate_companies(search_results_csv: str, output_csv: str = "verified_companies.csv"):
    """
    Reads a CSV of search results, scrapes the URLs respecting robots.txt and
    using rate limiting, finds hyperlinks, validates them, and saves the result.
    """
    try:
        df = pd.read_csv(search_results_csv)
    except FileNotFoundError:
        print(f"Error: The file {search_results_csv} was not found.")
        print("Please run Step 1 first to generate this file.")
        return

    # --- Best Practices Setup ---
    USER_AGENT = 'MyCompanyScraper/1.0'
    REQUEST_DELAY = 1  # Seconds to wait between requests
    robot_parsers = {} # Cache for robot.txt parsers to avoid re-fetching

    verified_results = []
    BLOCKLIST = {
        'home', 'about', 'contact', 'blog', 'faq', 'website', 'click here',
        'read more', 'learn more', 'privacy policy', 'terms of service'
    }

    url_list = df['url'].dropna().tolist()

    for source_url in url_list:
        parsed_uri = urlparse(source_url)
        domain = f"{parsed_uri.scheme}://{parsed_uri.netloc}"
        
        # --- 1. Respect robots.txt ---
        if domain not in robot_parsers:
            rp = RobotFileParser()
            rp.set_url(urljoin(domain, 'robots.txt'))
            try:
                rp.read()
                robot_parsers[domain] = rp
            except Exception as e:
                print(f"Could not read robots.txt for {domain}. Assuming allow. Reason: {e}")
                robot_parsers[domain] = None # Mark as failed to avoid retries
        
        rp = robot_parsers.get(domain)
        if rp and not rp.can_fetch(USER_AGENT, source_url):
            print(f"Disallowed by robots.txt: Skipping {source_url}")
            continue

        # --- 2. Rate Limiting ---
        print(f"Scraping: {source_url}")
        time.sleep(REQUEST_DELAY)

        try:
            response = requests.get(source_url, timeout=10, headers={'User-Agent': USER_AGENT})
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            base_domain = urlparse(source_url).netloc
        except requests.RequestException as e:
            print(f"Could not fetch {source_url}. Reason: {e}")
            continue

        for link in soup.find_all('a'):
            company_url = link.get('href')
            company_name = link.get_text(strip=True)

            if not company_url or not company_name or company_name.lower() in BLOCKLIST:
                continue
            
            if not (3 < len(company_name) < 100):
                continue
            
            company_url = urljoin(source_url, company_url)
            
            if not company_url.startswith(('http://', 'https://')):
                continue

            link_domain = urlparse(company_url).netloc
            if not link_domain or link_domain == base_domain:
                continue

            verified_results.append({
                'company_name': company_name,
                'url': company_url,
                'source': source_url
            })

    if not verified_results:
        print("Could not find any verified companies.")
        return
        
    verified_df = pd.DataFrame(verified_results)
    verified_df.drop_duplicates(subset=['company_name', 'url'], inplace=True)
    verified_df.to_csv(output_csv, index=False, encoding='utf-8')
    
    print(f"\n--- Saved {len(verified_df)} verified companies to {output_csv} ---")
    print(verified_df.head())


if __name__ == "__main__":
    # This script is a two-step process.
    # 1. Run the search to get an initial list of URLs.
    # 2. Scrape those URLs to find and validate company names.

    # --- Step 1: Perform search (run this first) ---
    print("--- Running Step 1: Initial Search ---")
    search_and_save("top lithium battery manufacturers in china", filename="search_results.csv")
    
    print("\n" + "="*50 + "\n") # Separator

    # --- Step 2: Extract and Validate Companies (runs automatically after step 1) ---
    print("--- Running Step 2: Extracting and Validating Companies ---")
    extract_and_validate_companies(search_results_csv="search_results.csv")