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

def _extract_all_sections（self，content_div：beautifulsoup，數據：dict [str，any]）：
“”“提取所有部分及其內容“”
打印（“提取所有部分...”）

部分= {}
current_section =無
current_subsection =無
current_content = []
subsect_content = []

＃找到所有標題和內容
對於content_div.find_all（['h1'，'h2'，'h3'，'h4'，'h5'，'h5'，p'，p'，ul'，'ol'，'ol'，'table'，'div']）的元素）：
如果element.name在['h1'，'h2'，'h3'，'h4'，'h5']中
＃保存上一個小節
如果current_subsection和subsection_content：
如果Current_section不在各節中：
部分[Current_Section] = {}
elif isInstance（章節[Current_section]，str）：
＃如果需要，將字符串轉換為dict
部分[Current_Section] = {}
部分[Current_Section] [Current_SubSection] ='\ n'.join（subsextecon_content）

＃保存上一節
如果current_section和current_content而不是Current_subsection：
部分[Current_Section] ='\ n'.join（current_content）

heading_text = element.get_text（strip = true）

＃確定這是主要部分還是小節
如果['h1'，'h2']中的element.name：
＃主部分
current_section = heading_text
current_content = []
current_subsection =無
subsect_content = []
打印（f“找到主部分：{heading_text}”）
別的：
＃小節
current_subsection = heading_text
subsect_content = []
打印（f“找到的小節：{heading_text}”）

elif Current_section：
text = element.get_text（strip = true）
如果文字：
如果Current_subsection：
subsept_content.append（文本）
別的：
current_content.append（文本）

＃保存最後一節和小節
如果current_subsection和subsection_content：
如果Current_section不在各節中：
部分[Current_Section] = {}
elif isInstance（章節[Current_section]，str）：
＃如果需要，將字符串轉換為dict
部分[Current_Section] = {}
部分[Current_Section] [Current_SubSection] ='\ n'.join（subsextecon_content）
elif current_section和current_content：
部分[Current_Section] ='\ n'.join（current_content）

數據['章節'] =部分
print（f“提取{len（pections）}主要部分”）

def _extract_all_tables（self，content_div：beautifulsoup，數據：dict [str，any]）：
“”“及其數據提取所有表“”
打印（“提取所有表...”）

表= {}
table_count = 0

對於content_div.find_all（'table'）中的表格：
table_count += 1
table_data = []

行= table.find_all（'tr'）
對於行排成：
單元格= row.find_all（['td'，'th']）
如果細胞：
row_data = []
用於細胞中的細胞：
cell_text = cell.get_text（strip = true）
如果cell_text：
row_data.append（cell_text）
如果row_data：
table_data.append（row_data）

如果table_data：
表[f“ table_ {table_count}”] = {
“行”：table_data，
'row_count'：len（table_data），
'column_count'：max（len（len for table_data中的行））如果table_data else 0
}

數據['表'] =表
打印（f“提取{len（tables）}表”）

def _extract_all_lists（self，content_div：beautifulsoup，數據：dict [str，any]）：
“”“提取所有列表（ul，ol）”“”
打印（“提取所有列表...”）

lists = {}
list_count = 0

對於content_div.find_all（['ul'，'ol']）中的list_element：
list_count += 1
List_items = []

對於LIST_ELEMENT.FIND_ALL（'li'）中的li：
item_text = li.get_text（strip = true）
如果item_text：
list_items.append（item_text）

如果List_items：
lists [f“ list_ {list_count}”] = {
'type'：list_element.name，
“項目”：list_items，
'item_count'：len（list_items）
}

數據['lists'] =列表
打印（f“提取{len（lists）}列表”）

def _extract_references_and_links（self，soup：beautifulsoup，數據：dict [str，any]）：
“”“提取引用和外部鏈接”“”
打印（“提取引用和外部鏈接...”）

＃查找參考部分
用於進入湯。find_all（['h2'，'h3'，'h4']）：
heading_text = heading.get_text（strip = true）
如果在heading_text或'heading_text中的'參考''中：
next_element = heading.find_next_sibling（）
如果next_element和next_element.name在['ul'，'ol']中：
對於li in next_element.find_all（'li'）：
ref_text = li.get_text（strip = true）
如果ref_text：
data ['references']。附錄（ref_text）

heading_text中的elif'外部連結'：
next_element = heading.find_next_sibling（）
如果next_element和next_element.name在['ul'，'ol']中：
對於li in next_element.find_all（'li'）：
link_text = li.get_text（strip = true）
如果link_text：
data ['external_links']。附錄（link_text）

print（f“提取{len（data ['references']）}引用”）
print（f“提取{len（data ['external_links']）}外部鏈接”）

def _extract_categories（self，湯：美麗的人，數據：dict [str，任何]）：
“”“提取頁類別”“”
打印（“提取類別...”）

category_div = soup.find（'div'，{'id'：'MW-Normal-catlinks'}）
如果category_div：
對於類別中的鏈接_div.find_all（'a'）：
category_text = link.get_text（strip = true）
如果category_text和category_text！='隱藏分類'：
data ['cantories']。附錄（category_text）

print（f“提取{len（data ['actories']）}類別”）

def _extract_raw_text（self，content_div：beautifulsoup，數據：dict [str，any]）：
“”“提取原始文本內容”“”
打印（“提取原始文本內容...”）

＃刪除腳本和样式元素
對於content_div中的腳本（[“腳本”，“樣式”]）：
script.decompose（）

＃獲取所有文字
raw_text = content_div.get_text（）
＃清理空格
raw_text = re.sub（r'\ s+'，''，raw_text）.strip（）

data ['raw_text'] = raw_text
print（f“提取{len（raw_text）}原始文本的字符”）

def save_as_text_files（self，數據：dict [str，任何]，輸出_dir：str =“/mnt/hdd2/he110/linly-tally-talker/llm_chat/itri_museum_docs/itri_comcompreregend_data”）打印（f“將數據保存到{output_dir}/”）＃與Open（OS.Path.Join（outpation_dir，'metadata.txt'），'W'），'W'，編碼='utf-8'）作為f：f.write（“＃itri wikipedia wikipedia crawler metadata \ n \ n”）的鍵' f.write（f“ {key}：{value} \ n”）＃如果數據['infobox_data']保存Infobox數據，請使用Open（OS.Path.Join（output_dir，'Infobox.txt'），'w'），'w'），'w'，encoding ='utf-8'）作為f：f.write（ data ['infobox_data']。項目（）：f.write（f“ {key}：{value} \ n”）＃保存pection_name的部分，data ['sections']的內容。項目（safe_name = re.name = re.sub = re.sub（r'[r'[^^\ w \ w \ s-]'，''，''，''，''''''''''''''''''''''''''''' str）：開放（OS.Path.join（output_dir，f'Section_ {safe_name} .txt'），'w'，encoding ='utf-8'）as f：f.write（f“＃{process_name} \ name} \ n \ n \ n \ n”） f'Section_ {safe_name} .txt'），'w'，編碼='utf-8'）作為f：f.write（f“＃{extact_name} \ n \ n \ n”），subsection_name，subsection_content in content.items in content.items（）： f.write（subsect_content）f.write（“ \ n \ n”）＃如果數據['tables']保存表，請在打開（OS.Path.join（output_dir，'tables.txt'），'w'，'w'，encoding ='utf-8'）中作為f：f.write（f.write（ data ['table']。項目（）：f.write（f“ ## {table_name} \ n”）f.write（f“ rows：{table_data ['row_count']}，列：{table_data [table_data ['column_count_count'} “。 data ['lists']。項目（）：f.write（f“ ## {list_name}（{list_data ['type'type'}）\ n“）f.write（f” items：{list_data ['item_count'} \ n \ n“} \ n \ n”）用於list_data ['''''''） f.write（“ \ n”）＃保存引用，如果數據['引用']：使用Open（OS.Path.join（output_dir，'revure.txt'），'w'，ododing ='utf-8'）as f：f.write（“＃itri wikipedia comeences fore） f.write（f“ {i}。枚舉（data ['external_links']，1）：f.write（f“ {i}。{link}。 Categories\n\n")                for category in data['categories']:                    f.write(f"- {category}\n")                # Save raw text        with open(os.path.join(output_dir, 'raw_text.txt'), 'w', encoding='utf-8') as f:            f.write("# ITRI Wikipedia Raw Text\n\n")

f.write（data ['raw_text']）＃與open（os.path.join（output_dir，'commistion_data.json'），'w'），'w'，encoding ='utf-8'）作為f：json.dump（data，data，f，suars_ascii = false，intent = 2）uspect.jojo Jojo Jojo Jojo Joso（off：json.dump） 'summary.txt'），'w'，編碼='utf-8'）作為f：f.write（“＃itri wikipedia crawler摘要摘要\ n \ n”）f.write（f“ agristance：{data [data ['metadata'n''grancy_name'] ['anchance_name'] ['andybor_name']}} \ n”） {data ['metadata'] ['crawled_at']} \ n”）f.write（f“ source url：{data [data ['metadata'] ['source_url']} \ n \ n \ n”） {data ['metadata']] ['total_content_length']}字符\ n”）f.write（f“ infobox項目：{len（data ['infobox_data']）} \ n”） {len（data ['lists']）} \ n“）f.write（f”引用：{len（data [data ['references']）} \ n“”）f.write（f“外部鏈接：{len（data [data ['external_links''external_links']}} \ n”） f.Write（“ ##章節名稱：\ n”）for data ['sections']。keys（）：f.write（f“  -  {extife_name} \ n”）print（“成功保存成功！”）print（在{uppute_dir}/fiens中創建的所有數據）print（f. _*。

def crawl（self，output_dir：str =“/mnt/hdd2/he110/linly-talker/llm_chat/itri_museum_docs/itri_comprehand_data”）：
“”“主要爬行方法”“”
打印（“開始綜合itri wikipedia crawler ...”）
打印（“ =” * 50）

＃獲取頁面
html_content = self.fetch_page（）
如果不是html_content：
打印（“無法獲取Wikipedia頁面”）
沒有返回

＃提取所有內容
data = self.extract_all_content（html_content）
如果沒有數據：
打印（“未能從頁面中提取內容”）
沒有返回

＃將所有數據保存為文本文件
self.save_as_text_files（數據，output_dir）

打印（“ \ n” +“ =” * 50）
打印（“爬行成功完成！”）
打印（f“組織：{data ['metadata'] ['anchoment_name']}”）
打印（f“提取的總截面：{data ['metadata'] ['total_sections']}”）
打印（f“總內容長度：{data ['metadata'] ['total_content_length']}字符”）
打印（f“ infobox項目：{len（data ['infobox_data']）}”）
打印（f“提取表：{len（data ['tables']）}”）
打印（f“提取的列表：{len（data ['lists']）}”）
print（f“參考：{len（data ['references']）}”）
print（f“外部鏈接：{len（data ['external_links']）}”）
print（f“類別：{len（data ['actories']）}”）

返回數據

def main（）：
“”“運行綜合軌道”的主要功能“”
crawler = itricmercrehensivecrawler（）
data = crawler.crawl（）

如果數據：
打印（“ \ ncrawling摘要：”）
打印（f“  - 組織：{data ['metadata'] ['anchoment_name']}”）
打印（f“  - 找到：{data ['metadata'] ['total_sections']}”）
打印（f“  - 內容長度：{data ['metadata'] ['total_content_length']}字符”）
打印（f“  - 數據保存到：/mnt/hdd2/he110/linly-talker/llm_chat/itri_museum_docs/itri_comprehand_data/”）

如果__name__ ==“ __ -main __”：
主要的（）