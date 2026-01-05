導入操作系統
來自playwright.sync_api導入sync_playwright
來自BS4進口美麗的小組
導入Urllib.Parse
從藏品進口Deque
進口時間
導入

＃ITRI SDGS的可配置的基本URL和域
base_url =“ https://itrisdgs.itri.org.tw/chi/index”
domain =“ itrisdgs.itri.org.tw”
max_pages = 1000
max_depth = 3
output_dir =“//mnt/hdd2/he110/linly-talker/llm_chat/itri_museum_docs/itri_sdgs_docs”
如果不是OS.PATH.EXISTS（output_dir）：
OS.Makedirs（output_dir）

visited_urls = set（）
url_queue = deque（[[（base_url，0）]）＃（url，depth）

DEF CLEAN_FILENAME（URL）：
“”“從URL創建一個乾淨的文件名”。
解析= urllib.parse.urlparse（url）
路徑=解析。
查詢= parsed.query.replace（'＆'，'_'）。替換（'='，' - '）如果解析

＃清理路徑以使其更可讀
路徑= re.sub（r'_+'，'_'，路徑）＃用單個替換多個下劃線
路徑= path.strip（'_'）＃刪除領先/尾隨下劃線

如果查詢：
返回f“ itri_sdgs_ {path} _ {query} .txt”
別的：
返回f“ itri_sdgs_ {path} .txt”

def extract_main_content（湯，URL）：
“”“從頁面中提取主要內容，處理ITRI SDGS特定結構”。
content_parts = []

＃嘗試查找特定於ITRI可持續發展目標的主要內容領域
main_selectors = [
'主要的'，
'＃主要的'，
'.main-content'，
'。內容'，
'＃內容'，
'文章'，
'。文章'，
'。 page-content'
這是給出的

main_content =無
對於main_selectors中的選擇器：
main_content = SOUP.SELECT_ONE（選擇器）
如果main_content：
休息

＃如果找不到主要內容，請嘗試身體
如果不是main_content：
main_content =湯

如果main_content：
＃提取文本內容
text = main_content.get_text（saparator =“ \ n”，strip = true）
content_parts.append（文本）

＃提取可能很重要的特定部分
部分= main_content.find_all（[['extions'，'div']，class_ = re.compile（r'（content | extifs | block | block | item）'））））））
對於各節中的部分：
section_text = section.get_text（saparator =“ \ n”，strip = true）
如果section_text and len（section_text）> 50：＃僅添加實質性內容
content_parts.append（f“ \ n ---- section ---- \ n {section_text}”）

＃還提取所有可能包含重要鏈接的列表或導航
nav_items = soup.find_all（['nav'，'ul'，'ol']）
對於NAV_ITEMS中的NAV：
nav_text = nav.get_text（saparator =“ \ n”，strip = true）
如果nav_text和len（nav_text）> 20：
content_parts.append（f“ \ n ---導航--- \ n {nav_text}”）

返回“ \ n \ n” .join（content_parts）

def is_valid_link（href，base_url）：
“”“檢查是否應遵循鏈接”
如果不是HREF：
返回false

＃跳過常見的非內心鏈接
skip_patterns = [
r'^javaScript：'，
r'^mailto：'，
r'^電話：'，
r'^＃'，
r'\。 pdf $'，
r'\。 doc $'，
r'\。 docx $'，
r'\。 xls $'，
r'\。 xlsx $'，
r'\。 zip $'，
r'\。 rar $'
這是給出的

對於skip_patterns中的模式：
如果Re.Search（模式，HREF，re.ignorecase）：
返回false

＃必須是同一域
嘗試：
full_url = urllib.parse.urljoin（base_url，href）
解析= urllib.parse.urlparse（full_url）
返回解析。 netloc==域
除了：
返回false

使用Sync_playwright（）作為p：
瀏覽器= P.Chromium.Launch（Headless = true）
page_count = 0

while url_queue和page_count <max_pages：
url，depth = url_queue.popleft（）

如果在visited_urls或depth中> max_depth中的URL：
繼續

print（f“ crawling（{page_count+1}/{max_pages}）：{url}在depth {depth}”）

嘗試：
page = browser.new_page（）

＃設置視口和用戶代理以提高兼容性
page.set_viewport_size（{“ width”：1920，“高度”：1080}）
page.set_extra_http_headers（{
“用戶代理”：“ Mozilla/5.0（Windows NT 10.0; Win64; X64）AppleWebkit/537.36（Khtml，像Gecko一樣）Chrome/91.0.4472.124 Safari/safari/537.36”
}））

＃導航到頁面
page.goto（url，wait_until =“ networkIdle”，超時= 30000）

＃等待加載的任何動態內容
page.wait_for_timeout（2000）

＃獲取HTML內容
html = pag.content（）
湯=美麗的套件（html，“ html.parser”）

＃提取主要內容
content = extract_main_content（湯，URL）

如果內容和len（content.strip（））> 50：＃僅在有大量內容的情況下保存
＃清潔內容
lines = [line.strip（）for content.splitlines（）中的行中的行
cleaned_content =“ \ n” .join（lines）

＃如果是錯誤頁面，請跳過
如果cleaned_content.startswith（“ 404”）或“ error”在cleaned_content.lower（）中：
打印（f“跳過錯誤頁面：{url}”）
page.close（）
visited_urls.add（url）
page_count += 1
繼續

＃創建文件名並保存
filename = clean_filename（url）
output_file = os.path.join（output_dir，文件名）

如果不是OS.PATH.EXISTS（output_file）：
使用open（output_file，“ w”，encoding =“ utf-8”）作為f：
f.write（f“ url：{url} \ n”）
f.write（f“ depth：{depth} \ n”）
f.write（f“爬行：{time.strftime（'％y-％m-％d％h：％m：％s'）} \ n”）
f.write（“ =” * 50 +“ \ n”）
F.Write（cleaned_content）
print（f“保存的內容為'{output_file}'（{len（cleaned_content）}字符）”）
別的：
打印（f“文件已經存在，跳過保存：{output_file}”）

＃查找新鏈接以添加到隊列
如果深度<max_depth：
links_found = 0
對於soup.find_all中的鏈接（'a'，href = true）：
href =鏈接['href']

如果IS_VALID_LINK（HREF，URL）：
full_url = urllib.parse.urljoin（url，href）
parsed_url = urllib.parse.urlparse（full_url）
norm_url = parsed_url._replace（fragment =“”）。 geturl（）

如果不在visited_urls中的norm_url和norm_url不在url_queue中的u [u [0]中：
url_queue.append（（norm_url，depth + 1））
links_found += 1
print（f“添加到隊列：{norm_url}在深度{depth + 1}”）

打印（f“找到{links_found}此頁面上的新鏈接”）

page.close（）
visited_urls.add（url）
page_count += 1

＃費率限制
時間。

除例外為E：
print（f“錯誤爬行{url}：{e}”）
繼續

browser.close（）
打印（f“爬行完整。訪問{page_count}頁。”）
print（f“找到的總唯一URL：{len（visited_urls）}”）