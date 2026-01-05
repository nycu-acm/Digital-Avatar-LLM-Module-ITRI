import os
import requests
import json
import re
import time
import concurrent.futures
from bs4 import BeautifulSoup

# 設置基本參數
BASE_URL_TEMPLATE = "https://livetour.istaging.com/f61aa0a8-c677-4232-901d-c1fda7ffb785?group=6e760cfc-cfa4-4b4f-b227-0ca674b18638&locale={}&index={}"
LOCALES = ["us", "zh-tw"]  # 英文和中文版本
MAX_SCENES = 10  # 最大場景數量，可以根據需要調整
DOWNLOAD_DIR = "LLM_Chat/itri_online_museum_docs/istaging_html_1"
OUTPUT_DIR = "LLM_Chat/itri_online_museum_docs/istaging_parsed_1"
TIMEOUT = 30  # 請求超時時間（秒）
MAX_RETRIES = 3  # 最大重試次數
CONCURRENT_DOWNLOADS = 5  # 並行下載數量

# 創建目錄
for directory in [DOWNLOAD_DIR, OUTPUT_DIR]:
    if not os.path.exists(directory):
        os.makedirs(directory)

def download_scene(scene_idx, locale):
    """下載指定索引和語言的場景 HTML"""
    url = BASE_URL_TEMPLATE.format(locale, scene_idx)
    html_file = os.path.join(DOWNLOAD_DIR, f"scene_{scene_idx}_{locale}.html")
    
    # 如果已經下載過，則跳過
    if os.path.exists(html_file):
        print(f"場景 {scene_idx} ({locale}) 已下載，跳過")
        return True
    
    print(f"正在下載場景 {scene_idx} ({locale}): {url}")
    
    # 嘗試下載，最多重試 MAX_RETRIES 次
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(url, timeout=TIMEOUT, verify=False)
            if response.status_code == 200:
                with open(html_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                print(f"場景 {scene_idx} ({locale}) 下載成功")
                return True
            else:
                print(f"場景 {scene_idx} ({locale}) 下載失敗，狀態碼: {response.status_code}，嘗試 {attempt+1}/{MAX_RETRIES}")
        except Exception as e:
            print(f"場景 {scene_idx} ({locale}) 下載出錯: {e}，嘗試 {attempt+1}/{MAX_RETRIES}")
        
        # 等待一段時間後重試
        time.sleep(2)
    
    print(f"場景 {scene_idx} ({locale}) 下載失敗，已達最大重試次數")
    return False

def parse_scene(scene_idx, locale):
    """解析指定索引和語言的場景 HTML"""
    html_file = os.path.join(DOWNLOAD_DIR, f"scene_{scene_idx}_{locale}.html")
    
    # 檢查文件是否存在
    if not os.path.exists(html_file):
        print(f"場景 {scene_idx} ({locale}) 的 HTML 文件不存在，無法解析")
        return False
    
    print(f"正在解析場景 {scene_idx} ({locale}) 的 HTML...")
    
    try:
        # 讀取 HTML 內容
        with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
            html_content = f.read()
        
        # 使用 BeautifulSoup 解析 HTML
        soup = BeautifulSoup(html_content, "html.parser")
        
        # 1. 提取頁面標題
        title = soup.title.text.strip() if soup.title else "無標題"
        print(f"場景 {scene_idx} ({locale}) 標題: {title}")
        
        # 2. 提取所有可能的展品信息
        info_elements = []
        
        # 2.1 查找隱藏的 div 元素
        hidden_div = soup.select_one("div[hidden]")
        if hidden_div:
            # 提取所有 section 元素
            sections = hidden_div.find_all("section")
            print(f"找到 {len(sections)} 個隱藏的 section 元素")
            
            for section_idx, section in enumerate(sections):
                # 提取標題和內容
                title_elem = section.find("h1")
                content_elem = section.find("h2")
                image_elem = section.find("img")
                
                title_text = title_elem.text.strip() if title_elem else ""
                content_text = content_elem.text.strip() if content_elem else ""
                image_url = image_elem.get("src") if image_elem else ""
                
                if title_text or content_text:
                    info_elements.append({
                        "type": "section",
                        "section_idx": section_idx,
                        "title": title_text,
                        "content": content_text,
                        "image_url": image_url
                    })
        else:
            # 2.2 如果沒有隱藏的 div，嘗試直接從頁面中提取內容
            print("未找到隱藏的 div，嘗試直接從頁面提取內容")
            
            # 嘗試提取標題和內容
            h1_elements = soup.find_all("h1")
            h2_elements = soup.find_all("h2")
            
            for idx, (h1, h2) in enumerate(zip(h1_elements, h2_elements) if len(h1_elements) == len(h2_elements) else []):
                title_text = h1.text.strip()
                content_text = h2.text.strip()
                
                if title_text or content_text:
                    info_elements.append({
                        "type": "h1_h2_pair",
                        "section_idx": idx,
                        "title": title_text,
                        "content": content_text
                    })
            
            # 如果 h1 和 h2 不成對，單獨處理
            if len(h1_elements) != len(h2_elements):
                for idx, h1 in enumerate(h1_elements):
                    title_text = h1.text.strip()
                    if title_text:
                        info_elements.append({
                            "type": "h1_only",
                            "section_idx": idx,
                            "title": title_text,
                            "content": ""
                        })
                
                for idx, h2 in enumerate(h2_elements):
                    content_text = h2.text.strip()
                    if content_text:
                        info_elements.append({
                            "type": "h2_only",
                            "section_idx": idx,
                            "title": "",
                            "content": content_text
                        })
        
        # 3. 提取 JavaScript 數據
        js_data = {}
        
        # 3.1 嘗試提取 window.__INITIAL_STATE__
        initial_state_pattern = re.compile(r'window\.__INITIAL_STATE__\s*=\s*({.*?});', re.DOTALL)
        initial_state_match = initial_state_pattern.search(html_content)
        if initial_state_match:
            js_data['initial_state'] = initial_state_match.group(1)
        
        # 3.2 嘗試提取 krpano 數據
        krpano_pattern = re.compile(r'embedpano\(({.*?})\);', re.DOTALL)
        krpano_match = krpano_pattern.search(html_content)
        if krpano_match:
            js_data['krpano'] = krpano_match.group(1)
        
        # 4. 保存提取的數據
        
        # 4.1 保存基本信息
        basic_info = {
            "title": title,
            "scene_index": scene_idx,
            "locale": locale,
            "url": BASE_URL_TEMPLATE.format(locale, scene_idx)
        }
        
        with open(os.path.join(OUTPUT_DIR, f"scene_{scene_idx}_{locale}_basic.json"), "w", encoding="utf-8") as f:
            json.dump(basic_info, f, ensure_ascii=False, indent=2)
        
        # 4.2 保存展品信息
        if info_elements:
            # 保存為 JSON 格式
            with open(os.path.join(OUTPUT_DIR, f"scene_{scene_idx}_{locale}_info.json"), "w", encoding="utf-8") as f:
                json.dump(info_elements, f, ensure_ascii=False, indent=2)
            
            # 保存為人類可讀的文本格式
            with open(os.path.join(OUTPUT_DIR, f"scene_{scene_idx}_{locale}_info.txt"), "w", encoding="utf-8") as f:
                for item in info_elements:
                    f.write(f"=== {item['title']} ===\n\n")
                    f.write(f"{item['content']}\n\n")
                    if item.get('image_url'):
                        f.write(f"圖片: {item['image_url']}\n\n")
                    f.write("-" * 80 + "\n\n")
        
        # 4.3 保存 JavaScript 數據
        if js_data:
            with open(os.path.join(OUTPUT_DIR, f"scene_{scene_idx}_{locale}_js_data.json"), "w", encoding="utf-8") as f:
                json.dump(js_data, f, ensure_ascii=False, indent=2)
        
        # 4.4 保存原始 HTML
        with open(os.path.join(OUTPUT_DIR, f"scene_{scene_idx}_{locale}_raw.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print(f"場景 {scene_idx} ({locale}) 解析完成，找到 {len(info_elements)} 個信息元素")
        return True
    
    except Exception as e:
        print(f"解析場景 {scene_idx} ({locale}) 時出錯: {e}")
        return False

def main():
    print(f"開始下載和解析新的 iStaging 虛擬導覽，最大場景數量: {MAX_SCENES}，語言: {', '.join(LOCALES)}")
    
    # 1. 並行下載所有場景 (從 idx=1 開始，包含多語言)
    print("\n=== 開始下載場景 HTML ===\n")
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_DOWNLOADS) as executor:
        futures = {}
        for scene_idx in range(1, MAX_SCENES + 1):
            for locale in LOCALES:
                futures[executor.submit(download_scene, scene_idx, locale)] = (scene_idx, locale)
        
        for future in concurrent.futures.as_completed(futures):
            scene_idx, locale = futures[future]
            try:
                success = future.result()
                if not success:
                    print(f"場景 {scene_idx} ({locale}) 下載失敗")
            except Exception as e:
                print(f"處理場景 {scene_idx} ({locale}) 時發生異常: {e}")
    
    # 2. 解析所有下載的場景 (從 idx=1 開始，包含多語言)
    print("\n=== 開始解析場景 HTML ===\n")
    for scene_idx in range(1, MAX_SCENES + 1):
        for locale in LOCALES:
            html_file = os.path.join(DOWNLOAD_DIR, f"scene_{scene_idx}_{locale}.html")
            if os.path.exists(html_file):
                parse_scene(scene_idx, locale)
    
    print("\n所有場景處理完成！")
    
    # 3. 合併所有提取的信息 (從 idx=1 開始，按語言分別合併)
    print("\n=== 合併所有提取的信息 ===\n")
    
    for locale in LOCALES:
        all_info_text = []
        all_info_json = []
        
        # 處理所有場景的 info.txt 文件
        for scene_idx in range(1, MAX_SCENES + 1):
            info_file = os.path.join(OUTPUT_DIR, f"scene_{scene_idx}_{locale}_info.txt")
            if not os.path.exists(info_file):
                continue
            
            print(f"合併場景 {scene_idx} ({locale}) 的信息...")
            
            # 讀取文本文件
            with open(info_file, "r", encoding="utf-8") as f:
                content = f.read()
                
                # 添加場景信息
                scene_header = f"\n\n{'='*80}\n場景 {scene_idx} ({locale})\n{'='*80}\n\n"
                all_info_text.append(scene_header + content)
            
            # 讀取 JSON 文件（如果存在）
            json_file = os.path.join(OUTPUT_DIR, f"scene_{scene_idx}_{locale}_info.json")
            if os.path.exists(json_file):
                with open(json_file, "r", encoding="utf-8") as f:
                    try:
                        info_json = json.load(f)
                        # 為每個項目添加場景索引和語言
                        for item in info_json:
                            item["scene_idx"] = scene_idx
                            item["locale"] = locale
                        all_info_json.extend(info_json)
                    except json.JSONDecodeError:
                        print(f"無法解析 JSON 文件: {json_file}")
        
        # 保存合併後的文本文件
        locale_suffix = "_en" if locale == "us" else "_zh"
        output_txt = os.path.join(OUTPUT_DIR, f"all_info{locale_suffix}.txt")
        with open(output_txt, "w", encoding="utf-8") as f:
            title = "工研院線上展示館資訊 (英文版)" if locale == "us" else "工研院線上展示館資訊 (中文版)"
            f.write(f"# {title}\n\n")
            f.write(f"本文件包含從工研院線上展示館虛擬導覽中提取的所有展品信息 ({locale})。\n\n")
            f.write("".join(all_info_text))
        
        # 保存合併後的 JSON 文件
        output_json = os.path.join(OUTPUT_DIR, f"all_info{locale_suffix}.json")
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(all_info_json, f, ensure_ascii=False, indent=2)
        
        print(f"處理完成！({locale})")
        print(f"合併後的文本文件: {output_txt}")
        print(f"合併後的 JSON 文件: {output_json}")

if __name__ == "__main__":
    # 忽略 SSL 警告
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    main() 