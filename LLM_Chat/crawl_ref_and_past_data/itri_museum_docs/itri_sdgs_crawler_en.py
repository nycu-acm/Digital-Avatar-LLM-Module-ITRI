import os
from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import urllib.parse
from collections import deque
import time
import re

# Configurable base URL and domain for ITRI SDGS
BASE_URL = "https://itrisdgs.itri.org.tw/chi/index"
DOMAIN = "itrisdgs.itri.org.tw"
MAX_PAGES = 1000
MAX_DEPTH = 3
OUTPUT_DIR = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_sdgs_docs"
if not os.path.exists(OUTPUT_DIR):
os.makedirs(OUTPUT_DIR)

visited_urls = set()
url_queue = deque([(BASE_URL, 0)])  # (url, depth)

def clean_filename(url):
"""Create a clean filename from URL"""
parsed = urllib.parse.urlparse(url)
path = parsed.path.replace('/', '_').replace('#', '_') or 'index'
query = parsed.query.replace('&', '_').replace('=', '-') if parsed.query else ''

# Clean up the path to make it more readable
path = re.sub(r'_+', '_', path)  # Replace multiple underscores with single
path = path.strip('_')  # Remove leading/trailing underscores

if query:
return f"itri_sdgs_{path}_{query}.txt"
else:
return f"itri_sdgs_{path}.txt"

def extract_main_content(soup, url):
"""Extract main content from the page, handling ITRI SDGS specific structure"""
content_parts = []

# Try to find main content areas specific to ITRI SDGS
main_selectors = [
'main',
'#main',
'.main-content',
'.content',
'#content',
'article',
'.article',
'.page-content'
]

main_content = None
for selector in main_selectors:
main_content = soup.select_one(selector)
if main_content:
break

# If no main content found, try body
if not main_content:
main_content = soup.body

if main_content:
# Extract text content
text = main_content.get_text(separator="\n", strip=True)
content_parts.append(text)

# Extract specific sections that might be important
sections = main_content.find_all(['section', 'div'], class_=re.compile(r'(content|section|block|item)'))
for section in sections:
section_text = section.get_text(separator="\n", strip=True)
if section_text and len(section_text) > 50:  # Only add substantial content
content_parts.append(f"\n--- Section ---\n{section_text}")

# Also extract any lists or navigation that might contain important links
nav_items = soup.find_all(['nav', 'ul', 'ol'])
for nav in nav_items:
nav_text = nav.get_text(separator="\n", strip=True)
if nav_text and len(nav_text) > 20:
content_parts.append(f"\n--- Navigation ---\n{nav_text}")

return "\n\n".join(content_parts)

def is_valid_link(href, base_url):
"""Check if a link should be followed"""
if not href:
return False

# Skip common non-content links
skip_patterns = [
r'^javascript:',
r'^mailto:',
r'^tel:',
r'^#',
r'\.pdf$',
r'\.doc$',
r'\.docx$',
r'\.xls$',
r'\.xlsx$',
r'\.zip$',
r'\.rar$'
]

for pattern in skip_patterns:
if re.search(pattern, href, re.IGNORECASE):
return False

# Must be same domain
try:
full_url = urllib.parse.urljoin(base_url, href)
parsed = urllib.parse.urlparse(full_url)
return parsed.netloc == DOMAIN
except:
return False

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

# Set viewport and user agent for better compatibility
page.set_viewport_size({"width": 1920, "height": 1080})
page.set_extra_http_headers({
"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
})

# Navigate to the page
page.goto(url, wait_until="networkidle", timeout=30000)

# Wait a bit for any dynamic content to load
page.wait_for_timeout(2000)

# Get the HTML content
html = page.content()
soup = BeautifulSoup(html, "html.parser")

# Extract main content
content = extract_main_content(soup, url)

if content and len(content.strip()) > 50:  # Only save if there's substantial content
# Clean the content
lines = [line.strip() for line in content.splitlines() if line.strip()]
cleaned_content = "\n".join(lines)

# Skip if it's an error page
if cleaned_content.startswith("404") or "error" in cleaned_content.lower():
print(f"Skipped error page: {url}")
page.close()
visited_urls.add(url)
page_count += 1
continue

# Create filename and save
filename = clean_filename(url)
output_file = os.path.join(OUTPUT_DIR, filename)

if not os.path.exists(output_file):
with open(output_file, "w", encoding="utf-8") as f:
f.write(f"URL: {url}\n")
f.write(f"Depth: {depth}\n")
f.write(f"Crawled: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
f.write("=" * 50 + "\n")
f.write(cleaned_content)
print(f"Saved content to '{output_file}' ({len(cleaned_content)} characters)")
else:
print(f"File already exists, skipping save: {output_file}")

# Find new links to add to queue
if depth < MAX_DEPTH:
links_found = 0
for link in soup.find_all('a', href=True):
href = link['href']

if is_valid_link(href, url):
full_url = urllib.parse.urljoin(url, href)
parsed_url = urllib.parse.urlparse(full_url)
norm_url = parsed_url._replace(fragment="").geturl()

if norm_url not in visited_urls and norm_url not in [u[0] for u in url_queue]:
url_queue.append((norm_url, depth + 1))
links_found += 1
print(f"Added to queue: {norm_url} at depth {depth + 1}")

print(f"Found {links_found} new links on this page")

page.close()
visited_urls.add(url)
page_count += 1

# Rate limiting
time.sleep(1)

except Exception as e:
print(f"Error crawling {url}: {e}")
continue

browser.close()
print(f"Crawling complete. Visited {page_count} pages.")
print(f"Total unique URLs found: {len(visited_urls)}")