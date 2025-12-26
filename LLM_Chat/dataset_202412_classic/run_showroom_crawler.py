#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ITRI Virtual Showroom Crawler Runner
===================================
專門用於爬取工研院虛擬展示間的執行器
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime

def check_selenium_requirements():
    """檢查 Selenium 相關需求"""
    print("🔍 檢查 Selenium 環境...")
    
    try:
        import selenium
        from selenium import webdriver
        print(f"✅ Selenium 已安裝: {selenium.__version__}")
    except ImportError:
        print("❌ Selenium 未安裝")
        print("💡 安裝指令: pip install selenium")
        return False
    
    # 檢查 Chrome/Chromium
    try:
        from selenium.webdriver.chrome.options import Options
        chrome_options = Options()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=chrome_options)
        driver.quit()
        print("✅ Chrome WebDriver 可用")
        return True
        
    except Exception as e:
        print(f"⚠️  Chrome WebDriver 問題: {e}")
        print("💡 請確保已安裝 Chrome 瀏覽器和 chromedriver")
        print("💡 Ubuntu/Debian: sudo apt-get install chromium-browser chromium-chromedriver")
        print("💡 或下載 ChromeDriver: https://chromedriver.chromium.org/")
        return False

def setup_output_directory():
    """設置輸出目錄"""
    base_dir = Path(__file__).parent
    output_dir = base_dir / "crawled_data" / "showroom"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 創建時間戳目錄
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    session_dir = output_dir / f"crawl_{timestamp}"
    session_dir.mkdir(exist_ok=True)
    
    return session_dir

def run_showroom_crawler(mode='basic', timeout=None):
    """運行虛擬展示間爬蟲"""
    
    # 檢查環境
    if mode == 'full' and not check_selenium_requirements():
        print("⚠️  Selenium 環境不完整，切換到基礎模式")
        mode = 'basic'
    
    # 設置輸出目錄
    session_dir = setup_output_directory()
    
    # 切換到爬蟲目錄
    crawler_dir = Path(__file__).parent / "itri_scrapy_crawler"
    os.chdir(crawler_dir)
    
    # 準備爬取命令
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "itri_showroom",
        "-L", "INFO",
        "-o", f"{session_dir}/showroom_data.json",
    ]
    
    # 根據模式調整設置
    if mode == 'basic':
        cmd.extend([
            "-s", "DOWNLOAD_DELAY=2",
            "-s", "CONCURRENT_REQUESTS=2"
        ])
    elif mode == 'full':
        cmd.extend([
            "-s", "DOWNLOAD_DELAY=5",
            "-s", "CONCURRENT_REQUESTS=1"
        ])
    
    if timeout:
        cmd.extend(["-s", f"CLOSESPIDER_TIMEOUT={timeout}"])
    
    print("🚀 啟動 ITRI 虛擬展示間爬蟲")
    print("=" * 60)
    print(f"📂 工作目錄: {crawler_dir}")
    print(f"💾 輸出目錄: {session_dir}")
    print(f"🔧 爬取模式: {mode}")
    print(f"🔧 執行命令: {' '.join(cmd)}")
    print("=" * 60)
    
    # 執行爬蟲
    start_time = time.time()
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            universal_newlines=True
        )
        
        # 實時顯示輸出
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
        
        process.wait()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        if process.returncode == 0:
            print("✅ 虛擬展示間爬蟲完成！")
            
            # 檢查輸出文件
            output_file = session_dir / "showroom_data.json"
            if output_file.exists():
                file_size = output_file.stat().st_size
                print(f"📊 輸出文件: {output_file}")
                print(f"📏 文件大小: {file_size:,} bytes")
                
                # 簡單統計
                try:
                    import json
                    with open(output_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    if isinstance(data, list):
                        print(f"📈 爬取項目數: {len(data)}")
                        
                        # 統計內容類型
                        content_types = {}
                        for item in data:
                            ct = item.get('content_type', 'unknown')
                            content_types[ct] = content_types.get(ct, 0) + 1
                        
                        print("📋 內容類型分布:")
                        for ct, count in content_types.items():
                            print(f"   {ct}: {count}")
                            
                except Exception as e:
                    print(f"⚠️  無法解析輸出文件: {e}")
            
        else:
            print(f"❌ 爬蟲失敗，退出代碼: {process.returncode}")
        
        print(f"⏱️  執行時間: {duration:.1f} 秒")
        print("=" * 60)
        
        return process.returncode == 0, session_dir
        
    except KeyboardInterrupt:
        print("\n⚠️  用戶中斷爬取")
        process.terminate()
        process.wait()
        return False, session_dir
        
    except Exception as e:
        print(f"\n❌ 執行錯誤: {e}")
        return False, session_dir

def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='ITRI Virtual Showroom Crawler',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用範例:
  # 基礎爬取 (不使用 Selenium)
  python run_showroom_crawler.py --mode basic
  
  # 完整爬取 (使用 Selenium 處理 JavaScript)
  python run_showroom_crawler.py --mode full
  
  # 限時爬取
  python run_showroom_crawler.py --timeout 300
        """
    )
    
    parser.add_argument('--mode', 
                       choices=['basic', 'full'],
                       default='basic',
                       help='爬取模式 (basic: 基礎HTML, full: 包含JavaScript)')
    
    parser.add_argument('--timeout',
                       type=int,
                       help='爬取超時時間 (秒)')
    
    parser.add_argument('--check-env',
                       action='store_true',
                       help='僅檢查環境，不執行爬取')
    
    args = parser.parse_args()
    
    print("🏛️  ITRI 虛擬展示間爬蟲")
    print("=" * 40)
    
    if args.check_env:
        print("🔍 環境檢查模式")
        selenium_ok = check_selenium_requirements()
        if selenium_ok:
            print("✅ 環境檢查完成，可以使用完整模式")
        else:
            print("⚠️  建議使用基礎模式")
        return
    
    # 執行爬取
    success, output_dir = run_showroom_crawler(
        mode=args.mode,
        timeout=args.timeout
    )
    
    if success:
        print(f"\n🎉 爬取成功完成！")
        print(f"📁 數據保存在: {output_dir}")
        print(f"\n💡 後續步驟:")
        print(f"   1. 檢查數據: ls -la {output_dir}")
        print(f"   2. 查看內容: head -20 {output_dir}/showroom_data.json")
        print(f"   3. 分析數據: python analyze_showroom_data.py {output_dir}")
    else:
        print(f"\n❌ 爬取未成功完成")
        print(f"📁 部分數據可能保存在: {output_dir}")

if __name__ == "__main__":
    main()
