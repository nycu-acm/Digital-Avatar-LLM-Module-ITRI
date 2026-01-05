import os
import requests
from bs4 import BeautifulSoup

# Target URL
TARGET_URL = "https://www.itri.org.tw/ListStyle.aspx?DisplayStyle=01_content&SiteID=1&MmmID=1036276263153520257&MGID=112111012485164330"
# Output directory (same as previous script)
OUTPUT_DIR = "LLM_Chat/itri_museum_docs"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

# Output file name
output_file = os.path.join(OUTPUT_DIR, "itri_news.txt")

try:
    print(f"Fetching: {TARGET_URL}")
    response = requests.get(TARGET_URL, timeout=30)
    response.raise_for_status()
    html = response.text

    # Parse HTML
    soup = BeautifulSoup(html, "html.parser")

    # Try to extract the main content area
    # (工研院網站主要內容區塊有 id="mainContent" 或 class="mainContent"，若無則取全部文字)
    main_content = soup.find(id="mainContent")
    if not main_content:
        main_content = soup.find(class_="mainContent")
    if not main_content:
        main_content = soup.body

    # Clean and extract text
    text = main_content.get_text(separator="\n")
    cleaned_text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

    # Save to file
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(cleaned_text)
    print(f"Saved content to '{output_file}'")
except Exception as e:
    print(f"Error fetching or parsing: {e}") 