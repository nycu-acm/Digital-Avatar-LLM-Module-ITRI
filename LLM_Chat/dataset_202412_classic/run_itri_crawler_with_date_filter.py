#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ITRI Crawler with Date Filtering
===============================
Enhanced crawler runner with publication date filtering capabilities
"""

import os
import sys
import subprocess
import time
import argparse
from datetime import datetime, timedelta
from pathlib import Path

def setup_date_filter_settings(min_date=None, max_date=None):
    """Setup date filtering in Scrapy settings"""
    settings_file = Path(__file__).parent / "itri_scrapy_crawler" / "itri_scrapy_crawler" / "settings.py"
    
    # Read current settings
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Remove existing date filter settings
    lines = content.split('\n')
    filtered_lines = []
    skip_next = False
    
    for line in lines:
        if 'DATE_FILTER_' in line:
            continue
        filtered_lines.append(line)
    
    # Add new date filter settings
    if min_date or max_date:
        filtered_lines.append('')
        filtered_lines.append('# Date filtering settings')
        if min_date:
            filtered_lines.append(f'DATE_FILTER_MIN = "{min_date}"')
        if max_date:
            filtered_lines.append(f'DATE_FILTER_MAX = "{max_date}"')
    
    # Write back to file
    with open(settings_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(filtered_lines))
    
    return min_date, max_date

def update_pipeline_order():
    """Update pipeline order to include DateFilterPipeline"""
    settings_file = Path(__file__).parent / "itri_scrapy_crawler" / "itri_scrapy_crawler" / "settings.py"
    
    # Read current settings
    with open(settings_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if DateFilterPipeline is already in ITEM_PIPELINES
    if 'DateFilterPipeline' not in content:
        # Find ITEM_PIPELINES section and add DateFilterPipeline
        lines = content.split('\n')
        in_pipelines = False
        updated_lines = []
        
        for line in lines:
            if line.strip().startswith('ITEM_PIPELINES'):
                in_pipelines = True
                updated_lines.append(line)
            elif in_pipelines and line.strip() == '}':
                # Add DateFilterPipeline before closing brace
                updated_lines.append('    "itri_scrapy_crawler.pipelines.DateFilterPipeline": 150,')
                updated_lines.append(line)
                in_pipelines = False
            else:
                updated_lines.append(line)
        
        # Write back to file
        with open(settings_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(updated_lines))

def get_date_presets():
    """Get common date range presets"""
    today = datetime.now()
    
    return {
        'last_week': (
            (today - timedelta(days=7)).strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d')
        ),
        'last_month': (
            (today - timedelta(days=30)).strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d')
        ),
        'last_3_months': (
            (today - timedelta(days=90)).strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d')
        ),
        'last_6_months': (
            (today - timedelta(days=180)).strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d')
        ),
        'last_year': (
            (today - timedelta(days=365)).strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d')
        ),
        'this_year': (
            f"{today.year}-01-01",
            today.strftime('%Y-%m-%d')
        ),
        'recent_only': (
            (today - timedelta(days=14)).strftime('%Y-%m-%d'),
            today.strftime('%Y-%m-%d')
        )
    }

def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='ITRI Crawler with Date Filtering',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Crawl only recent content (last 2 weeks)
  python run_itri_crawler_with_date_filter.py --preset recent_only
  
  # Crawl content from specific date range
  python run_itri_crawler_with_date_filter.py --min-date 2024-01-01 --max-date 2024-12-31
  
  # Crawl only content after a specific date
  python run_itri_crawler_with_date_filter.py --min-date 2024-06-01
  
  # Show available presets
  python run_itri_crawler_with_date_filter.py --list-presets
        """
    )
    
    parser.add_argument('--min-date', 
                       help='Minimum publication date (YYYY-MM-DD)')
    parser.add_argument('--max-date', 
                       help='Maximum publication date (YYYY-MM-DD)')
    parser.add_argument('--preset', 
                       choices=['last_week', 'last_month', 'last_3_months', 
                               'last_6_months', 'last_year', 'this_year', 'recent_only'],
                       help='Use predefined date range')
    parser.add_argument('--list-presets', 
                       action='store_true',
                       help='List available date presets')
    parser.add_argument('--no-date-filter', 
                       action='store_true',
                       help='Disable date filtering (crawl all content)')
    
    args = parser.parse_args()
    
    # List presets if requested
    if args.list_presets:
        print("📅 Available Date Presets:")
        print("=" * 50)
        presets = get_date_presets()
        for name, (min_date, max_date) in presets.items():
            print(f"  {name:<15} : {min_date} to {max_date}")
        return
    
    # Determine date range
    min_date = None
    max_date = None
    
    if args.preset:
        presets = get_date_presets()
        min_date, max_date = presets[args.preset]
        print(f"📅 Using preset '{args.preset}': {min_date} to {max_date}")
    elif args.min_date or args.max_date:
        min_date = args.min_date
        max_date = args.max_date
        print(f"📅 Custom date range: {min_date or 'unlimited'} to {max_date or 'unlimited'}")
    elif not args.no_date_filter:
        # Default to recent content only
        presets = get_date_presets()
        min_date, max_date = presets['last_3_months']
        print(f"📅 Default filter (last 3 months): {min_date} to {max_date}")
    else:
        print("📅 No date filtering - crawling all content")
    
    # Setup date filtering
    if min_date or max_date:
        print(f"⚙️  Setting up date filters...")
        setup_date_filter_settings(min_date, max_date)
        update_pipeline_order()
        print(f"✅ Date filters configured")
    
    # Change to crawler directory
    crawler_dir = Path(__file__).parent / "itri_scrapy_crawler"
    os.chdir(crawler_dir)
    
    # Prepare crawl command
    cmd = [
        sys.executable, "-m", "scrapy", "crawl", "itri_official",
        "-L", "INFO"
    ]
    
    print("🚀 Starting ITRI Crawler with Date Filtering")
    print("=" * 60)
    print(f"📂 Working directory: {crawler_dir}")
    print(f"🔧 Command: {' '.join(cmd)}")
    if min_date:
        print(f"📅 Minimum date: {min_date}")
    if max_date:
        print(f"📅 Maximum date: {max_date}")
    print("=" * 60)
    
    # Run the crawler
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
        
        # Stream output in real-time
        for line in iter(process.stdout.readline, ''):
            print(line.rstrip())
        
        process.wait()
        
        end_time = time.time()
        duration = end_time - start_time
        
        print("\n" + "=" * 60)
        if process.returncode == 0:
            print(f"✅ Crawler completed successfully!")
        else:
            print(f"❌ Crawler failed with exit code: {process.returncode}")
        
        print(f"⏱️  Total duration: {duration:.1f} seconds")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n⚠️  Crawler interrupted by user")
        process.terminate()
        process.wait()
    except Exception as e:
        print(f"\n❌ Error running crawler: {e}")

if __name__ == "__main__":
    main()












