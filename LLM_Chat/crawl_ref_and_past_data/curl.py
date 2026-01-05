import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse
from collections import deque
import time
import requests

# Base URL and domain to restrict crawling
BASE_URL = "https://50th.itri.org.tw/"
DOMAIN = "50th.itri.org.tw"
# Maximum number of pages to crawl and maximum depth
MAX_PAGES = 5000
MAX_DEPTH = 2
# Output directory for saving content
OUTPUT_DIR = "LLM_Chat/itri_museum_docs_by_curl"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Set to keep track of visited URLs
visited_urls = set()
# Queue for BFS
url_queue = deque([(BASE_URL + "#index-activity", 0)])  # (url, depth)

def is_pdf_url(url):
    return url.lower().endswith('.pdf')

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page_count = 0
    
    while url_queue and page_count < MAX_PAGES:
        url, depth = url_queue.popleft()
        if url in visited_urls or depth > MAX_DEPTH:
            continue
        
        print(f"Crawling ({page_count+1}/{MAX_PAGES}): {url} at depth {depth}")
        try:
            if is_pdf_url(url):
                try:
                    url_path = urllib.parse.urlparse(url).path.replace('/', '_').replace('#', '_') or 'index'
                    output_file = os.path.join(OUTPUT_DIR, f"itri_content_{url_path}.pdf")
                    if os.path.exists(output_file):
                        print(f"File already exists, skipping: {output_file}")
                        visited_urls.add(url)
                        page_count += 1
                        continue
                    response = requests.get(url, timeout=30)
                    if response.status_code == 200:
                        with open(output_file, "wb") as f:
                            f.write(response.content)
                        print(f"Debug: Saved PDF to '{output_file}'")
                    else:
                        print(f"Failed to download PDF: {url} (status {response.status_code})")
                except Exception as e:
                    print(f"Error downloading PDF {url}: {e}")
                visited_urls.add(url)
                page_count += 1
                continue

            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            # Handle JavaScript-based pagination if present
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, "html.parser")
            pagination_container = soup.find('div', id='pagecontainer')
            if pagination_container:
                # Sequentially click the 'next' button to navigate pages
                try:
                    # Find the total number of pages from the last page button
                    import re
                    last_page_btn = None
                    for a in pagination_container.find_all('a', onclick=True):
                        match = re.match(r'pageto\((\d+)\)', a['onclick'])
                        if match:
                            last_page_btn = max(int(match.group(1)), int(last_page_btn) if last_page_btn else 1)
                    if last_page_btn and last_page_btn > 1:
                        for page_num in range(2, last_page_btn + 1):
                            page.goto(url, wait_until="networkidle", timeout=30000)
                            # Click 'next' button to go to the next page
                            try:
                                next_btn = page.locator('a.next')
                                next_btn.wait_for(state='visible', timeout=5000)
                                next_btn.click()
                                page.wait_for_load_state('networkidle')
                                paged_html = page.content()
                                paged_soup = BeautifulSoup(paged_html, "html.parser")
                                # Save content for this page number
                                url_path = urllib.parse.urlparse(url).path.replace('/', '_').replace('#', '_') or 'index'
                                output_file = os.path.join(OUTPUT_DIR, f"itri_content_{url_path}_page{page_num}.txt")
                                if not os.path.exists(output_file):
                                    paged_text = paged_soup.get_text(separator="\n")
                                    cleaned_paged_text = "\n".join(line.strip() for line in paged_text.splitlines() if line.strip())
                                    with open(output_file, "w", encoding="utf-8") as f:
                                        f.write(cleaned_paged_text)
                                    print(f"Debug: Saved paginated content to '{output_file}'")
                                else:
                                    print(f"File already exists, skipping save: {output_file}")
                            except Exception as e:
                                print(f"Error handling sequential pagination for page {page_num} at {url}: {e}")
                except Exception as e:
                    print(f"Error in sequential pagination logic at {url}: {e}")
            page.close()
            # Mark as visited
            visited_urls.add(url)
            page_count += 1
            # Parse HTML with BeautifulSoup (already done above)
            # Extract text and clean up multiple blank lines
            text = soup.get_text(separator="\n")
            cleaned_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
            # Save the cleaned text to a file named after the URL path
            url_path = urllib.parse.urlparse(url).path.replace('/', '_').replace('#', '_') or 'index'
            output_file = os.path.join(OUTPUT_DIR, f"itri_content_{url_path}.txt")
            if not os.path.exists(output_file):
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)
                print(f"Debug: Saved content to '{output_file}'")
            else:
                print(f"File already exists, skipping save: {output_file}")
            # Find all links on the page if within depth limit
            if depth < MAX_DEPTH:
                pagination_keywords = [
                    "下一頁", "下一步", "Next", ">", ">>", "上一頁", "Prev", "<", "<<", "更多", "載入更多", "More", "Load More", "...", "»", "«"
                ]
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    text = link.text.strip()
                    # Check if this is a pagination link (numbered page or keyword)
                    is_pagination = text.isdigit() or text in pagination_keywords
                    # Also match patterns like '第X頁', 'Page X'
                    if not is_pagination:
                        import re
                        if re.match(r"^第\d+頁$", text) or re.match(r"^Page \d+$", text, re.IGNORECASE):
                            is_pagination = True
                    if is_pagination:
                        full_url = urllib.parse.urljoin(url, href)
                    else:
                        full_url = urllib.parse.urljoin(BASE_URL, href)
                    parsed_url = urllib.parse.urlparse(full_url)
                    # Normalize URL (remove fragment, sort query params)
                    norm_url = parsed_url._replace(fragment="").geturl()
                    if parsed_url.netloc == DOMAIN and norm_url not in visited_urls and norm_url not in [u[0] for u in url_queue]:
                        url_queue.append((norm_url, depth + 1))
                        print(f"Added to queue: {norm_url} at depth {depth + 1}")
            # Small delay to avoid overwhelming the server
            time.sleep(2)
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            continue
    
    browser.close()
    print(f"Crawling complete. Visited {page_count} pages.")