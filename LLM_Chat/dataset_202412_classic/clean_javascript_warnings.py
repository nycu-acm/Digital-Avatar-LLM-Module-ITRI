#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
JavaScript Warning Cleaner for ITRI Crawled Data
================================================
清理已爬取數據中的 JavaScript 警告訊息
"""

import json
import re
import os
from pathlib import Path
from datetime import datetime

def clean_javascript_warnings(text):
    """Remove JavaScript warning messages from text"""
    if not text:
        return text
        
    # JavaScript warning and code patterns
    js_warning_patterns = [
        r'『您的瀏覽器不支援JavaScript功能，若網頁功能無法正常使用時，請開啟瀏覽器JavaScript狀態』\s*',
        r'Your browser does not support JavaScript.*?please enable JavaScript\s*',
        r'請開啟瀏覽器JavaScript功能.*?\s*',
        r'//\s*\(function\s*\([^)]*\)\s*\{.*?\}\)\s*\([^)]*\)\s*;?\s*',  # GTM JavaScript code
        r'function\s*\([^)]*\)\s*\{[^}]*gtm[^}]*\}',  # GTM function blocks
    ]
    
    cleaned_text = text
    for pattern in js_warning_patterns:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
    
    # Clean up excessive whitespace
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()
    
    return cleaned_text

def clean_json_file(file_path):
    """Clean JavaScript warnings from a JSON file"""
    print(f"🧹 清理文件: {file_path}")
    
    try:
        # Read the JSON file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            print(f"⚠️  跳過: {file_path} (不是數組格式)")
            return 0
        
        cleaned_count = 0
        
        # Clean each item
        for item in data:
            if isinstance(item, dict):
                # Clean content field
                if 'content' in item and item['content']:
                    original_content = item['content']
                    cleaned_content = clean_javascript_warnings(original_content)
                    if cleaned_content != original_content:
                        item['content'] = cleaned_content
                        cleaned_count += 1
                
                # Clean summary field
                if 'summary' in item and item['summary']:
                    original_summary = item['summary']
                    cleaned_summary = clean_javascript_warnings(original_summary)
                    if cleaned_summary != original_summary:
                        item['summary'] = cleaned_summary
                
                # Clean title field (less likely but just in case)
                if 'title' in item and item['title']:
                    original_title = item['title']
                    cleaned_title = clean_javascript_warnings(original_title)
                    if cleaned_title != original_title:
                        item['title'] = cleaned_title
        
        # Create backup
        backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.rename(file_path, backup_path)
        print(f"📦 備份已創建: {backup_path}")
        
        # Write cleaned data
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 已清理 {cleaned_count} 個項目")
        return cleaned_count
        
    except Exception as e:
        print(f"❌ 清理失敗: {e}")
        return 0

def main():
    """Main function"""
    print("🧹 JavaScript 警告清理工具")
    print("=" * 50)
    
    # Find all JSON files in crawled_data directories
    base_dir = Path(__file__).parent
    json_files = []
    
    # Search in main crawled_data
    crawled_data_dir = base_dir / "crawled_data"
    if crawled_data_dir.exists():
        json_files.extend(crawled_data_dir.rglob("*.json"))
    
    # Search in itri_scrapy_crawler/crawled_data
    itri_crawled_dir = base_dir / "itri_scrapy_crawler" / "crawled_data"
    if itri_crawled_dir.exists():
        json_files.extend(itri_crawled_dir.rglob("*.json"))
    
    if not json_files:
        print("📂 未找到任何 JSON 文件")
        return
    
    print(f"📁 找到 {len(json_files)} 個 JSON 文件")
    print()
    
    total_cleaned = 0
    
    for json_file in json_files:
        # Skip statistics files
        if 'statistics' in json_file.name.lower():
            print(f"⏭️  跳過統計文件: {json_file}")
            continue
            
        cleaned_count = clean_json_file(json_file)
        total_cleaned += cleaned_count
        print()
    
    print("=" * 50)
    print(f"🎉 清理完成！總共清理了 {total_cleaned} 個項目")
    print()
    print("💡 提示:")
    print("  - 原始文件已備份 (.backup_* 文件)")
    print("  - 新的爬取數據將自動清理 JavaScript 警告")
    print("  - 如需還原，請重命名備份文件")

if __name__ == "__main__":
    main()
