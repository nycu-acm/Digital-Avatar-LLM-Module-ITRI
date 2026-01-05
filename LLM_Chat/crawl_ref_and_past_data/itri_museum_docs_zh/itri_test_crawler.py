#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test ITRI Website Crawler
First tests if we can access the website, then tries different approaches
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import re
from datetime import datetime
from typing import Dict, Any, List
import time

class TestITRICrawler:
    def __init__(self):
        self.base_url = "https://www.itri.org.tw"
        self.session = requests.Session()
        
        # Try different user agents
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0'
        ]
        
    def test_connection(self) -> Dict[str, Any]:
        """Test basic connection to ITRI website"""
        results = {}
        
        print("Testing connection to ITRI website...")
        print("=" * 50)
        
        # Test 1: Basic GET request
        print("Test 1: Basic GET request")
        try:
            response = requests.get(self.base_url, timeout=30)
            results['basic_get'] = {
                'status_code': response.status_code,
                'content_length': len(response.text),
                'headers': dict(response.headers),
                'encoding': response.encoding
            }
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Content length: {len(response.text)} characters")
            print(f"✓ Encoding: {response.encoding}")
        except Exception as e:
            results['basic_get'] = {'error': str(e)}
            print(f"✗ Error: {e}")
        
        # Test 2: With session and headers
        print("\nTest 2: With session and headers")
        try:
            self.session.headers.update({
                'User-Agent': self.user_agents[0],
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
            response = self.session.get(self.base_url, timeout=30)
            results['session_get'] = {
                'status_code': response.status_code,
                'content_length': len(response.text),
                'headers': dict(response.headers),
                'encoding': response.encoding
            }
            print(f"✓ Status: {response.status_code}")
            print(f"✓ Content length: {len(response.text)} characters")
        except Exception as e:
            results['session_get'] = {'error': str(e)}
            print(f"✗ Error: {e}")
        
        # Test 3: Try different user agents
        print("\nTest 3: Different user agents")
        for i, user_agent in enumerate(self.user_agents):
            try:
                headers = {'User-Agent': user_agent}
                response = requests.get(self.base_url, headers=headers, timeout=30)
                results[f'user_agent_{i}'] = {
                    'status_code': response.status_code,
                    'content_length': len(response.text),
                    'user_agent': user_agent
                }
                print(f"✓ User Agent {i+1}: Status {response.status_code}, Length {len(response.text)}")
            except Exception as e:
                results[f'user_agent_{i}'] = {'error': str(e)}
                print(f"✗ User Agent {i+1}: Error {e}")
        
        # Test 4: Try specific pages
        print("\nTest 4: Specific pages")
        test_pages = [
            '/index.aspx',
            '/about.aspx',
            '/technology.aspx',
            '/news.aspx',
            '/contact.aspx',
            '/',
            '/index.html',
            '/index.htm'
        ]
        
        for page in test_pages:
            try:
                url = self.base_url + page
                response = self.session.get(url, timeout=30)
                results[f'page_{page.replace("/", "_").replace(".", "_")}'] = {
                    'status_code': response.status_code,
                    'content_length': len(response.text),
                    'url': url
                }
                print(f"✓ {page}: Status {response.status_code}, Length {len(response.text)}")
            except Exception as e:
                results[f'page_{page.replace("/", "_").replace(".", "_")}'] = {'error': str(e)}
                print(f"✗ {page}: Error {e}")
        
        return results
    
    def analyze_content(self, html_content: str) -> Dict[str, Any]:
        """Analyze the HTML content structure"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        analysis = {
            'title': soup.find('title').get_text(strip=True) if soup.find('title') else '',
            'meta_tags': [],
            'links': [],
            'images': [],
            'forms': [],
            'scripts': [],
            'styles': [],
            'text_content': '',
            'structure': {}
        }
        
        # Extract meta tags
        for meta in soup.find_all('meta'):
            analysis['meta_tags'].append({
                'name': meta.get('name', ''),
                'content': meta.get('content', ''),
                'property': meta.get('property', '')
            })
        
        # Extract links
        for link in soup.find_all('a', href=True):
            analysis['links'].append({
                'text': link.get_text(strip=True),
                'href': link.get('href', ''),
                'title': link.get('title', ''),
                'class': ' '.join(link.get('class', []))
            })
        
        # Extract images
        for img in soup.find_all('img'):
            analysis['images'].append({
                'src': img.get('src', ''),
                'alt': img.get('alt', ''),
                'title': img.get('title', '')
            })
        
        # Extract forms
        for form in soup.find_all('form'):
            analysis['forms'].append({
                'action': form.get('action', ''),
                'method': form.get('method', ''),
                'id': form.get('id', ''),
                'class': ' '.join(form.get('class', []))
            })
        
        # Extract scripts
        for script in soup.find_all('script'):
            analysis['scripts'].append({
                'src': script.get('src', ''),
                'type': script.get('type', ''),
                'content_length': len(script.get_text())
            })
        
        # Extract styles
        for style in soup.find_all('style'):
            analysis['styles'].append({
                'content_length': len(style.get_text())
            })
        
        # Extract text content
        analysis['text_content'] = soup.get_text(separator='\n', strip=True)
        
        # Analyze structure
        analysis['structure'] = {
            'headings': len(soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])),
            'paragraphs': len(soup.find_all('p')),
            'lists': len(soup.find_all(['ul', 'ol'])),
            'tables': len(soup.find_all('table')),
            'divs': len(soup.find_all('div')),
            'spans': len(soup.find_all('span'))
        }
        
        return analysis
    
    def extract_working_content(self, html_content: str) -> Dict[str, Any]:
        """Extract any working content from the HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove scripts and styles
        for script in soup(["script", "style"]):
            script.decompose()
        
        content = {
            'title': '',
            'main_text': '',
            'navigation': [],
            'footer': '',
            'forms': [],
            'links': []
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            content['title'] = title_tag.get_text(strip=True)
        
        # Extract main text content
        main_content = soup.get_text(separator='\n', strip=True)
        content['main_text'] = main_content
        
        # Extract navigation links
        nav_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            if text and href:
                nav_links.append({
                    'text': text,
                    'href': href,
                    'title': link.get('title', '')
                })
        content['links'] = nav_links
        
        # Extract forms
        forms = []
        for form in soup.find_all('form'):
            forms.append({
                'action': form.get('action', ''),
                'method': form.get('method', ''),
                'inputs': [{'name': inp.get('name', ''), 'type': inp.get('type', '')} 
                          for inp in form.find_all('input')]
            })
        content['forms'] = forms
        
        return content
    
    def save_test_results(self, test_results: Dict[str, Any], analysis: Dict[str, Any], 
                         content: Dict[str, Any], output_dir: str = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_test_data"):
        """Save test results to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Save test results
        with open(os.path.join(output_dir, 'test_results.json'), 'w', encoding='utf-8') as f:
            json.dump(test_results, f, ensure_ascii=False, indent=2)
        
        # Save analysis
        with open(os.path.join(output_dir, 'content_analysis.json'), 'w', encoding='utf-8') as f:
            json.dump(analysis, f, ensure_ascii=False, indent=2)
        
        # Save extracted content
        with open(os.path.join(output_dir, 'extracted_content.json'), 'w', encoding='utf-8') as f:
            json.dump(content, f, ensure_ascii=False, indent=2)
        
        # Save readable summary
        with open(os.path.join(output_dir, 'test_summary.txt'), 'w', encoding='utf-8') as f:
            f.write("ITRI Website Test Results\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Connection Tests:\n")
            f.write("-" * 20 + "\n")
            for test_name, result in test_results.items():
                f.write(f"{test_name}:\n")
                if 'error' in result:
                    f.write(f"  Error: {result['error']}\n")
                else:
                    f.write(f"  Status: {result.get('status_code', 'N/A')}\n")
                    f.write(f"  Content Length: {result.get('content_length', 'N/A')}\n")
                f.write("\n")
            
            f.write("Content Analysis:\n")
            f.write("-" * 20 + "\n")
            f.write(f"Title: {analysis.get('title', 'N/A')}\n")
            f.write(f"Meta Tags: {len(analysis.get('meta_tags', []))}\n")
            f.write(f"Links: {len(analysis.get('links', []))}\n")
            f.write(f"Images: {len(analysis.get('images', []))}\n")
            f.write(f"Forms: {len(analysis.get('forms', []))}\n")
            f.write(f"Scripts: {len(analysis.get('scripts', []))}\n")
            f.write(f"Text Content Length: {len(analysis.get('text_content', ''))}\n")
            
            f.write("\nStructure:\n")
            for key, value in analysis.get('structure', {}).items():
                f.write(f"  {key}: {value}\n")
        
        # Save extracted text content
        with open(os.path.join(output_dir, 'text_content.txt'), 'w', encoding='utf-8') as f:
            f.write("Extracted Text Content\n")
            f.write("=" * 50 + "\n\n")
            f.write(content.get('main_text', 'No content extracted'))
        
        # Save links
        with open(os.path.join(output_dir, 'links.txt'), 'w', encoding='utf-8') as f:
            f.write("Found Links\n")
            f.write("=" * 50 + "\n\n")
            for link in content.get('links', []):
                f.write(f"Text: {link.get('text', '')}\n")
                f.write(f"Href: {link.get('href', '')}\n")
                f.write(f"Title: {link.get('title', '')}\n")
                f.write("-" * 30 + "\n")
        
        print(f"Test results saved to: {output_dir}/")
        print("Files created:")
        print("- test_results.json")
        print("- content_analysis.json")
        print("- extracted_content.json")
        print("- test_summary.txt")
        print("- text_content.txt")
        print("- links.txt")
    
    def run_tests(self, output_dir: str = "/mnt/HDD2/he110/Linly-Talker/LLM_Chat/itri_museum_docs/itri_test_data"):
        """Run all tests"""
        print("Starting ITRI Website Tests...")
        print("=" * 60)
        
        # Run connection tests
        test_results = self.test_connection()
        
        # Get the best working response
        best_response = None
        best_content_length = 0
        
        for test_name, result in test_results.items():
            if 'error' not in result and result.get('status_code') == 200:
                content_length = result.get('content_length', 0)
                if content_length > best_content_length:
                    best_content_length = content_length
                    best_response = result
        
        if best_response:
            print(f"\n✓ Found working response with {best_content_length} characters")
            
            # Get the actual HTML content
            if 'session_get' in test_results and 'error' not in test_results['session_get']:
                response = self.session.get(self.base_url, timeout=30)
                html_content = response.text
            else:
                response = requests.get(self.base_url, timeout=30)
                html_content = response.text
            
            # Analyze content
            analysis = self.analyze_content(html_content)
            
            # Extract content
            content = self.extract_working_content(html_content)
            
            # Save results
            self.save_test_results(test_results, analysis, content, output_dir)
            
            print(f"\n✓ Content Analysis:")
            print(f"  - Title: {analysis.get('title', 'N/A')}")
            print(f"  - Links found: {len(analysis.get('links', []))}")
            print(f"  - Text content: {len(analysis.get('text_content', ''))} characters")
            print(f"  - Structure: {analysis.get('structure', {})}")
            
        else:
            print("\n✗ No working responses found")
            # Save test results anyway
            self.save_test_results(test_results, {}, {}, output_dir)

def main():
    crawler = TestITRICrawler()
    crawler.run_tests()

if __name__ == "__main__":
    main() 