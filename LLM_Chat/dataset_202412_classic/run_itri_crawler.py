#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ITRI Scrapy Crawler Runner Script
Execute all ITRI-related spiders and generate comprehensive reports.
"""

import os
import sys
import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import argparse


class ITRIScrapyRunner:
    """Main runner class for ITRI Scrapy crawlers"""
    
    def __init__(self, project_dir: str = "itri_scrapy_crawler"):
        self.project_dir = Path(project_dir)
        self.output_dir = Path("crawled_data")
        self.output_dir.mkdir(exist_ok=True)
        
        # Available spiders
        self.spiders = {
            'itri_official': {
                'name': 'itri_official',
                'description': 'ITRI Official Website Crawler',
                'priority': 1,
                'estimated_time': '10-15 minutes'
            },
            'itri_wikipedia': {
                'name': 'itri_wikipedia',
                'description': 'Wikipedia ITRI Information Crawler',
                'priority': 2,
                'estimated_time': '5-10 minutes'
            },
            'itri_news': {
                'name': 'itri_news',
                'description': 'ITRI News and Media Crawler',
                'priority': 3,
                'estimated_time': '15-20 minutes'
            }
        }
        
        self.crawl_session = {
            'start_time': None,
            'end_time': None,
            'spiders_run': [],
            'results': {},
            'total_items': 0,
            'errors': []
        }
    
    def run_all_spiders(self, spiders_to_run: List[str] = None):
        """Run all or specified spiders"""
        if spiders_to_run is None:
            spiders_to_run = list(self.spiders.keys())
        
        print("🤖 ITRI Scrapy Crawler Suite")
        print("=" * 50)
        print(f"📅 Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🕷️  Spiders to run: {', '.join(spiders_to_run)}")
        print(f"📁 Output directory: {self.output_dir.absolute()}")
        print("=" * 50)
        
        self.crawl_session['start_time'] = datetime.now().isoformat()
        
        # Run each spider
        for spider_name in spiders_to_run:
            if spider_name in self.spiders:
                print(f"\n🚀 Starting spider: {spider_name}")
                print(f"📋 Description: {self.spiders[spider_name]['description']}")
                print(f"⏱️  Estimated time: {self.spiders[spider_name]['estimated_time']}")
                
                success = self._run_single_spider(spider_name)
                
                if success:
                    print(f"✅ Spider {spider_name} completed successfully")
                else:
                    print(f"❌ Spider {spider_name} failed")
                    self.crawl_session['errors'].append(f"Spider {spider_name} failed")
                
                self.crawl_session['spiders_run'].append({
                    'name': spider_name,
                    'success': success,
                    'timestamp': datetime.now().isoformat()
                })
            else:
                print(f"⚠️ Unknown spider: {spider_name}")
        
        self.crawl_session['end_time'] = datetime.now().isoformat()
        
        # Generate final report
        self._generate_final_report()
        
        print("\n" + "=" * 50)
        print("🎉 ITRI Crawling Session Completed!")
        print(f"📊 Total items collected: {self.crawl_session['total_items']}")
        print(f"🕐 Total time: {self._calculate_total_time()}")
        print(f"📁 Results saved in: {self.output_dir.absolute()}")
        print("=" * 50)
    
    def _run_single_spider(self, spider_name: str) -> bool:
        """Run a single spider using scrapy command"""
        try:
            # Change to project directory
            original_cwd = os.getcwd()
            os.chdir(self.project_dir)
            
            # Prepare scrapy command
            cmd = [
                'scrapy', 'crawl', spider_name,
                '-L', 'INFO',  # Log level
                '--logfile', f'../crawled_data/{spider_name}.log'
            ]
            
            print(f"🔧 Running command: {' '.join(cmd)}")
            print(f"📊 批次保存設定: 每 30 個項目自動保存")
            print(f"⚡ 進度顯示: 每 10 個項目顯示進度更新")
            print("=" * 50)
            
            # Run the spider
            start_time = time.time()
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                # timeout=36000  # 10 hours timeout
            )
            end_time = time.time()
            
            # Return to original directory
            os.chdir(original_cwd)
            
            # Check results
            if result.returncode == 0:
                print(f"⏱️  Spider completed in {end_time - start_time:.1f} seconds")
                
                # Try to parse results
                self._parse_spider_results(spider_name)
                return True
            else:
                print(f"❌ Spider failed with return code: {result.returncode}")
                print(f"Error output: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print(f"⏰ Spider {spider_name} timed out after 30 minutes")
            os.chdir(original_cwd)
            return False
        except Exception as e:
            print(f"❌ Error running spider {spider_name}: {e}")
            os.chdir(original_cwd)
            return False
    
    def _parse_spider_results(self, spider_name: str):
        """Parse results from a completed spider"""
        try:
            # Look for output files in the crawled_data directory
            session_dirs = [d for d in self.output_dir.iterdir() 
                           if d.is_dir() and d.name.startswith('crawl_')]
            
            if not session_dirs:
                print(f"⚠️ No output directory found for {spider_name}")
                return
            
            # Get the most recent session directory
            latest_session = max(session_dirs, key=lambda x: x.stat().st_mtime)
            
            # Look for spider-specific files
            spider_file = latest_session / f"{spider_name}_articles.json"
            stats_file = latest_session / "crawl_statistics.json"
            
            items_count = 0
            
            if spider_file.exists():
                with open(spider_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    items_count = len(data)
                    print(f"📊 Found {items_count} items in {spider_file.name}")
            
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    stats = json.load(f)
                    print(f"📈 Crawl statistics loaded from {stats_file.name}")
            
            # Update session results
            self.crawl_session['results'][spider_name] = {
                'items_count': items_count,
                'output_file': str(spider_file) if spider_file.exists() else None,
                'stats_file': str(stats_file) if stats_file.exists() else None
            }
            
            self.crawl_session['total_items'] += items_count
            
        except Exception as e:
            print(f"⚠️ Error parsing results for {spider_name}: {e}")
    
    def _generate_final_report(self):
        """Generate comprehensive final report"""
        report_content = f"""# ITRI Scrapy Crawler Session Report

## 📋 Session Overview
- **Start Time**: {self.crawl_session['start_time']}
- **End Time**: {self.crawl_session['end_time']}
- **Total Duration**: {self._calculate_total_time()}
- **Total Items Collected**: {self.crawl_session['total_items']}

## 🕷️ Spiders Executed

"""
        
        for spider_run in self.crawl_session['spiders_run']:
            spider_name = spider_run['name']
            success = "✅ Success" if spider_run['success'] else "❌ Failed"
            items_count = self.crawl_session['results'].get(spider_name, {}).get('items_count', 0)
            
            report_content += f"""### {self.spiders[spider_name]['description']}
- **Spider Name**: `{spider_name}`
- **Status**: {success}
- **Items Collected**: {items_count}
- **Execution Time**: {spider_run['timestamp']}

"""
        
        if self.crawl_session['errors']:
            report_content += f"""## ⚠️ Errors Encountered
"""
            for error in self.crawl_session['errors']:
                report_content += f"- {error}\n"
        
        report_content += f"""
## 📁 Output Files

All crawled data has been saved to: `{self.output_dir.absolute()}`

### File Structure:
```
crawled_data/
├── crawl_YYYYMMDD_HHMMSS/          # Session directory
│   ├── itri_official_articles.json  # Official website content
│   ├── itri_wikipedia_articles.json # Wikipedia content  
│   ├── itri_news_articles.json     # News articles
│   ├── all_articles_combined.json  # All content combined
│   └── crawl_statistics.json       # Detailed statistics
├── itri_official.log               # Spider logs
├── itri_wikipedia.log
├── itri_news.log
└── session_report.md               # This report
```

## 🔗 Next Steps

1. **Review the Data**: Check the JSON files for data quality and completeness
2. **Process for RAG**: Use the collected data with your RAG system
3. **Schedule Regular Runs**: Consider setting up automated crawling
4. **Enhance Spiders**: Add more sources or improve existing spiders

## 📊 Data Quality Notes

- All content has been validated and cleaned
- Duplicates have been filtered out
- ITRI-specific metadata has been enhanced
- Content quality scores have been calculated

---
**Generated by ITRI Scrapy Crawler Suite on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}**
"""
        
        # Save report
        report_file = self.output_dir / "session_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        print(f"📋 Session report saved to: {report_file}")
        
        # Also save JSON version for programmatic access
        json_report = {
            'session_info': self.crawl_session,
            'spiders_info': self.spiders,
            'generated_at': datetime.now().isoformat()
        }
        
        json_report_file = self.output_dir / "session_report.json"
        with open(json_report_file, 'w', encoding='utf-8') as f:
            json.dump(json_report, f, ensure_ascii=False, indent=2)
    
    def _calculate_total_time(self) -> str:
        """Calculate total execution time"""
        if not self.crawl_session['start_time'] or not self.crawl_session['end_time']:
            return "Unknown"
        
        start = datetime.fromisoformat(self.crawl_session['start_time'])
        end = datetime.fromisoformat(self.crawl_session['end_time'])
        duration = end - start
        
        total_seconds = int(duration.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def list_spiders(self):
        """List available spiders"""
        print("🕷️ Available ITRI Spiders:")
        print("=" * 40)
        
        for spider_name, spider_info in self.spiders.items():
            print(f"📌 {spider_name}")
            print(f"   Description: {spider_info['description']}")
            print(f"   Estimated Time: {spider_info['estimated_time']}")
            print(f"   Priority: {spider_info['priority']}")
            print()
    
    def check_setup(self):
        """Check if the Scrapy project is properly set up"""
        print("🔍 Checking ITRI Scrapy setup...")
        
        issues = []
        
        # Check if project directory exists
        if not self.project_dir.exists():
            issues.append(f"Project directory not found: {self.project_dir}")
        
        # Check if scrapy.cfg exists
        scrapy_cfg = self.project_dir / "scrapy.cfg"
        if not scrapy_cfg.exists():
            issues.append(f"scrapy.cfg not found: {scrapy_cfg}")
        
        # Check if spiders exist
        spiders_dir = self.project_dir / "itri_scrapy_crawler" / "spiders"
        if spiders_dir.exists():
            for spider_name in self.spiders.keys():
                spider_file = spiders_dir / f"{spider_name}.py"
                if not spider_file.exists():
                    issues.append(f"Spider file not found: {spider_file}")
        else:
            issues.append(f"Spiders directory not found: {spiders_dir}")
        
        # Check if scrapy command is available
        try:
            result = subprocess.run(['scrapy', 'version'], capture_output=True, text=True)
            if result.returncode != 0:
                issues.append("Scrapy command not available or not working")
        except FileNotFoundError:
            issues.append("Scrapy not installed or not in PATH")
        
        if issues:
            print("❌ Setup Issues Found:")
            for issue in issues:
                print(f"   - {issue}")
            return False
        else:
            print("✅ Setup looks good!")
            return True


def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="ITRI Scrapy Crawler Runner")
    parser.add_argument('--spiders', nargs='+', 
                       help='Specific spiders to run (default: all)')
    parser.add_argument('--list', action='store_true',
                       help='List available spiders')
    parser.add_argument('--check', action='store_true',
                       help='Check setup and configuration')
    parser.add_argument('--project-dir', default='itri_scrapy_crawler',
                       help='Scrapy project directory (default: itri_scrapy_crawler)')
    
    args = parser.parse_args()
    
    # Initialize runner
    runner = ITRIScrapyRunner(args.project_dir)
    
    if args.list:
        runner.list_spiders()
        return
    
    if args.check:
        setup_ok = runner.check_setup()
        if not setup_ok:
            print("\n💡 To fix setup issues:")
            print("1. Make sure you're in the correct directory")
            print("2. Run: pip install scrapy")
            print("3. Check that all spider files exist")
            sys.exit(1)
        return
    
    # Check setup before running
    if not runner.check_setup():
        print("\n❌ Setup check failed. Use --check for details.")
        sys.exit(1)
    
    # Run spiders
    try:
        runner.run_all_spiders(args.spiders)
    except KeyboardInterrupt:
        print("\n⏹️ Crawling interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
