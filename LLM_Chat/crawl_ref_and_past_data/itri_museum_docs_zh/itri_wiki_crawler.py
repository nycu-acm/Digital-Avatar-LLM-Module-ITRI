#!/usr/bin/env python3
"""
Enhanced ITRI Wikipedia Crawler
Crawls the ITRI Wikipedia page and extracts comprehensive structured data for the museum chatbot.
"""

import requests
from bs4 import BeautifulSoup
import json
import re
from datetime import datetime
import os
from typing import Dict, List, Any, Optional

class EnhancedITRIWikiCrawler:
    def __init__(self):
        self.base_url = "https://zh.wikipedia.org/zh-tw/工業技術研究院"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
    def fetch_page(self) -> str:
        """Fetch the ITRI Wikipedia page"""
        try:
            response = self.session.get(self.base_url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching page: {e}")
            return None

    def parse_content(self, html_content: str) -> Dict[str, Any]:
        """Parse the HTML content and extract comprehensive structured data"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Find the main content area
        content_div = soup.find('div', {'id': 'mw-content-text'})
        if not content_div:
            return {}
        
        data = {
            'organization_name': '工業技術研究院 (Industrial Technology Research Institute)',
            'english_name': 'Industrial Technology Research Institute',
            'abbreviation': 'ITRI',
            'crawled_at': datetime.now().isoformat(),
            'source_url': self.base_url,
            'sections': {},
            'leadership': {},
            'achievements': [],
            'organization_structure': {},
            'key_facts': {},
            'awards': [],
            'notable_alumni': [],
            'research_areas': [],
            'international_offices': [],
            'controversies': []
        }
        
        # Extract comprehensive information
        self._extract_basic_info(soup, data)
        self._extract_sections_enhanced(content_div, data)
        self._extract_leadership_enhanced(soup, data)
        self._extract_achievements_enhanced(soup, data)
        self._extract_organization_structure_enhanced(soup, data)
        self._extract_awards_and_honors(soup, data)
        self._extract_notable_alumni(soup, data)
        self._extract_research_areas(soup, data)
        self._extract_international_offices(soup, data)
        self._extract_controversies(soup, data)
        
        return data

    def _extract_basic_info(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract basic organization information from infobox"""
        infobox = soup.find('table', {'class': 'infobox'})
        if infobox:
            rows = infobox.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    key = cells[0].get_text(strip=True)
                    value = cells[1].get_text(strip=True)
                    if key and value:
                        data['key_facts'][key] = value

    def _extract_sections_enhanced(self, content_div: BeautifulSoup, data: Dict[str, Any]):
        """Enhanced section extraction with better structure"""
        sections = {}
        current_section = None
        current_content = []
        current_subsection = None
        subsections = {}
        
        for element in content_div.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'ul', 'ol', 'table']):
            if element.name in ['h1', 'h2', 'h3', 'h4']:
                # Save previous section
                if current_section and current_content:
                    if current_subsection:
                        subsections[current_subsection] = '\n'.join(current_content)
                        sections[current_section] = subsections
                    else:
                        sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = element.get_text(strip=True)
                current_content = []
                current_subsection = None
                subsections = {}
                
                # Check if this is a subsection
                if element.name in ['h3', 'h4'] and current_section:
                    current_subsection = current_section
                    
            elif current_section:
                if element.name == 'table':
                    # Extract table data
                    table_data = self._extract_table_data(element)
                    if table_data:
                        current_content.append(f"表格數據: {json.dumps(table_data, ensure_ascii=False)}")
                else:
                    text = element.get_text(strip=True)
                    if text:
                        current_content.append(text)
        
        # Save last section
        if current_section and current_content:
            if current_subsection:
                subsections[current_subsection] = '\n'.join(current_content)
                sections[current_section] = subsections
            else:
                sections[current_section] = '\n'.join(current_content)
        
        data['sections'] = sections

    def _extract_table_data(self, table: BeautifulSoup) -> List[Dict[str, str]]:
        """Extract structured data from tables"""
        table_data = []
        rows = table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) >= 2:
                row_data = {}
                for i, cell in enumerate(cells):
                    if i == 0:
                        row_data['key'] = cell.get_text(strip=True)
                    else:
                        row_data['value'] = cell.get_text(strip=True)
                if row_data:
                    table_data.append(row_data)
        
        return table_data

    def _extract_leadership_enhanced(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Enhanced leadership extraction"""
        leadership = {}
        
        # Look for leadership sections and tables
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if any(keyword in heading_text for keyword in ['院長', '領導', '組織', '管理']):
                # Extract the list of leaders
                next_element = heading.find_next_sibling()
                if next_element and next_element.name == 'ul':
                    leaders = []
                    for li in next_element.find_all('li'):
                        leader_text = li.get_text(strip=True)
                        if leader_text:
                            leaders.append(leader_text)
                    leadership[heading_text] = leaders
                elif next_element and next_element.name == 'table':
                    # Extract table data for leadership
                    table_data = self._extract_table_data(next_element)
                    if table_data:
                        leadership[heading_text] = table_data
        
        data['leadership'] = leadership

    def _extract_achievements_enhanced(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Enhanced achievements extraction"""
        achievements = []
        
        # Look for achievement-related content
        for element in soup.find_all(['p', 'li']):
            text = element.get_text(strip=True)
            if any(keyword in text for keyword in ['獎', '成就', '榮譽', '專利', '技術', '創新', '研發', '突破']):
                achievements.append(text)
        
        # Also look for specific achievement sections
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if any(keyword in heading_text for keyword in ['成就', '榮譽', '獎項', '專利']):
                next_element = heading.find_next_sibling()
                if next_element and next_element.name == 'ul':
                    for li in next_element.find_all('li'):
                        achievement_text = li.get_text(strip=True)
                        if achievement_text:
                            achievements.append(achievement_text)
        
        data['achievements'] = achievements

    def _extract_organization_structure_enhanced(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Enhanced organization structure extraction"""
        structure = {}
        
        # Look for organizational sections
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if any(keyword in heading_text for keyword in ['組織', '部門', '中心', '研究所', '架構']):
                # Extract the organizational structure
                next_element = heading.find_next_sibling()
                if next_element and next_element.name in ['ul', 'ol']:
                    departments = []
                    for li in next_element.find_all('li'):
                        dept_text = li.get_text(strip=True)
                        if dept_text:
                            departments.append(dept_text)
                    structure[heading_text] = departments
                elif next_element and next_element.name == 'table':
                    # Extract table data for organization structure
                    table_data = self._extract_table_data(next_element)
                    if table_data:
                        structure[heading_text] = table_data
        
        data['organization_structure'] = structure

    def _extract_awards_and_honors(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract awards and honors"""
        awards = []
        
        # Look for awards sections
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if any(keyword in heading_text for keyword in ['獎', '榮譽', '殊榮']):
                next_element = heading.find_next_sibling()
                if next_element and next_element.name == 'ul':
                    for li in next_element.find_all('li'):
                        award_text = li.get_text(strip=True)
                        if award_text:
                            awards.append(award_text)
        
        data['awards'] = awards

    def _extract_notable_alumni(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract notable alumni information"""
        alumni = []
        
        # Look for alumni sections
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if any(keyword in heading_text for keyword in ['院友', '校友', '傑出', '知名']):
                next_element = heading.find_next_sibling()
                if next_element and next_element.name == 'ul':
                    for li in next_element.find_all('li'):
                        alumni_text = li.get_text(strip=True)
                        if alumni_text:
                            alumni.append(alumni_text)
        
        data['notable_alumni'] = alumni

    def _extract_research_areas(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract research areas and focus areas"""
        research_areas = []
        
        # Look for research-related content
        for element in soup.find_all(['p', 'li']):
            text = element.get_text(strip=True)
            if any(keyword in text for keyword in ['研發', '技術', '領域', '產業', '科技']):
                research_areas.append(text)
        
        data['research_areas'] = research_areas

    def _extract_international_offices(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract international office information"""
        offices = []
        
        # Look for international office information
        for element in soup.find_all(['p', 'li']):
            text = element.get_text(strip=True)
            if any(keyword in text for keyword in ['美國', '歐洲', '日本', '辦事處', '海外']):
                offices.append(text)
        
        data['international_offices'] = offices

    def _extract_controversies(self, soup: BeautifulSoup, data: Dict[str, Any]):
        """Extract controversy information"""
        controversies = []
        
        # Look for controversy sections
        for heading in soup.find_all(['h2', 'h3']):
            heading_text = heading.get_text(strip=True)
            if any(keyword in heading_text for keyword in ['爭議', '爭論', '問題']):
                next_element = heading.find_next_sibling()
                if next_element and next_element.name in ['p', 'ul']:
                    if next_element.name == 'ul':
                        for li in next_element.find_all('li'):
                            controversy_text = li.get_text(strip=True)
                            if controversy_text:
                                controversies.append(controversy_text)
                    else:
                        controversy_text = next_element.get_text(strip=True)
                        if controversy_text:
                            controversies.append(controversy_text)
        
        data['controversies'] = controversies

    def create_enhanced_qa_pairs(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create comprehensive Q&A pairs for the chatbot"""
        qa_pairs = []
        
        # Basic organization info
        qa_pairs.extend([
            {
                "question": "什麼是工研院？",
                "answer": f"工研院（{data['organization_name']}）是台灣最重要的產業技術研發機構，專注於產業技術研發與創新。"
            },
            {
                "question": "工研院的英文名稱是什麼？",
                "answer": f"工研院的英文名稱是 {data['english_name']}，簡稱 ITRI。"
            },
            {
                "question": "工研院的主要任務是什麼？",
                "answer": "工研院的主要任務包括：產業技術研發、技術移轉、人才培育、產業服務等，致力於提升台灣產業競爭力。"
            },
            {
                "question": "工研院成立於哪一年？",
                "answer": "工研院成立於1973年，由時任經濟部長孫運璿推動成立。"
            },
            {
                "question": "工研院的總部在哪裡？",
                "answer": "工研院的總部位於台灣新竹，並在美國、歐洲、日本設有辦事處。"
            }
        ])
        
        # Add section-based Q&A
        if 'sections' in data:
            for section_name, content in data['sections'].items():
                if isinstance(content, dict):
                    # Handle subsections
                    for subsection_name, subsection_content in content.items():
                        if '沿革' in subsection_name or '歷史' in subsection_name:
                            qa_pairs.append({
                                "question": f"工研院的{subsection_name}如何？",
                                "answer": f"工研院的{subsection_name}：{subsection_content[:800]}..."
                            })
                else:
                    # Handle main sections
                    if '沿革' in section_name or '歷史' in section_name:
                        qa_pairs.append({
                            "question": "工研院的歷史沿革如何？",
                            "answer": f"工研院的歷史沿革：{content[:800]}..."
                        })
                    elif '組織' in section_name:
                        qa_pairs.append({
                            "question": "工研院的組織架構如何？",
                            "answer": f"工研院的組織架構：{content[:800]}..."
                        })
                    elif '榮譽' in section_name or '獎' in section_name:
                        qa_pairs.append({
                            "question": "工研院有哪些榮譽和獎項？",
                            "answer": f"工研院的榮譽和獎項：{content[:800]}..."
                        })
        
        # Add leadership Q&A
        if 'leadership' in data:
            for position, leaders in data['leadership'].items():
                if leaders:
                    if isinstance(leaders, list):
                        qa_pairs.append({
                            "question": f"工研院的{position}有哪些？",
                            "answer": f"工研院的{position}包括：{', '.join(leaders[:10])}"
                        })
                    elif isinstance(leaders, list) and len(leaders) > 0 and isinstance(leaders[0], dict):
                        # Handle table data
                        leader_names = [leader.get('value', '') for leader in leaders if leader.get('value')]
                        if leader_names:
                            qa_pairs.append({
                                "question": f"工研院的{position}有哪些？",
                                "answer": f"工研院的{position}包括：{', '.join(leader_names[:10])}"
                            })
        
        # Add achievements Q&A
        if 'achievements' in data and data['achievements']:
            qa_pairs.append({
                "question": "工研院有哪些重要成就？",
                "answer": f"工研院的重要成就包括：{'；'.join(data['achievements'][:10])}"
            })
        
        # Add awards Q&A
        if 'awards' in data and data['awards']:
            qa_pairs.append({
                "question": "工研院獲得過哪些獎項？",
                "answer": f"工研院獲得的重要獎項包括：{'；'.join(data['awards'][:10])}"
            })
        
        # Add alumni Q&A
        if 'notable_alumni' in data and data['notable_alumni']:
            qa_pairs.append({
                "question": "工研院有哪些傑出院友？",
                "answer": f"工研院的傑出院友包括：{'、'.join(data['notable_alumni'][:10])}"
            })
        
        # Add research areas Q&A
        if 'research_areas' in data and data['research_areas']:
            qa_pairs.append({
                "question": "工研院主要從事哪些研究領域？",
                "answer": f"工研院主要從事的研究領域包括：{'；'.join(data['research_areas'][:10])}"
            })
        
        # Add international presence Q&A
        if 'international_offices' in data and data['international_offices']:
            qa_pairs.append({
                "question": "工研院在海外有哪些辦事處？",
                "answer": f"工研院在海外設有辦事處，包括：{'；'.join(data['international_offices'][:5])}"
            })
        
        # Add controversies Q&A (if any)
        if 'controversies' in data and data['controversies']:
            qa_pairs.append({
                "question": "工研院曾經發生過哪些爭議事件？",
                "answer": f"工研院曾經發生過的爭議事件包括：{'；'.join(data['controversies'][:5])}"
            })
        
        return qa_pairs

    def save_enhanced_data(self, data: Dict[str, Any], output_dir: str = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_museum_docs_by_itri_wiki_crawler"):
        """Save the enhanced crawled data to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save raw data
        with open(os.path.join(output_dir, 'itri_wiki_raw_data.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Save enhanced Q&A pairs
        qa_pairs = self.create_enhanced_qa_pairs(data)
        with open(os.path.join(output_dir, 'itri_qa_pairs.json'), 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        
        # Save enhanced structured content
        structured_content = {
            'organization_info': {
                'name': data.get('organization_name', ''),
                'english_name': data.get('english_name', ''),
                'abbreviation': data.get('abbreviation', ''),
                'description': '台灣最重要的產業技術研發機構，專注於產業技術研發與創新'
            },
            'key_facts': data.get('key_facts', {}),
            'sections': data.get('sections', {}),
            'leadership': data.get('leadership', {}),
            'achievements': data.get('achievements', []),
            'organization_structure': data.get('organization_structure', {}),
            'awards': data.get('awards', []),
            'notable_alumni': data.get('notable_alumni', []),
            'research_areas': data.get('research_areas', []),
            'international_offices': data.get('international_offices', []),
            'controversies': data.get('controversies', [])
        }
        
        with open(os.path.join(output_dir, 'itri_structured_data.json'), 'w', encoding='utf-8') as f:
            json.dump(structured_content, f, ensure_ascii=False, indent=2)
        
        print(f"Enhanced data saved to {output_dir}/")
        print(f"- Raw data: itri_wiki_raw_data.json")
        print(f"- Q&A pairs: itri_qa_pairs.json")
        print(f"- Structured data: itri_structured_data.json")
        print(f"- Total Q&A pairs created: {len(qa_pairs)}")
        print(f"- Sections extracted: {len(data.get('sections', {}))}")
        print(f"- Achievements found: {len(data.get('achievements', []))}")
        print(f"- Awards found: {len(data.get('awards', []))}")
        print(f"- Notable alumni: {len(data.get('notable_alumni', []))}")

    def crawl(self, output_dir: str = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_museum_docs_by_itri_wiki_crawler"):
        """Main crawling method"""
        print("Starting Enhanced ITRI Wikipedia crawler...")
        
        # Fetch the page
        html_content = self.fetch_page()
        if not html_content:
            print("Failed to fetch the Wikipedia page")
            return None
        
        # Parse the content
        data = self.parse_content(html_content)
        if not data:
            print("Failed to parse the page content")
            return None
        
        # Save the enhanced data
        self.save_enhanced_data(data, output_dir)
        
        print(f"Enhanced crawling completed successfully!")
        print(f"Extracted {len(data.get('sections', {}))} sections")
        print(f"Found {len(data.get('achievements', []))} achievements")
        print(f"Found {len(data.get('awards', []))} awards")
        print(f"Found {len(data.get('notable_alumni', []))} notable alumni")
        print(f"Created {len(self.create_enhanced_qa_pairs(data))} Q&A pairs")
        
        return data

def main():
    """Main function to run the enhanced crawler"""
    crawler = EnhancedITRIWikiCrawler()
    data = crawler.crawl()
    
    if data:
        print("\nEnhanced crawling summary:")
        print(f"- Organization: {data.get('organization_name', 'N/A')}")
        print(f"- Sections found: {len(data.get('sections', {}))}")
        print(f"- Leadership positions: {len(data.get('leadership', {}))}")
        print(f"- Achievements: {len(data.get('achievements', []))}")
        print(f"- Awards: {len(data.get('awards', []))}")
        print(f"- Notable alumni: {len(data.get('notable_alumni', []))}")
        print(f"- Research areas: {len(data.get('research_areas', []))}")

if __name__ == "__main__":
    main()