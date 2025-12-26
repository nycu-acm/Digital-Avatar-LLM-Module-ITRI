#!/bin/bash

# ==========================================
# ITRI Crawler Data Cleanup Script
# ==========================================
# 此腳本用於安全地清除 crawled_data 目錄中的所有文件
# 保留目錄結構，只刪除內容
# ==========================================

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 當前腳本目錄
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRAWLED_DATA_DIR="$SCRIPT_DIR/crawled_data"
ITRI_CRAWLER_DIR="$SCRIPT_DIR/itri_scrapy_crawler/crawled_data"

echo -e "${BLUE}🧹 ITRI Crawler Data Cleanup Script${NC}"
echo "=========================================="

# 檢查目錄是否存在
check_directory() {
    local dir="$1"
    if [ -d "$dir" ]; then
        echo -e "${GREEN}✅ 找到目錄: $dir${NC}"
        return 0
    else
        echo -e "${YELLOW}⚠️  目錄不存在: $dir${NC}"
        return 1
    fi
}

# 顯示目錄內容統計
show_directory_stats() {
    local dir="$1"
    if [ -d "$dir" ] && [ "$(ls -A "$dir" 2>/dev/null)" ]; then
        echo -e "${BLUE}📊 目錄內容統計: $(basename "$dir")${NC}"
        
        # 統計文件類型
        local log_count=$(find "$dir" -name "*.log" 2>/dev/null | wc -l)
        local json_count=$(find "$dir" -name "*.json" 2>/dev/null | wc -l)
        local dir_count=$(find "$dir" -maxdepth 1 -type d ! -path "$dir" 2>/dev/null | wc -l)
        local total_files=$(find "$dir" -type f 2>/dev/null | wc -l)
        local total_size=$(du -sh "$dir" 2>/dev/null | cut -f1)
        
        echo "  📁 子目錄數量: $dir_count"
        echo "  📄 總文件數量: $total_files"
        echo "  📋 日誌文件: $log_count"
        echo "  📊 JSON文件: $json_count" 
        echo "  💾 總大小: $total_size"
        echo ""
    else
        echo -e "${GREEN}✅ 目錄 $(basename "$dir") 已經是空的${NC}"
    fi
}

# 清除目錄內容
cleanup_directory() {
    local dir="$1"
    local dir_name=$(basename "$dir")
    
    if [ ! -d "$dir" ]; then
        echo -e "${YELLOW}⚠️  跳過不存在的目錄: $dir${NC}"
        return 0
    fi
    
    if [ ! "$(ls -A "$dir" 2>/dev/null)" ]; then
        echo -e "${GREEN}✅ 目錄 $dir_name 已經是空的${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}🗑️  正在清除目錄: $dir_name${NC}"
    
    # 使用 find 安全地刪除所有內容
    find "$dir" -mindepth 1 -delete 2>/dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 成功清除目錄: $dir_name${NC}"
    else
        echo -e "${RED}❌ 清除目錄失敗: $dir_name${NC}"
        return 1
    fi
}

# 主函數
main() {
    echo "正在檢查目錄..."
    echo ""
    
    # 檢查並顯示目錄狀態
    dirs_found=0
    
    if check_directory "$CRAWLED_DATA_DIR"; then
        show_directory_stats "$CRAWLED_DATA_DIR"
        dirs_found=$((dirs_found + 1))
    fi
    
    if check_directory "$ITRI_CRAWLER_DIR"; then
        show_directory_stats "$ITRI_CRAWLER_DIR"
        dirs_found=$((dirs_found + 1))
    fi
    
    if [ $dirs_found -eq 0 ]; then
        echo -e "${RED}❌ 未找到任何 crawled_data 目錄${NC}"
        exit 1
    fi
    
    # 確認提示
    echo -e "${YELLOW}⚠️  警告: 此操作將永久刪除所有爬取的數據！${NC}"
    echo -e "${RED}🚨 這包括所有 .log 文件、.json 文件和子目錄${NC}"
    echo ""
    read -p "確定要繼續嗎？(輸入 'yes' 確認): " confirmation
    
    if [ "$confirmation" != "yes" ]; then
        echo -e "${BLUE}ℹ️  操作已取消${NC}"
        exit 0
    fi
    
    echo ""
    echo -e "${BLUE}🚀 開始清除操作...${NC}"
    echo ""
    
    # 執行清除操作
    cleanup_success=true
    
    if [ -d "$CRAWLED_DATA_DIR" ]; then
        cleanup_directory "$CRAWLED_DATA_DIR" || cleanup_success=false
    fi
    
    if [ -d "$ITRI_CRAWLER_DIR" ]; then
        cleanup_directory "$ITRI_CRAWLER_DIR" || cleanup_success=false
    fi
    
    echo ""
    if [ "$cleanup_success" = true ]; then
        echo -e "${GREEN}🎉 所有數據已成功清除！${NC}"
        echo -e "${GREEN}✅ 爬蟲系統已準備好進行全新的爬取${NC}"
    else
        echo -e "${RED}⚠️  部分清除操作失敗，請檢查權限${NC}"
        exit 1
    fi
}

# 顯示使用說明
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "使用說明:"
    echo "  $0              # 交互式清除 (推薦)"
    echo "  $0 --force      # 強制清除 (無確認提示)"
    echo "  $0 --help       # 顯示此幫助信息"
    echo ""
    echo "目標目錄:"
    echo "  - $CRAWLED_DATA_DIR"
    echo "  - $ITRI_CRAWLER_DIR"
    exit 0
fi

# 強制模式
if [ "$1" = "--force" ]; then
    echo -e "${RED}🚨 強制模式: 跳過確認提示${NC}"
    confirmation="yes"
    
    dirs_found=0
    if check_directory "$CRAWLED_DATA_DIR"; then
        dirs_found=$((dirs_found + 1))
    fi
    if check_directory "$ITRI_CRAWLER_DIR"; then
        dirs_found=$((dirs_found + 1))
    fi
    
    if [ $dirs_found -eq 0 ]; then
        echo -e "${RED}❌ 未找到任何 crawled_data 目錄${NC}"
        exit 1
    fi
    
    cleanup_success=true
    if [ -d "$CRAWLED_DATA_DIR" ]; then
        cleanup_directory "$CRAWLED_DATA_DIR" || cleanup_success=false
    fi
    if [ -d "$ITRI_CRAWLER_DIR" ]; then
        cleanup_directory "$ITRI_CRAWLER_DIR" || cleanup_success=false
    fi
    
    if [ "$cleanup_success" = true ]; then
        echo -e "${GREEN}🎉 強制清除完成！${NC}"
    else
        echo -e "${RED}⚠️  強制清除失敗${NC}"
        exit 1
    fi
else
    # 交互模式
    main
fi












