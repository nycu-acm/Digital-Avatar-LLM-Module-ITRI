#!/usr/bin/env python3
"""
Comprehensive ITRI Wikipedia Crawler
Extracts all information from the ITRI Wikipedia page and saves as text files.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
from typing import Dict, List, Any, Optional

class ITRIComprehensiveCrawler:
    def __init__(self):
        self.base_url = "https://zh.wikipedia.org/zh-tw/工業技術研究院"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def fetch_page(self) -> str:
        """Fetch the ITRI Wikipedia page"""
        try:
            print(f"Fetching page from: {self.base_url}")
            response = self.session.get(self.base_url)
            response.raise_for_status()
            print("Successfully fetched the Wikipedia page")
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def extract_all_content(self, html_content: str) -> Dict[str, Any]:
        """Extract all content from the Wikipedia page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the main content area
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            print("Could not find main content area")
            return {}
        
        print("Extracting comprehensive content...")
        
        data = {
            'metadata': {
                'organization_name': '工業技術研究院 (Industrial Technology Research Institute)',
                'english_name': 'Industrial Technology Research Institute',
                'abbreviation': 'ITRI',
                'crawled_at': datetime.now().isoformat(),
                'source_url': self.base_url,
                'total_sections': 0,
                'total_content_length': 0
            },
            'infobox_data': {},
            'sections': {},
            'tables': {},
            'lists': {},
            'references': [],
            'external_links': [],
            'categories': [],
            'raw_text': ""
        }
        
        # Extract infobox data
        self._extract_infobox(soup, data)
        
        # Extract all sections with subsections
        self._extract_all_sections(content_div, data)
        
        # Extract all tables
        self._extract_all_tables(content_div, data)
        
        # Extract all lists
        self._extract_all_lists(content_div, data)
        
        # Extract references and external links
        self._extract_references_and_links(soup, data)
        
        # Extract categories
        self._extract_categories(soup, data)
        
        # Extract raw text for full content
        self._extract_raw_text(content_div, data)
        
        # Update metadata
        data['metadata']['total_sections'] = len(data['sections'])
        data['metadata']['total_content_length'] = len(data['raw_text'])
        
        return data

    def _extract_infobox(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract all infobox data"""
        print("Extracting infobox data...")
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        data['infobox_data'][key] = value
            print(f"Extracted {len(data['infobox_data'])} infobox items")

    def _extract_all_sections(self, content_div: BeautifulSoup, data: Dict[str, Any]):
        """Extract all sections with their content"""
        print("Extracting all sections...")
        
        sections = {}
        current_section = None
        current_subsection = None
        current_content = []
        subsection_content = []
        
        # Find all headings and content
        for element in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'p', 'ul', 'ol', 'table', 'div']):
            if element.name in ['h1', 'h2', 'h3', 'h4', 'h5']:
                # Save previous subsection
                if current_subsection and subsection_content:
                    if current_section not in sections:
                        sections[current_section] = {}
                    elif isinstance(sections[current_section], str):
                        # Convert string to dict if needed
                        sections[current_section] = {}
                    sections[current_section][current_subsection] = '\n'.join(subsection_content)
                
                # Save previous section
                if current_section and current_content and not current_subsection:
                    sections[current_section] = '\n'.join(current_content)
                
                heading_text = element.get_text(strip=True)
                
                # Determine if this is a main section or subsection
                if element.name in ['h1', 'h2']:
                    # Main section
                    current_section = heading_text
                    current_content = []
                    current_subsection = None
                    subsection_content = []
                    print(f"Found main section: {heading_text}")
                else:
                    # Subsection
                    current_subsection = heading_text
                    subsection_content = []
                    print(f"Found subsection: {heading_text}")
                    
            elif current_section:
                text = element.get_text(strip=True)
                if text:
                    if current_subsection:
                        subsection_content.append(text)
                    else:
                        current_content.append(text)
        
        # Save last section and subsection
        if current_subsection and subsection_content:
            if current_section not in sections:
                sections[current_section] = {}
            elif isinstance(sections[current_section], str):
                # Convert string to dict if needed
                sections[current_section] = {}
            sections[current_section][current_subsection] = '\n'.join(subsection_content)
        elif current_section and current_content:
            sections[current_section] = '\n'.join(current_content)
        
        data['sections'] = sections
        print(f"Extracted {len(sections)} main sections")

    def _extract_all_tables(self, content_div: BeautifulSoup, data: Dict[str, Any]):
        """Extract all tables with their data"""
        print("Extracting all tables...")
        
        tables = {}
        table_count = 0
        
        for table in content_div.find_all('table'):
            table_count += 1
            table_data = []
            
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if cells:
                    row_data = []
                    for cell in cells:
                        cell_text = cell.get_text(strip=True)
                        if cell_text:
                            row_data.append(cell_text)
                    if row_data:
                        table_data.append(row_data)
            
            if table_data:
                tables[f"table_{table_count}"] = {
                    'rows': table_data,
                    'row_count': len(table_data),
                    'column_count': max(len(row) for row in table_data) if table_data else 0
                }
        
        data['tables'] = tables
        print(f"Extracted {len(tables)} tables")

    def _extract_all_lists(self, content_div: BeautifulSoup, data: Dict[str, Any]):
        """Extract all lists (ul, ol)"""
        print("Extracting all lists...")
        
        lists = {}
        list_count = 0
        
        for list_element in content_div.find_all(['ul', 'ol']):
            list_count += 1
            list_items = []
            
            for li in list_element.find_all('li'):
                item_text = li.get_text(strip=True)
                if item_text:
                    list_items.append(item_text)
            
            if list_items:
                lists[f"list_{list_count}"] = {
                    'type': list_element.name,
                    'items': list_items,
                    'item_count': len(list_items)
                }
        
        data['lists'] = lists
        print(f"Extracted {len(lists)} lists")

    def _extract_references_and_links(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract references and external links"""
        print("Extracting references and external links...")
        
        # Find references section
        for heading in soup.find_all(['h2', 'h3', 'h4']):
            heading_text = heading.get_text(strip=True)
            if '參考' in heading_text or '文獻' in heading_text:
                next_element = heading.find_next_sibling()
                if next_element and next_element.name in ['ul', 'ol']:
                    for li in next_element.find_all('li'):
                        ref_text = li.get_text(strip=True)
                        if ref_text:
                            data['references'].append(ref_text)
            
            elif '外部連結' in heading_text:
                next_element = heading.find_next_sibling()
                if next_element and next_element.name in ['ul', 'ol']:
                    for li in next_element.find_all('li'):
                        link_text = li.get_text(strip=True)
                        if link_text:
                            data['external_links'].append(link_text)
        
        print(f"Extracted {len(data['references'])} references")
        print(f"Extracted {len(data['external_links'])} external links")

    def _extract_categories(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract page categories"""
        print("Extracting categories...")
        
        category_div = soup.find('div', {'id': 'mw-normal-catlinks'})
        if category_div:
            for link in category_div.find_all('a'):
                category_text = link.get_text(strip=True)
                if category_text and category_text != '隱藏分類':
                    data['categories'].append(category_text)
        
        print(f"Extracted {len(data['categories'])} categories")

    def _extract_raw_text(self, content_div: BeautifulSoup, data: Dict[str, Any]):
        """Extract raw text content"""
        print("Extracting raw text content...")
        
        # Remove script and style elements
        for script in content_div(["script", "style"]):
            script.decompose()
        
        # Get all text
        raw_text = content_div.get_text()
        # Clean up whitespace
        raw_text = re.sub(r'\s+', ' ', raw_text).strip()
        
        data['raw_text'] = raw_text
        print(f"Extracted {len(raw_text)} characters of raw text")

    def save_as_text_files(self, data: Dict[str, Any], output_dir: str = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_comprehensive_data"):
        """Save all extracted data as text files"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"Saving data to {output_dir}/")
        
        # Save metadata
        with open(os.path.join(output_dir, 'metadata.txt'), 'w', encoding='utf-8') as f:
            f.write("# ITRI Wikipedia Crawler Metadata\n\n")
            for key, value in data['metadata'].items():
                f.write(f"{key}: {value}\n")
        
        # Save infobox data
        if data['infobox_data']:
            with open(os.path.join(output_dir, 'infobox.txt'), 'w', encoding='utf-8') as f:
                f.write("# ITRI Infobox Data\n\n")
                for key, value in data['infobox_data'].items():
                    f.write(f"{key}: {value}\n")
        
        # Save sections
        for section_name, content in data['sections'].items():
            safe_name = re.sub(r'[^\w\s-]', '', section_name).replace(' ', '_')
            if isinstance(content, str):
                with open(os.path.join(output_dir, f'section_{safe_name}.txt'), 'w', encoding='utf-8') as f:
                    f.write(f"# {section_name}\n\n")
                    f.write(content)
            elif isinstance(content, dict):
                with open(os.path.join(output_dir, f'section_{safe_name}.txt'), 'w', encoding='utf-8') as f:
                    f.write(f"# {section_name}\n\n")
                    for subsection_name, subsection_content in content.items():
                        f.write(f"## {subsection_name}\n\n")
                        f.write(subsection_content)
                        f.write("\n\n")
        
        # Save tables
        if data['tables']:
            with open(os.path.join(output_dir, 'tables.txt'), 'w', encoding='utf-8') as f:
                f.write("# ITRI Wikipedia Tables\n\n")
                for table_name, table_data in data['tables'].items():
                    f.write(f"## {table_name}\n")
                    f.write(f"Rows: {table_data['row_count']}, Columns: {table_data['column_count']}\n\n")
                    for row in table_data['rows']:
                        f.write("| " + " | ".join(row) + " |\n")
                    f.write("\n")
        
        # Save lists
        if data['lists']:
            with open(os.path.join(output_dir, 'lists.txt'), 'w', encoding='utf-8') as f:
                f.write("# ITRI Wikipedia Lists\n\n")
                for list_name, list_data in data['lists'].items():
                    f.write(f"## {list_name} ({list_data['type']})\n")
                    f.write(f"Items: {list_data['item_count']}\n\n")
                    for item in list_data['items']:
                        f.write(f"- {item}\n")
                    f.write("\n")
        
        # Save references
        if data['references']:
            with open(os.path.join(output_dir, 'references.txt'), 'w', encoding='utf-8') as f:
                f.write("# ITRI Wikipedia References\n\n")
                for i, ref in enumerate(data['references'], 1):
                    f.write(f"{i}. {ref}\n")
        
        # Save external links
        if data['external_links']:
            with open(os.path.join(output_dir, 'external_links.txt'), 'w', encoding='utf-8') as f:
                f.write("# ITRI Wikipedia External Links\n\n")
                for i, link in enumerate(data['external_links'], 1):
                    f.write(f"{i}. {link}\n")
        
        # Save categories
        if data['categories']:
            with open(os.path.join(output_dir, 'categories.txt'), 'w', encoding='utf-8') as f:
                f.write("# ITRI Wikipedia Categories\n\n")
                for category in data['categories']:
                    f.write(f"- {category}\n")
        
        # Save raw text
        with open(os.path.join(output_dir, 'raw_text.txt'), 'w', encoding='utf-8') as f:
            f.write("# ITRI Wikipedia Raw Text\n\n")
            f.write(data['raw_text'])
        
        # Save comprehensive JSON
        with open(os.path.join(output_dir, 'comprehensive_data.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Create summary file
        with open(os.path.join(output_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
            f.write("# ITRI Wikipedia Crawler Summary\n\n")
            f.write(f"Organization: {data['metadata']['organization_name']}\n")
            f.write(f"Crawled at: {data['metadata']['crawled_at']}\n")
            f.write(f"Source URL: {data['metadata']['source_url']}\n\n")
            f.write(f"Total sections: {data['metadata']['total_sections']}\n")
            f.write(f"Total content length: {data['metadata']['total_content_length']} characters\n")
            f.write(f"Infobox items: {len(data['infobox_data'])}\n")
            f.write(f"Tables: {len(data['tables'])}\n")
            f.write(f"Lists: {len(data['lists'])}\n")
            f.write(f"References: {len(data['references'])}\n")
            f.write(f"External links: {len(data['external_links'])}\n")
            f.write(f"Categories: {len(data['categories'])}\n\n")
            
            f.write("## Section Names:\n")
            for section_name in data['sections'].keys():
                f.write(f"- {section_name}\n")
        
        print("All data saved successfully!")
        print(f"Files created in {output_dir}/:")
        print("- metadata.txt")
        print("- infobox.txt")
        print("- section_*.txt (multiple files)")
        print("- tables.txt")
        print("- lists.txt")
        print("- references.txt")
        print("- external_links.txt")
        print("- categories.txt")
        print("- raw_text.txt")
        print("- comprehensive_data.json")
        print("- summary.txt")

    def crawl(self, output_dir: str = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_comprehensive_data"):
        """Main crawling method"""
        print("Starting Comprehensive ITRI Wikipedia Crawler...")
        print("=" * 50)
        
        # Fetch the page
        html_content = self.fetch_page()
        if not html_content:
            print("Failed to fetch the Wikipedia page")
            return None
        
        # Extract all content
        data = self.extract_all_content(html_content)
        if not data:
            print("Failed to extract content from the page")
            return None
        
        # Save all data as text files
        self.save_as_text_files(data, output_dir)
        
        print("\n" + "=" * 50)
        print("Crawling completed successfully!")
        print(f"Organization: {data['metadata']['organization_name']}")
        print(f"Total sections extracted: {data['metadata']['total_sections']}")
        print(f"Total content length: {data['metadata']['total_content_length']} characters")
        print(f"Infobox items: {len(data['infobox_data'])}")
        print(f"Tables extracted: {len(data['tables'])}")
        print(f"Lists extracted: {len(data['lists'])}")
        print(f"References: {len(data['references'])}")
        print(f"External links: {len(data['external_links'])}")
        print(f"Categories: {len(data['categories'])}")
        
        return data

def main():
    """Main function to run the comprehensive crawler"""
    crawler = ITRIComprehensiveCrawler()
    data = crawler.crawl()
    
    if data:
        print("\nCrawling Summary:")
        print(f"- Organization: {data['metadata']['organization_name']}")
        print(f"- Sections found: {data['metadata']['total_sections']}")
        print(f"- Content length: {data['metadata']['total_content_length']} characters")
        print(f"- Data saved to: /mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_comprehensive_data/")

if __name__ == "__main__":
    main() 