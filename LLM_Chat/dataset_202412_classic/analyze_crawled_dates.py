#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ITRI Crawled Data Date Analysis
==============================
分析爬取數據的時間分布，幫助設定合適的時間過濾條件
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict, Counter
import argparse

def analyze_dates_in_file(file_path):
    """分析單個 JSON 文件中的日期分布"""
    print(f"📊 分析文件: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"❌ 無法讀取文件: {e}")
        return None
    
    if not isinstance(data, list):
        print(f"⚠️  文件格式不正確 (非數組)")
        return None
    
    # 統計數據
    stats = {
        'total_items': len(data),
        'items_with_published_date': 0,
        'items_with_crawled_date': 0,
        'published_dates': [],
        'crawled_dates': [],
        'date_patterns': Counter(),
        'content_types': Counter(),
        'date_extraction_success_rate': 0,
    }
    
    for item in data:
        # 檢查 published_date
        published_date = item.get('published_date', '').strip()
        if published_date:
            stats['items_with_published_date'] += 1
            stats['published_dates'].append(published_date)
            
            # 分析日期格式模式
            if re.match(r'^\d{4}-\d{2}-\d{2}$', published_date):
                stats['date_patterns']['YYYY-MM-DD'] += 1
            elif re.match(r'^\d{4}/\d{1,2}/\d{1,2}$', published_date):
                stats['date_patterns']['YYYY/M/D'] += 1
            elif re.match(r'^\d{4}年\d{1,2}月\d{1,2}日$', published_date):
                stats['date_patterns']['中文日期'] += 1
            else:
                stats['date_patterns']['其他格式'] += 1
        
        # 檢查 crawled_at
        crawled_at = item.get('crawled_at', '').strip()
        if crawled_at:
            stats['items_with_crawled_date'] += 1
            # 提取日期部分
            crawled_date = crawled_at.split('T')[0] if 'T' in crawled_at else crawled_at
            stats['crawled_dates'].append(crawled_date)
        
        # 統計內容類型
        content_type = item.get('content_type', 'unknown')
        stats['content_types'][content_type] += 1
    
    # 計算成功率
    if stats['total_items'] > 0:
        stats['date_extraction_success_rate'] = (stats['items_with_published_date'] / stats['total_items']) * 100
    
    return stats

def analyze_date_distribution(dates):
    """分析日期分布"""
    if not dates:
        return {}
    
    # 解析日期
    parsed_dates = []
    for date_str in dates:
        try:
            # 嘗試不同的日期格式
            for fmt in ['%Y-%m-%d', '%Y/%m/%d', '%Y年%m月%d日']:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    parsed_dates.append(dt)
                    break
                except ValueError:
                    continue
        except:
            continue
    
    if not parsed_dates:
        return {}
    
    # 統計分布
    parsed_dates.sort()
    
    # 按年份分組
    yearly_counts = defaultdict(int)
    monthly_counts = defaultdict(int)
    
    for dt in parsed_dates:
        yearly_counts[dt.year] += 1
        monthly_counts[f"{dt.year}-{dt.month:02d}"] += 1
    
    # 計算時間範圍
    min_date = parsed_dates[0]
    max_date = parsed_dates[-1]
    date_range = (max_date - min_date).days
    
    return {
        'count': len(parsed_dates),
        'min_date': min_date.strftime('%Y-%m-%d'),
        'max_date': max_date.strftime('%Y-%m-%d'),
        'date_range_days': date_range,
        'yearly_distribution': dict(yearly_counts),
        'monthly_distribution': dict(monthly_counts),
        'recent_30_days': len([dt for dt in parsed_dates if (datetime.now() - dt).days <= 30]),
        'recent_90_days': len([dt for dt in parsed_dates if (datetime.now() - dt).days <= 90]),
        'recent_365_days': len([dt for dt in parsed_dates if (datetime.now() - dt).days <= 365]),
    }

def print_analysis_report(stats, file_path):
    """打印分析報告"""
    print(f"\n📋 文件分析報告: {Path(file_path).name}")
    print("=" * 80)
    
    # 基本統計
    print(f"📊 基本統計:")
    print(f"   總項目數: {stats['total_items']:,}")
    print(f"   有發布日期: {stats['items_with_published_date']:,} ({stats['date_extraction_success_rate']:.1f}%)")
    print(f"   有爬取日期: {stats['items_with_crawled_date']:,}")
    
    # 內容類型分布
    print(f"\n📝 內容類型分布:")
    for content_type, count in stats['content_types'].most_common():
        percentage = (count / stats['total_items']) * 100
        print(f"   {content_type}: {count:,} ({percentage:.1f}%)")
    
    # 日期格式分析
    if stats['date_patterns']:
        print(f"\n📅 日期格式分布:")
        for pattern, count in stats['date_patterns'].most_common():
            percentage = (count / stats['items_with_published_date']) * 100 if stats['items_with_published_date'] > 0 else 0
            print(f"   {pattern}: {count:,} ({percentage:.1f}%)")
    
    # 發布日期分析
    if stats['published_dates']:
        print(f"\n🗓️  發布日期分析:")
        pub_analysis = analyze_date_distribution(stats['published_dates'])
        if pub_analysis:
            print(f"   日期範圍: {pub_analysis['min_date']} 到 {pub_analysis['max_date']}")
            print(f"   時間跨度: {pub_analysis['date_range_days']} 天")
            print(f"   最近30天: {pub_analysis['recent_30_days']:,} 項")
            print(f"   最近90天: {pub_analysis['recent_90_days']:,} 項")
            print(f"   最近1年: {pub_analysis['recent_365_days']:,} 項")
            
            # 年份分布
            if pub_analysis['yearly_distribution']:
                print(f"\n   年份分布:")
                for year in sorted(pub_analysis['yearly_distribution'].keys(), reverse=True):
                    count = pub_analysis['yearly_distribution'][year]
                    print(f"     {year}: {count:,} 項")
    
    # 爬取日期分析
    if stats['crawled_dates']:
        print(f"\n🕐 爬取日期分析:")
        crawl_analysis = analyze_date_distribution(stats['crawled_dates'])
        if crawl_analysis:
            print(f"   爬取範圍: {crawl_analysis['min_date']} 到 {crawl_analysis['max_date']}")
            print(f"   爬取跨度: {crawl_analysis['date_range_days']} 天")

def suggest_date_filters(stats):
    """建議合適的日期過濾條件"""
    print(f"\n💡 建議的時間過濾設定:")
    print("=" * 50)
    
    if stats['items_with_published_date'] == 0:
        print("⚠️  由於發布日期提取成功率為 0%，建議：")
        print("   1. 改進時間提取邏輯")
        print("   2. 使用爬取時間作為替代")
        print("   3. 暫時不使用時間過濾")
        return
    
    success_rate = stats['date_extraction_success_rate']
    
    if success_rate < 10:
        print(f"⚠️  發布日期提取成功率較低 ({success_rate:.1f}%)，建議：")
        print("   1. 先改進時間提取邏輯")
        print("   2. 謹慎使用時間過濾")
    elif success_rate < 50:
        print(f"🔶 發布日期提取成功率中等 ({success_rate:.1f}%)，建議：")
        print("   1. 可以使用寬鬆的時間過濾")
        print("   2. 考慮改進時間提取邏輯")
    else:
        print(f"✅ 發布日期提取成功率良好 ({success_rate:.1f}%)，可以安全使用時間過濾")
    
    # 分析發布日期分布並給出建議
    if stats['published_dates']:
        pub_analysis = analyze_date_distribution(stats['published_dates'])
        if pub_analysis:
            print(f"\n📅 根據數據分布的建議:")
            
            recent_30 = pub_analysis['recent_30_days']
            recent_90 = pub_analysis['recent_90_days']
            recent_365 = pub_analysis['recent_365_days']
            total = pub_analysis['count']
            
            if recent_30 > total * 0.5:
                print(f"   🔥 大部分內容都很新 (50%+ 在30天內)")
                print(f"      建議: --preset recent_only (最近2週)")
            elif recent_90 > total * 0.7:
                print(f"   📈 內容較新 (70%+ 在90天內)")
                print(f"      建議: --preset last_month 或 --preset last_3_months")
            elif recent_365 > total * 0.8:
                print(f"   📊 內容相對較新 (80%+ 在1年內)")
                print(f"      建議: --preset last_6_months 或 --preset this_year")
            else:
                print(f"   📚 內容跨度較大，包含較多歷史資料")
                print(f"      建議: --min-date {pub_analysis['max_date'][:4]}-01-01 (從今年開始)")
            
            print(f"\n🎯 具體命令建議:")
            print(f"   # 只爬取最近內容")
            print(f"   python run_itri_crawler_with_date_filter.py --preset recent_only")
            print(f"   ")
            print(f"   # 爬取最近3個月")
            print(f"   python run_itri_crawler_with_date_filter.py --preset last_3_months")
            print(f"   ")
            print(f"   # 自定義日期範圍")
            print(f"   python run_itri_crawler_with_date_filter.py --min-date 2024-01-01")

def main():
    """主函數"""
    parser = argparse.ArgumentParser(description='分析 ITRI 爬取數據的時間分布')
    parser.add_argument('--file', help='指定要分析的 JSON 文件路徑')
    parser.add_argument('--all', action='store_true', help='分析所有找到的 JSON 文件')
    
    args = parser.parse_args()
    
    print("🔍 ITRI 爬取數據時間分析工具")
    print("=" * 50)
    
    # 確定要分析的文件
    json_files = []
    
    if args.file:
        json_files = [Path(args.file)]
    else:
        # 自動查找 JSON 文件
        base_dir = Path(__file__).parent
        
        # 搜索 crawled_data 目錄
        crawled_data_dirs = [
            base_dir / "crawled_data",
            base_dir / "itri_scrapy_crawler" / "crawled_data"
        ]
        
        for crawled_dir in crawled_data_dirs:
            if crawled_dir.exists():
                json_files.extend(crawled_dir.rglob("*_articles.json"))
    
    if not json_files:
        print("❌ 未找到任何 JSON 數據文件")
        print("💡 請確保已經運行過爬蟲，或使用 --file 指定文件路徑")
        return
    
    print(f"📁 找到 {len(json_files)} 個數據文件")
    
    # 分析每個文件
    all_stats = []
    
    for json_file in json_files:
        if 'statistics' in json_file.name.lower():
            continue  # 跳過統計文件
            
        stats = analyze_dates_in_file(json_file)
        if stats:
            all_stats.append((json_file, stats))
            print_analysis_report(stats, json_file)
    
    # 如果有多個文件，提供綜合建議
    if len(all_stats) > 1:
        print(f"\n🎯 綜合分析建議:")
        print("=" * 50)
        
        total_items = sum(stats['total_items'] for _, stats in all_stats)
        total_with_dates = sum(stats['items_with_published_date'] for _, stats in all_stats)
        overall_success_rate = (total_with_dates / total_items * 100) if total_items > 0 else 0
        
        print(f"📊 總體統計:")
        print(f"   總項目數: {total_items:,}")
        print(f"   有發布日期: {total_with_dates:,} ({overall_success_rate:.1f}%)")
        
        # 使用最新文件的統計進行建議
        if all_stats:
            latest_file, latest_stats = max(all_stats, key=lambda x: x[0].stat().st_mtime)
            print(f"\n基於最新文件 ({latest_file.name}) 的建議:")
            suggest_date_filters(latest_stats)
    elif len(all_stats) == 1:
        suggest_date_filters(all_stats[0][1])

if __name__ == "__main__":
    main()












