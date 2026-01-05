import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse
from collections import deque
import time

# Configurable base URL and domain
BASE_URL = "https://www.itri.org.tw/index.aspx"
DOMAIN = "www.itri.org.tw"
MAX_PAGES = 5000
MAX_DEPTH = 2
OUTPUT_DIR = "LLM_Chat/itri_museum_docs_by_itri"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

visited_urls = set()
url_queue = deque([(BASE_URL, 0)])  # (url, depth)

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page_count = 0

    while url_queue and page_count < MAX_PAGES:
        url, depth = url_queue.popleft()
        if url in visited_urls or depth > MAX_DEPTH:
            continue

        print(f"Crawling ({page_count+1}/{MAX_PAGES}): {url} at depth {depth}")
        try:
            page = browser.new_page()
            page.goto(url, wait_until="networkidle", timeout=30000)
            html = page.content()
            # Handle JavaScript-based pagination if present
            soup = BeautifulSoup(html, "html.parser")
            pagination_container = soup.find('div', id='pagecontainer')
            if pagination_container:
                import re
                for a in pagination_container.find_all('a', onclick=True):
                    match = re.match(r'pageto\((\d+)\)', a['onclick'])
                    if match:
                        page_num = match.group(1)
                        try:
                            if not a.get('class') or 'on' not in a.get('class'):
                                page.goto(url, wait_until="networkidle", timeout=30000)
                                page.click(f'a[onclick="pageto({page_num})"]')
                                page.wait_for_load_state('networkidle')
                                paged_html = page.content()
                                paged_soup = BeautifulSoup(paged_html, "html.parser")
                                # Try to extract main content area if available
                                main_content = paged_soup.find(id="mainContent")
                                if not main_content:
                                    main_content = paged_soup.find(class_="mainContent")
                                if not main_content:
                                    main_content = paged_soup.body
                                text = main_content.get_text(separator="\n")
                                cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
                                if cleaned_lines and cleaned_lines[0] == "404 Error":
                                    print(f"Skipped 404 page: {url} (page {page_num})")
                                    continue
                                cleaned_text = "\n".join(cleaned_lines)
                                url_path = urllib.parse.urlparse(url).path.replace('/', '_').replace('#', '_') or 'index'
                                url_query = urllib.parse.urlparse(url).query.replace('&', '_').replace('=', '-')
                                filename = f"itri_content_{url_path}_{url_query}_page{page_num}.txt" if url_query else f"itri_content_{url_path}_page{page_num}.txt"
                                output_file = os.path.join(OUTPUT_DIR, filename)
                                if not os.path.exists(output_file):
                                    with open(output_file, "w", encoding="utf-8") as f:
                                        f.write(cleaned_text)
                                    print(f"Saved paginated content to '{output_file}'")
                                else:
                                    print(f"File already exists, skipping save: {output_file}")
                        except Exception as e:
                            print(f"Error handling pagination for page {page_num} at {url}: {e}")
            page.close()
            visited_urls.add(url)
            page_count += 1
            # Try to extract main content area if available
            main_content = soup.find(id="mainContent")
            if not main_content:
                main_content = soup.find(class_="mainContent")
            if not main_content:
                main_content = soup.body
            text = main_content.get_text(separator="\n")
            cleaned_lines = [line.strip() for line in text.splitlines() if line.strip()]
            if cleaned_lines and cleaned_lines[0] == "404 Error":
                print(f"Skipped 404 page: {url}")
                continue
            cleaned_text = "\n".join(cleaned_lines)
            url_path = urllib.parse.urlparse(url).path.replace('/', '_').replace('#', '_') or 'index'
            url_query = urllib.parse.urlparse(url).query.replace('&', '_').replace('=', '-')
            filename = f"itri_content_{url_path}_{url_query}.txt" if url_query else f"itri_content_{url_path}.txt"
            output_file = os.path.join(OUTPUT_DIR, filename)
            if not os.path.exists(output_file):
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(cleaned_text)
                print(f"Saved content to '{output_file}'")
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
                    is_pagination = text.isdigit() or text in pagination_keywords
                    if not is_pagination:
                        import re
                        if re.match(r"^第\d+頁$", text) or re.match(r"^Page \d+$", text, re.IGNORECASE):
                            is_pagination = True
                    if is_pagination:
                        full_url = urllib.parse.urljoin(url, href)
                    else:
                        full_url = urllib.parse.urljoin(BASE_URL, href)
                    parsed_url = urllib.parse.urlparse(full_url)
                    norm_url = parsed_url._replace(fragment="").geturl()
                    if parsed_url.netloc == DOMAIN and norm_url not in visited_urls and norm_url not in [u[0] for u in url_queue]:
                        url_queue.append((norm_url, depth + 1))
                        print(f"Added to queue: {norm_url} at depth {depth + 1}")
            time.sleep(2)
        except Exception as e:
            print(f"Error crawling {url}: {e}")
            continue

    browser.close()
    print(f"Crawling complete. Visited {page_count} pages.") 