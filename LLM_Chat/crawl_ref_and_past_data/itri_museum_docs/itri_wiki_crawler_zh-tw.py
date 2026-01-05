＃！ /usr/bin/env Python3
”“”
增強的Itri Wikipedia爬蟲
抓取ITRI Wikipedia頁面，並為博物館聊天機器人提取全面的結構化數據。
”“”

導入請求
來自BS4進口美麗的小組
進口JSON
導入
從DateTime Import DateTime
導入操作系統
從輸入導入dict，列表，任何可選的

班級增強了Itriwikicrawler：
def __init __（自我）：
self.base_url =“ https://zh.wikipedia.org/zh-tw/工業技術研究院”
self.session = requests.session（）
self.session.headers.update（{{
“用戶代理”：'Mozilla/5.0（Windows NT 10.0; Win64; X64）AppleWebkit/537.36（Khtml，像Gecko一樣）Chrome/91.0.4472.124 Safari/537.36'
}））

def fetch_page（self） - > str：
“”“獲取Itri Wikipedia頁面”
嘗試：
響應= self.session.get（self.base_url）
response.raise_for_status（）
返迴響應
除了請求。 requestException作為e：
打印（f“錯誤獲取頁面：{e}”）
沒有返回

def parse_content（self，html_content：str） - > dict [str，任何]：
”“”解析HTML含量並提取全面的結構化數據“”。
湯= beautifutsoup（html_content，'html.parser'）

＃找到主要內容區域
content_div = soup.find（'div'，{'id'：'mw-content-text'}）
如果不是content_div：
返回 {}

數據= {
'anchomenty_name'：'工業技術研究院（工業技術研究所）'，
“ English_name”：“工業技術研究所”，
'縮寫'：'itri'，
'crawled_at'：datetime.now（）。isoformat（），
'source_url'：self.base_url，
'部分'：{}，
“領導力”：{}，
“成就”：[]，
'agrommisty_trusture'：{}，
'key_facts'：{}，
“獎勵”：[]，
'notable_alumni'：[]，，
“ Research_areas”：[]，
“國際_offices”：[]，
“爭議”：[]
}

＃提取全面信息
self._extract_basic_info（湯，數據）
self._extract_sections_enhanced（content_div，數據）
self._extract_leadership_enhanced（湯，數據）
self._extract_achievements_enhanced（湯，數據）
self._extract_organization_structure_enhanced（湯，數據）
self._extract_awards_and_honors（湯，數據）
self._extract_notable_alumni（湯，數據）
self._extract_research_areas（湯，數據）
self._extract_international_offices（湯，數據）
self._extract_controversies（湯，數據）

返回數據

def _extract_basic_info（self，soup：beautifulsoup，數據：dict [str，任何]）：
“”“從Infobox中提取基本組織信息”。
infobox = soup.find（'table'，{'class'：'infobox'}）
如果Infobox：
行= infobox.find_all（'tr'）
對於行排成：
單元格= row.find_all（['td'，'th']）
如果Len（單元）> = 2：
鍵=單元格[0] .get_text（strip = true）
值=單元格[1] .get_text（strip = true）
如果鍵和值：
data ['key_facts'] [key] =值

def _extract_sections_enhanced（self，content_div：beautifulsoup，data：dict [str，any]）：
”“”“增強的截面提取具有更好的結構”
部分= {}
current_section =無
current_content = []
current_subsection =無
小節= {}

對於content_div.find_all中的元素（['h1'，'h2'，'h3'，'h4'，'p'，'ul'，'ol'，'ol'，'table']）：
如果['H1'，'H2'，'H3'，'H4']中的element.name：
＃保存上一節
如果current_section和current_content：
如果Current_subsection：
subsions [current_subsection] ='\ n'.join（current_content）
節[Current_Section] =小節
別的：
部分[Current_Section] ='\ n'.join（current_content）

＃開始新部分
current_section = element.get_text（strip = true）
current_content = []
current_subsection =無
小節= {}

＃檢查這是否是小節
如果['H3'，'H4']和Current_section中的element.name：
current_subsection = current_section

elif Current_section：
如果element.name =='表'：
＃提取表數據
table_data = self._extract_table_data（element）
如果table_data：
current_content.append（f“ f”表格數據：{json.dumps（table_data，suarsy_ascii = false）}'）
別的：
text = element.get_text（strip = true）
如果文字：
current_content.append（文本）

＃保存最後一部分
如果current_section和current_content：
如果Current_subsection：
subsions [current_subsection] ='\ n'.join（current_content）
節[Current_Section] =小節
別的：
部分[Current_Section] ='\ n'.join（current_content）

數據['章節'] =部分

def _extract_table_data（self，table：beautifulsoup） - > list [dict [str，str]]：
“”“從表中提取結構化數據”
table_data = []
行= table.find_all（'tr'）

對於行排成：
單元格= row.find_all（['td'，'th']）
如果Len（單元）> = 2：
row_data = {}
對於I，枚舉（細胞）中的細胞：
如果i == 0：
row_data ['key'] = cell.get_text（strip = true）
別的：
row_data ['value'] = cell.get_text（strip = true）
如果row_data：
table_data.append（row_data）

返回table_data

def _extract_leadership_enhanced（self，soup：beautifulsoup，數據：dict [str，any]）：
“”“增強的領導力提取”“”
領導= {}

＃尋找領導部門和表格
用於進入湯。 find_all（['h2'，'h3']）：
heading_text = heading.get_text（strip = true）
如果有任何（heading_text中的關鍵字for ['院長'，''''，'組織'，'管理']中的關鍵字）：）：
＃提取領導者名單
next_element = heading.find_next_sibling（）
如果next_element和next_element.name =='ul'：
領導者= []
對於li in next_element.find_all（'li'）：
Leader_text = li.get_text（strip = true）
如果Leader_text：
LINDERES.APPEND（LEDEND_TEXT）
領導力[heading_text] =領導者
elif next_element和next_element.name =='table'：
＃提取領導的表數據
table_data = self._extract_table_data（next_element）
如果table_data：
領導力[heading_text] = table_data

數據['領導'] =領導力

def _extract_achievements_enhanced（self，soup：beautifulsoup，數據：dict [str，any]）：
“”“增強的成就提取”“”
成就= []

＃尋找與成就相關的內容
對於湯中的元素。 find_all（['p'，'li']）：
text = element.get_text（strip = true）
如果有（'獎'，''''，'榮譽'，'專利'，'技術'，'創新'，'研發'，'突破''，'突破'，'突破''，'突破'，''，''，''，''，'突破']）中有任何（for Text in Text in Text in Text for Text for Text for Text in Text in Text in Text in Text in Text in Text in Text
成就append（文本）

＃還尋找特定的成就部分
用於進入湯。find_all（['h2'，'h3']）：
heading_text = heading.get_text（strip = true）
如果有任何（heading_text中的關鍵字for ['成就'，''''，'獎項'，'專利']中的關鍵字）：）：
next_element = heading.find_next_sibling（）
如果next_element和next_element.name =='ul'：
對於li in next_element.find_all（'li'）：
achievement_text = li.get_text（strip = true）
如果Achievement_Text：
Achievements.Append（Achievement_Text）

數據['成就'] =成就

def _extract_organization_structure_enhanced（self，soup：beautifulsoup，data：dict [str，any]）：
“”“增強的組織結構提取”“”
結構= {}

＃尋找組織部分
用於進入湯。 find_all（['h2'，'h3']）：
heading_text = heading.get_text（strip = true）
如果有任何（heading_text中的關鍵字for ['組織'，'''''，'中心'，'研究所'，'架構']的關鍵字中的關鍵字）：
＃提取組織結構
next_element = heading.find_next_sibling（）
如果next_element和next_element.name在['ul'，'ol']中：
部門= []
對於li in next_element.find_all（'li'）：
dept_text = li.get_text（strip = true）
如果dept_text：
部門Append（dept_text）
結構[heading_text] =部門
elif next_element和next_element.name =='table'：
＃提取組織結構的表數據
table_data = self._extract_table_data（next_element）
如果table_data：
結構[heading_text] = table_data

data ['agrommy_structure'] =結構

def _extract_awards_and_honors（self，soup：beautifulsoup，數據：dict [str，any]）：
“”“提取獎項和榮譽”“”
獎項= []

＃尋找獎項部分
用於進入湯。 find_all（['h2'，'h3']）：
heading_text = heading.get_text（strip = true）
如果有任何（heading_text中的關鍵字for ['獎'，''''，'殊榮'']中的關鍵字）：
next_element = heading.find_next_sibling（）
如果next_element和next_element.name =='ul'：
對於li in next_element.find_all（'li'）：
awad_text = li.get_text（strip = true）
如果award_text：
獎勵。

數據['獎項'] =獎項

def _extract_notable_alumni（self，soup：beautifulsoup，數據：dict [str，any]）：
“”“提取著名的校友信息”“”
校友= []

＃尋找校友部分
用於進入湯。 find_all（['h2'，'h3']）：
heading_text = heading.get_text（strip = true）
如果有任何（heading_text中的關鍵字for ['院友'，''''，'傑出'，'知名']中的關鍵字）：）：
next_element = heading.find_next_sibling（）
如果next_element和next_element.name =='ul'：
對於li in next_element.find_all（'li'）：
alumni_text = li.get_text（strip = true）
如果alumni_text：
alumni.Append（alumni_text）

data ['notable_alumni'] =校友

def _extract_research_areas（self，soup：beautifulsoup，數據：dict [str，any]）：
“”“提取研究領域和重點領域”“”
Research_areas = []

＃尋找與研究有關的內容
對於湯中的元素。 find_all（['p'，'li']）：
text = element.get_text（strip = true）
如果有任何（在['研發'，''''，'領域'，'產業'，'科技'']中的關鍵字中的文本中的關鍵字）：
Research_areas.Append（文本）

數據['Research_areas'] = Research_areas

def _extract_international_offices（self，湯：美麗的人，數據：dict [str，any]）：
“”“提取國際辦公室信息”“”
辦公室= []

＃尋找國際辦公室信息
對於湯中的元素。 find_all（['p'，'li']）：
text = element.get_text（strip = true）
如果有任何（在['美國'，''''，'日本'，'辦事處'，'海外'']中的關鍵字中的文本中的關鍵字）：
辦公室.append（文字）

數據['Internation_Offices'] =辦公室

def _extract_controversies（self，湯：美麗的人，數據：dict [str，任何]）：
“”“提取爭議信息”“”
爭議= []

＃尋找爭議的部分
用於進入湯。 find_all（['h2'，'h3']）：
heading_text = heading.get_text（strip = true）
如果有任何（heading_text中的關鍵字for ['爭議'，''''，'問題'']中的關鍵字）：
next_element = heading.find_next_sibling（）
如果next_element和next_element.name在['p'，'ul']中：
如果next_element.name =='ul'：
對於li in next_element.find_all（'li'）：
condroversy_text = li.get_text（strip = true）
如果condoversy_text：
爭議。
別的：
condroversy_text = next_element.get_text（strip = true）
如果condoversy_text：
爭議。

數據['爭議'] =爭議

def create_enhanced_qa_pairs(self, data: Dict[str, Any]) -> List[Dict[str, str]]:        """Create comprehensive Q&A pairs for the chatbot"""        qa_pairs = []                # Basic organization info        qa_pairs.extend([            {                "question": "什麼是工研院？",                "answer": f"工研院（{data['organization_name']}）是台灣最重要的產業技術研發機構，專注於產業技術研發與創新."            },            {                "question": "工研院的英文名稱是什麼？",                "answer": f"工研院的英文名稱是 {data['english_name']}，簡稱 ITRI."            },            {                "question": "工研院的主要任務是什麼？",                "answer": "工研院的主要任務包括：產業技術研發、技術移轉、人才培育、產業服務等，致力於提升台灣產業競爭力."            },            {                "question": "工研院成立於哪一年？",                "answer": "工研院成立於1973年，由時任經濟部長孫運璿推動成立."            },            {                "question": "工研院的總部在哪裡？",                "answer": "工研院的總部位於台灣新竹，並在美國、歐洲、日本設有辦事處."            }        ])                # Add section-based Q&A        if 'sections' in data:            for section_name, content in data['sections'].items():                if isinstance(content, dict):                    # Handle subsections                    for subsection_name, subsection_content in content.items():                        if '沿革' in subsection_name or '歷史' in subsection_name:                            qa_pairs.append({                                "question": f"工研院的{subsection_name}如何？",                                "answer": f"工研院的{subsection_name}：{subsection_content[:800]}..."                            })                else:                    # Handle main sections                    if '沿革' in section_name or '歷史' in section_name:                        qa_pairs.append({                            "question": "工研院的歷史沿革如何？",                            "answer": f"工研院的歷史沿革：{content[:800]}..."                        })                    elif '組織' in section_name:                        qa_pairs.append({                            "question": "工研院的組織架構如何？",                            "answer": f"工研院的組織架構：{content[:800]}..."                        })                    elif '榮譽' in section_name or '獎' in section_name:                        qa_pairs.append({                            "question": "工研院有哪些榮譽和獎項？",                            "answer": f"工研院的榮譽和獎項：{content[:800]}..."                        })                # Add leadership Q&A        if 'leadership' in data:            for position, leaders in data['leadership'].items():                if leaders:                    if isinstance(leaders, list):                        qa_pairs.append({                            "question": f"工研院的{position}有哪些？",                            "answer": f"工研院的{position}包括：{', '.join(leaders[:10])}"                        })                    elif isinstance(leaders, list) and len(leaders) > 0 and isinstance(leaders[0], dict):                        # Handle table data                        leader_names = [leader.get('value', '') for leader in leaders if leader.get('value')]                        if leader_names:                            qa_pairs.append({                                "question": f"工研院的{position}有哪些？",                                "answer": f"工研院的{position}包括：{', '.join(leader_names[:10])}"                            })                # Add achievements Q&A        if 'achievements' in data and data['achievements']:            qa_pairs.append({                "question": "工研院有哪些重要成就？",                "answer": f"工研院的重要成就包括：{'；'.join(data['achievements'][:10])}"            })                # Add awards Q&A        if 'awards' in data and data['awards']:            qa_pairs.append({                "question": "工研院獲得過哪些獎項？",                "answer": f"工研院獲得的重要獎項包括：{'；'.join(data['awards'][:10])}"            })                # Add alumni Q&A        if 'notable_alumni' in data and data['notable_alumni']:            qa_pairs.append({                "question": "工研院有哪些傑出院友？",

"answer": f"工研院的傑出院友包括：{'、'.join(data['notable_alumni'][:10])}"            })                # Add research areas Q&A        if 'research_areas' in data and data['research_areas']:            qa_pairs.append({                "question": "工研院主要從事哪些研究領域？",                "answer": f"工研院主要從事的研究領域包括：{'；'.join(data['research_areas'][:10])}"            })                # Add international presence Q&A        if 'international_offices' in data and data['international_offices']:            qa_pairs.append({                "question": "工研院在海外有哪些辦事處？",                "answer": f"工研院在海外設有辦事處，包括：{'；'.join(data['international_offices'][:5])}"            })                # Add controversies Q&A (if any)        if 'controversies' in data and data['controversies']:            qa_pairs.append({                "question": "工研院曾經發生過哪些爭議事件？",                "answer": f"工研院曾經發生過的爭議事件包括：{'；'.join(data['controversies'][:5])}"            })                return qa_pairs

def save_enhanced_data（self，數據：dict [str Any]，output_dir：str =“//mnt/hdd2/he110/linly-talker/llm_chat/itri_museum_docs/itri_museum_docs/itri_museum_museum_museum_docs_by_itri_itri_itri_wiki_wiki_crawler”）
“”“將增強的爬行數據保存到文件中”。
OS.Makedirs（output_dir，equent_ok = true）

＃保存原始數據
開放（OS.Path.join（output_dir，'itri_wiki_raw_data.json'），'w'，encoding ='utf-8'）as f：f：
json.dump（data，f，suse_ascii = false，縮進= 2）

＃保存增強的問答對
qa_pairs = self.create_enhanced_qa_pairs（數據）
開放（OS.PATH.JOIN（output_dir，'itri_qa_pairs.json'），'w'，編碼='utf-8'）as f：
json.dump（qa_pairs，f，suarsy_ascii = false，縮進= 2）

＃保存增強的結構化內容
structred_content = {
'anchomenty_info'：{
'name'：data.get（'anchoment_name'，''），
'English_name'：data.get（'English_name'，''），
'縮寫'：data.get（'縮寫'，''），
'描述'：'台灣最重要的產業技術研發機構，專注於產業技術研發與創新'
}，，
'key_facts'：data.get（'key_facts'，{}），
'部分'：data.get（'pection'，{}），，
'領導'：data.get（'領導'，{}），
“成就”：data.get（“成就”，[]），
'anchomenty_structure'：data.get（'agromomy_structure'，{}），，
“獎勵”：data.get（'Awards'，[]），
'notable_alumni'：data.get（'notable_alumni'，[]），，
'Research_areas'：data.get（'research_areas'，[]），，
'International_offices'：data.get（'International_offices'，[]），
“爭議”：data.get（“爭議”，​​[]）
}

開放（OS.Path.Join（output_dir，'itri_structured_data.json'），'w'，encoding ='utf-8'）as f：
json.dump（structred_content，f，suse_ascii = false，縮進= 2）

打印（f“增強的數據保存到{output_dir}/”）
打印（f“  - 原始數據：itri_wiki_raw_data.json”）
打印（f“  - 問答對：itri_qa_pairs.json”）
打印（f“  - 結構化數據：itri_structured_data.json”）
打印（f“  - 創建的總問答對：{len（qa_pairs）}”）
print（f“  - 提取的部分：{len（data.get（'sections'，{}））}”）
打印（f“  - 找到成就：{len（data.get（'achievement'，[]））}）
打印（f“  - 找到的獎項：{len（data.get（'awhards'，[]））}”）
打印（f“  - 著名校友：{len（data.get（'notable_alumni'，[]））}}）

def crawl（self，output_dir：str =“/mnt/hdd2/he110/linly-talker/llm_chat/itri_museum_docs/itri_museum_docs_by_itri_itri_itri_wiki_crawler”）：
“”“主要爬行方法”“”
打印（“啟動增強了Itri Wikipedia crawler ...”）

＃獲取頁面
html_content = self.fetch_page（）
如果不是html_content：
打印（“無法獲取Wikipedia頁面”）
沒有返回

＃解析內容
data = self.parse_content（html_content）
如果沒有數據：
打印（“無法解析頁面內容”）
沒有返回

＃保存增強的數據
self.save_enhanced_data（數據，output_dir）

打印（f“增強的爬行成功完成！”）
print（f“提取{len（data.get（'sections'，{}））} exotions”）
print（f“找到{len（data.get（'成就'，[]））}成就）
print（f“找到{len（data.get（'awards'，[]））}獎勵”）
print（f“找到{len（data.get（'notable_alumni'，[]））} newable校友”）
print（f“創建{len（self.create_enhanced_qa_pairs（data））} Q＆A對”））

返回數據

def main（）：
“”“運行增強攻擊者的主要功能”“”
crawler =增強的intriwikicrawler（）
data = crawler.crawl（）

如果數據：
打印（“ \ nenhanced爬行摘要：”）
打印（f“  - 組織：{data.get（'andurans_name'，'n/a'）}”）
print（f“  - 找到的部分找到：{len（data.get（'sections'，{}））}”）
打印（f“  - 領導職位：{len（data.get（'領導'，{}））}”）
打印（f“  - 成就：{len（data.get（'achievement'，[]）}）}）
打印（f“  - 獎勵：{len（data.get（'awad'，[]））}）
打印（f“  - 著名校友：{len（data.get（'notable_alumni'，[]））}}）
打印（f“  - 研究領域：{len（data.get（'research_areas'，[]））}）

如果__name__ ==“ __ -main __”：
主要的（）