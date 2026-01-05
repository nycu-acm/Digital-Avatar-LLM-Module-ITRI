#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Direct ITRI Website Crawler
Uses the content we successfully extracted from our test to create comprehensive data
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List

class DirectITRICrawler:
    def __init__(self):
        self.base_url = "https://www.itri.org.tw"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def fetch_main_page(self) -> str:
        """Fetch the main page content"""
        try:
            print(f"Fetching main page: {self.base_url}/index.aspx")
            response = self.session.get(f"{self.base_url}/index.aspx", timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"Error fetching main page: {e}")
            return None
    
    def extract_main_content(self, html_content: str) -> Dict[str, Any]:
        """Extract comprehensive content from main page"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts and styles
        for element in soup.find_all(['script', 'style']):
            element.decompose()
        
        # Extract all text content
        all_text = soup.get_text(separator='\n', strip=True)
        
        # Extract navigation and menu items
        navigation = []
        for link in soup.find_all('a', href=True):
            text = link.get_text(strip=True)
            href = link.get('href', '')
            if text and href:
                navigation.append({
                    'text': text,
                    'href': href,
                    'title': link.get('title', '')
                })
        
        # Extract sections based on headings
        sections = {}
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = heading.get_text(strip=True)
            if heading_text:
                # Get content until next heading
                content = []
                next_element = heading.find_next_sibling()
                
                while next_element and next_element.name not in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
                    if next_element.name in ['p', 'div', 'span', 'li']:
                        text = next_element.get_text(strip=True)
                        if text:
                            content.append(text)
                    next_element = next_element.find_next_sibling()
                
                if content:
                    sections[heading_text] = '\n'.join(content)
        
        # Extract title
        title = soup.find('title')
        page_title = title.get_text(strip=True) if title else "工業技術研究院-首頁"
        
        return {
            'title': page_title,
            'all_text': all_text,
            'navigation': navigation,
            'sections': sections,
            'url': f"{self.base_url}/index.aspx"
        }
    
    def categorize_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Categorize the extracted content"""
        all_text = content.get('all_text', '')
        navigation = content.get('navigation', [])
        
        categories = {
            'technologies': [],
            'news': [],
            'about': [],
            'services': [],
            'organization': [],
            'contact': [],
            'other': []
        }
        
        # Categorize navigation items
        for item in navigation:
            text = item['text'].lower()
            href = item['href'].lower()
            
            # Technology related
            if any(keyword in text or keyword in href for keyword in ['技術', '科技', '智慧', '尖端', 'technology', 'tech']):
                categories['technologies'].append(item)
            
            # News related
            elif any(keyword in text or keyword in href for keyword in ['新聞', '公告', '消息', 'news']):
                categories['news'].append(item)
            
            # About related
            elif any(keyword in text or keyword in href for keyword in ['關於', '院長', '組織', 'about']):
                categories['about'].append(item)
            
            # Services related
            elif any(keyword in text or keyword in href for keyword in ['服務', '產業', 'service', 'industry']):
                categories['services'].append(item)
            
            # Organization related
            elif any(keyword in text or keyword in href for keyword in ['組織', '架構', '部門', '中心']):
                categories['organization'].append(item)
            
            # Contact related
            elif any(keyword in text or keyword in href for keyword in ['聯絡', '地址', '電話', 'contact']):
                categories['contact'].append(item)
            
            else:
                categories['other'].append(item)
        
        # Extract specific content from text
        text_sections = {
            'technologies': [],
            'news': [],
            'achievements': [],
            'organization_info': [],
            'contact_info': []
        }
        
        # Split text into lines and categorize
        lines = all_text.split('\n')
        current_section = 'other'
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            line_lower = line.lower()
            
            # Technology content
            if any(keyword in line_lower for keyword in ['技術', '科技', '智慧', '尖端', '研發', '創新', '專利']):
                text_sections['technologies'].append(line)
            
            # News content
            elif any(keyword in line_lower for keyword in ['新聞', '公告', '消息', '發布', '活動']):
                text_sections['news'].append(line)
            
            # Achievement content
            elif any(keyword in line_lower for keyword in ['成就', '獎項', '榮譽', '獲獎', '認證']):
                text_sections['achievements'].append(line)
            
            # Organization content
            elif any(keyword in line_lower for keyword in ['組織', '架構', '部門', '中心', '院長', '主管']):
                text_sections['organization_info'].append(line)
            
            # Contact content
            elif any(keyword in line_lower for keyword in ['聯絡', '地址', '電話', 'email', '信箱']):
                text_sections['contact_info'].append(line)
        
        return {
            'navigation_categories': categories,
            'text_sections': text_sections
        }
    
    def create_comprehensive_data(self, content: Dict[str, Any], categories: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive data structure"""
        
        # Extract key information from text
        all_text = content.get('all_text', '')
        
        # Find organization name
        org_name = "工業技術研究院"
        if "工業技術研究院" in all_text:
            org_name = "工業技術研究院"
        
        # Extract main sections
        sections = content.get('sections', {})
        
        # Create comprehensive data structure
        comprehensive_data = {
            'metadata': {
                'source_url': self.base_url,
                'crawl_timestamp': datetime.now().isoformat(),
                'organization_name': org_name,
                'english_name': 'Industrial Technology Research Institute',
                'abbreviation': 'ITRI'
            },
            'main_page': {
                'title': content.get('title', ''),
                'url': content.get('url', ''),
                'content': all_text,
                'sections': sections
            },
            'navigation': {
                'all_links': content.get('navigation', []),
                'categories': categories.get('navigation_categories', {})
            },
            'content_sections': categories.get('text_sections', {}),
            'technologies': [],
            'news_articles': [],
            'achievements': [],
            'organization_info': {},
            'contact_info': {},
            'qa_pairs': []
        }
        
        # Process technologies
        tech_content = categories.get('text_sections', {}).get('technologies', [])
        for tech in tech_content:
            comprehensive_data['technologies'].append({
                'title': tech[:50] + '...' if len(tech) > 50 else tech,
                'content': tech,
                'category': 'technology'
            })
        
        # Process news
        news_content = categories.get('text_sections', {}).get('news', [])
        for news in news_content:
            comprehensive_data['news_articles'].append({
                'title': news[:50] + '...' if len(news) > 50 else news,
                'content': news,
                'category': 'news'
            })
        
        # Process achievements
        achievement_content = categories.get('text_sections', {}).get('achievements', [])
        for achievement in achievement_content:
            comprehensive_data['achievements'].append({
                'title': achievement[:50] + '...' if len(achievement) > 50 else achievement,
                'content': achievement,
                'category': 'achievement'
            })
        
        # Process organization info
        org_content = categories.get('text_sections', {}).get('organization_info', [])
        if org_content:
            comprehensive_data['organization_info'] = {
                'content': '\n'.join(org_content),
                'sections': org_content
            }
        
        # Process contact info
        contact_content = categories.get('text_sections', {}).get('contact_info', [])
        if contact_content:
            comprehensive_data['contact_info'] = {
                'content': '\n'.join(contact_content),
                'sections': contact_content
            }
        
        return comprehensive_data
    
    def create_qa_pairs(self, data: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create comprehensive Q&A pairs"""
        qa_pairs = []
        
        # Basic ITRI information
        qa_pairs.extend([
            {
                "question": "什麼是工研院？",
                "answer": "工研院（工業技術研究院）是台灣最重要的產業技術研發機構，專注於產業技術研發與創新，致力於提升台灣產業競爭力。"
            },
            {
                "question": "工研院的主要任務是什麼？",
                "answer": "工研院的主要任務包括：產業技術研發、技術移轉、人才培育、產業服務等，致力於提升台灣產業競爭力。"
            },
            {
                "question": "工研院的英文名稱是什麼？",
                "answer": "工研院的英文名稱是 Industrial Technology Research Institute，簡稱 ITRI。"
            },
            {
                "question": "工研院的官方網站是什麼？",
                "answer": "工研院的官方網站是 https://www.itri.org.tw"
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
        
        # Add content-based Q&A
        main_content = data.get('main_page', {}).get('content', '')
        
        # Technology Q&A
        if '尖端科技' in main_content:
            qa_pairs.append({
                "question": "工研院有哪些尖端科技？",
                "answer": "工研院的尖端科技包括：智慧生活、人機互動與服務、自主移動系統、智慧消費與運籌服務、智慧化致能技術、人工智慧與資安、半導體晶片、通訊、智慧感測等領域。"
            })
        
        if '智慧生活' in main_content:
            qa_pairs.append({
                "question": "工研院在智慧生活方面有什麼技術？",
                "answer": "工研院在智慧生活方面的技術包括：人機互動與服務、自主移動系統、智慧消費與運籌服務、智慧化致能技術等。"
            })
        
        if '健康樂活' in main_content:
            qa_pairs.append({
                "question": "工研院在健康樂活方面有什麼技術？",
                "answer": "工研院在健康樂活方面的技術包括：智慧醫療、健康照護等領域。"
            })
        
        if '永續環境' in main_content:
            qa_pairs.append({
                "question": "工研院在永續環境方面有什麼技術？",
                "answer": "工研院在永續環境方面的技術包括：循環經濟、低碳製造、綠能系統與環境科技等。"
            })
        
        if '韌性社會' in main_content:
            qa_pairs.append({
                "question": "工研院在韌性社會方面有什麼技術？",
                "answer": "工研院在韌性社會方面的技術包括：基礎設施韌性、資源能源韌性、生產力韌性等。"
            })
        
        # Services Q&A
        if '產業服務' in main_content:
            qa_pairs.append({
                "question": "工研院提供哪些產業服務？",
                "answer": "工研院提供的產業服務包括：技術移轉、淨零排放服務、檢測服務、產業人才培訓、產業趨勢與情報、開放實驗室與創業育成等。"
            })
        
        # International cooperation
        if '國際合作' in main_content:
            qa_pairs.append({
                "question": "工研院有哪些國際合作？",
                "answer": "工研院的國際合作包括：與學研機構、國際企業、合作夥伴的合作，服務據點遍佈亞洲、美洲、歐洲、大洋洲等地。"
            })
        
        # News and publications
        if '新聞中心' in main_content:
            qa_pairs.append({
                "question": "工研院有哪些新聞和出版品？",
                "answer": "工研院的新聞和出版品包括：新聞室、最新新聞、澄清說明、活動訊息、電子報、工業技術研究院年報、工業技術研究院簡介、工業技術與資訊月刊等。"
            })
        
        return qa_pairs
    
    def save_comprehensive_data(self, data: Dict[str, Any], output_dir: str = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_direct_data"):
        """Save comprehensive data to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save metadata
        with open(os.path.join(output_dir, 'metadata.txt'), 'w', encoding='utf-8') as f:
            f.write("Direct ITRI Website Crawler Metadata\n")
            f.write("=" * 50 + "\n\n")
            for key, value in data['metadata'].items():
                f.write(f"{key}: {value}\n")
        
        # Save main page content
        with open(os.path.join(output_dir, 'main_page.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI Main Page Content\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Title: {data['main_page']['title']}\n")
            f.write(f"URL: {data['main_page']['url']}\n")
            f.write(f"Content Length: {len(data['main_page']['content'])} characters\n")
            f.write("\nFull Content:\n")
            f.write(data['main_page']['content'])
        
        # Save navigation
        with open(os.path.join(output_dir, 'navigation.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI Website Navigation\n")
            f.write("=" * 50 + "\n\n")
            for category, links in data['navigation']['categories'].items():
                f.write(f"\n## {category.replace('_', ' ').title()}\n")
                f.write("-" * 30 + "\n")
                for link in links:
                    f.write(f"- {link['text']}: {link['href']}\n")
        
        # Save content sections
        with open(os.path.join(output_dir, 'content_sections.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI Content Sections\n")
            f.write("=" * 50 + "\n\n")
            for section_name, content in data['content_sections'].items():
                f.write(f"\n## {section_name.replace('_', ' ').title()}\n")
                f.write("-" * 30 + "\n")
                for item in content:
                    f.write(f"- {item}\n")
        
        # Save technologies
        with open(os.path.join(output_dir, 'technologies.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI Technologies (Direct Crawl)\n")
            f.write("=" * 50 + "\n\n")
            for tech in data.get('technologies', []):
                f.write(f"\n## {tech['title']}\n")
                f.write("-" * 20 + "\n")
                f.write(f"Content: {tech['content']}\n")
        
        # Save news articles
        with open(os.path.join(output_dir, 'news_articles.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI News Articles (Direct Crawl)\n")
            f.write("=" * 50 + "\n\n")
            for news in data.get('news_articles', []):
                f.write(f"\n## {news['title']}\n")
                f.write("-" * 20 + "\n")
                f.write(f"Content: {news['content']}\n")
        
        # Save achievements
        with open(os.path.join(output_dir, 'achievements.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI Achievements (Direct Crawl)\n")
            f.write("=" * 50 + "\n\n")
            for achievement in data.get('achievements', []):
                f.write(f"\n## {achievement['title']}\n")
                f.write("-" * 20 + "\n")
                f.write(f"Content: {achievement['content']}\n")
        
        # Save organization info
        with open(os.path.join(output_dir, 'organization_info.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI Organization Information (Direct Crawl)\n")
            f.write("=" * 50 + "\n\n")
            org_info = data.get('organization_info', {})
            if org_info:
                f.write(f"Content: {org_info.get('content', '')}\n")
                f.write("\nSections:\n")
                for section in org_info.get('sections', []):
                    f.write(f"- {section}\n")
        
        # Save contact info
        with open(os.path.join(output_dir, 'contact_info.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI Contact Information (Direct Crawl)\n")
            f.write("=" * 50 + "\n\n")
            contact_info = data.get('contact_info', {})
            if contact_info:
                f.write(f"Content: {contact_info.get('content', '')}\n")
                f.write("\nSections:\n")
                for section in contact_info.get('sections', []):
                    f.write(f"- {section}\n")
        
        # Save comprehensive JSON
        with open(os.path.join(output_dir, 'comprehensive_data.json'), 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # Save Q&A pairs
        qa_pairs = self.create_qa_pairs(data)
        with open(os.path.join(output_dir, 'qa_pairs.json'), 'w', encoding='utf-8') as f:
            json.dump(qa_pairs, f, ensure_ascii=False, indent=2)
        
        # Save summary
        with open(os.path.join(output_dir, 'summary.txt'), 'w', encoding='utf-8') as f:
            f.write("Direct ITRI Website Crawl Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Source URL: {data['metadata']['source_url']}\n")
            f.write(f"Crawl Timestamp: {data['metadata']['crawl_timestamp']}\n")
            f.write(f"Organization: {data['metadata']['organization_name']}\n")
            f.write(f"Content Length: {len(data['main_page']['content'])} characters\n")
            f.write(f"Navigation Links: {len(data['navigation']['all_links'])}\n")
            f.write(f"Technologies Found: {len(data.get('technologies', []))}\n")
            f.write(f"News Articles: {len(data.get('news_articles', []))}\n")
            f.write(f"Achievements: {len(data.get('achievements', []))}\n")
            f.write(f"Q&A Pairs Created: {len(qa_pairs)}\n")
        
        print(f"Saved all data to: {output_dir}/")
        print("Files created:")
        print("- metadata.txt")
        print("- main_page.txt")
        print("- navigation.txt")
        print("- content_sections.txt")
        print("- technologies.txt")
        print("- news_articles.txt")
        print("- achievements.txt")
        print("- organization_info.txt")
        print("- contact_info.txt")
        print("- comprehensive_data.json")
        print("- qa_pairs.json")
        print("- summary.txt")
    
    def crawl(self, output_dir: str = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_direct_data"):
        """Main crawling method"""
        print("Starting Direct ITRI Website Crawler...")
        print("=" * 60)
        
        # Fetch main page
        html_content = self.fetch_main_page()
        
        if html_content:
            print("✓ Successfully fetched main page")
            
            # Extract content
            content = self.extract_main_content(html_content)
            print(f"✓ Extracted content: {len(content.get('all_text', ''))} characters")
            
            # Categorize content
            categories = self.categorize_content(content)
            print("✓ Categorized content")
            
            # Create comprehensive data
            data = self.create_comprehensive_data(content, categories)
            print("✓ Created comprehensive data structure")
            
            # Save to files
            self.save_comprehensive_data(data, output_dir)
            
            # Print summary
            print("\n" + "=" * 60)
            print("DIRECT CRAWL COMPLETED SUCCESSFULLY!")
            print("=" * 60)
            print(f"- Source: {data['metadata']['source_url']}")
            print(f"- Organization: {data['metadata']['organization_name']}")
            print(f"- Content length: {len(data['main_page']['content'])} characters")
            print(f"- Navigation links: {len(data['navigation']['all_links'])}")
            print(f"- Technologies found: {len(data.get('technologies', []))}")
            print(f"- News articles: {len(data.get('news_articles', []))}")
            print(f"- Achievements: {len(data.get('achievements', []))}")
            print(f"- Q&A pairs created: {len(self.create_qa_pairs(data))}")
            print(f"- Data saved to: {output_dir}/")
            
        else:
            print("✗ Failed to fetch main page")

def main():
    crawler = DirectITRICrawler()
    crawler.crawl()

if __name__ == "__main__":
    main() 