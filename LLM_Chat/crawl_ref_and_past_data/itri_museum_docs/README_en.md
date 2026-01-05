# ITRI SDGS Website Crawler

This crawler is specifically designed to crawl the ITRI Sustainable Development Goals (SDGS) website at https://itrisdgs.itri.org.tw/chi/index.

## Features

- **Breadth-First Search**: Crawls the website systematically by following links
- **Content Extraction**: Extracts main content from pages while avoiding navigation elements
- **Smart Link Filtering**: Only follows relevant links within the same domain
- **Error Handling**: Skips error pages and handles exceptions gracefully
- **Rate Limiting**: Includes delays to be respectful to the server
- **Duplicate Prevention**: Avoids crawling the same page twice
- **Depth Control**: Limits crawling depth to prevent infinite loops

## Configuration

The crawler can be configured by modifying these variables in `itri_sdgs_crawler.py`:

- `MAX_PAGES`: Maximum number of pages to crawl (default: 1000)
- `MAX_DEPTH`: Maximum depth of crawling (default: 3)
- `OUTPUT_DIR`: Directory where crawled content will be saved

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

1. Activate your conda environment (if using):
```bash
conda activate env2
```

2. Run the crawler:
```bash
python itri_sdgs_crawler.py
```

## Output

The crawler will create text files in the `LLM_Chat/itri_sdgs_docs` directory. Each file contains:

- URL of the crawled page
- Depth at which it was found
- Timestamp of when it was crawled
- Extracted content from the page

## File Naming Convention

Files are named using the URL path, for example:
- `itri_sdgs_index.txt` (for the homepage)
- `itri_sdgs_chi_about.txt` (for /chi/about)
- `itri_sdgs_chi_news_article_id123.txt` (for news articles)

## Content Extraction Strategy

The crawler uses multiple strategies to extract content:

1. **Main Content Areas**: Looks for semantic HTML elements like `<main>`, `<article>`, etc.
2. **Section Extraction**: Identifies and extracts content from specific sections
3. **Navigation Context**: Captures navigation menus for context
4. **Text Cleaning**: Removes empty lines and formats text for readability

## Link Discovery

The crawler discovers new pages by:

1. Finding all `<a>` tags with `href` attributes
2. Filtering out non-content links (PDFs, mailto, javascript, etc.)
3. Ensuring links are within the same domain
4. Normalizing URLs to avoid duplicates

## Error Handling

- Skips 404 and error pages
- Handles network timeouts gracefully
- Continues crawling even if individual pages fail
- Logs errors for debugging

## Rate Limiting

The crawler includes a 1-second delay between requests to be respectful to the server and avoid being blocked.

## Monitoring

The crawler provides real-time feedback:
- Shows current page being crawled
- Reports number of new links found
- Displays file save status
- Shows final statistics

## Customization

You can modify the crawler for different websites by:

1. Changing `BASE_URL` and `DOMAIN`
2. Adjusting content extraction selectors in `extract_main_content()`
3. Modifying link filtering rules in `is_valid_link()`
4. Updating filename generation in `clean_filename()`