#!/bin/bash
# 檢查 Git 歷史中是否有敏感資訊

echo "=========================================="
echo "🔍 檢查 Git 歷史中的敏感資訊"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

FOUND_ISSUES=0

# 檢查 1: 檢查歷史中是否有 credentials.json
echo "檢查 1: 歷史中的 credentials.json"
if git log --all --full-history --source -- "*credentials.json" 2>/dev/null | grep -q "credentials.json"; then
    echo -e "${RED}❌ 發現 credentials.json 在 Git 歷史中！${NC}"
    echo "   這是一個嚴重的安全風險！"
    echo ""
    echo "   受影響的提交："
    git log --all --full-history --source -- "*credentials.json" --oneline | head -5
    echo ""
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo -e "${GREEN}✅ 未發現 credentials.json 在歷史中${NC}"
fi
echo ""

# 檢查 2: 檢查歷史中是否有 .env
echo "檢查 2: 歷史中的 .env 檔案"
if git log --all --full-history --source -- ".env" 2>/dev/null | grep -q "\.env"; then
    echo -e "${RED}❌ 發現 .env 在 Git 歷史中！${NC}"
    echo "   這是一個嚴重的安全風險！"
    echo ""
    echo "   受影響的提交："
    git log --all --full-history --source -- ".env" --oneline | head -5
    echo ""
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo -e "${GREEN}✅ 未發現 .env 在歷史中${NC}"
fi
echo ""

# 檢查 3: 檢查歷史中是否有私鑰
echo "檢查 3: 歷史中的私鑰（private_key）"
if git log -p --all -S "private_key" 2>/dev/null | grep -q "private_key"; then
    echo -e "${RED}❌ 發現 private_key 在 Git 歷史中！${NC}"
    echo "   這是一個嚴重的安全風險！"
    echo ""
    echo "   受影響的提交（前 5 個）："
    git log -p --all -S "private_key" --oneline | head -5
    echo ""
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo -e "${GREEN}✅ 未發現 private_key 在歷史中${NC}"
fi
echo ""

# 檢查 4: 檢查歷史中是否有 client_secret
echo "檢查 4: 歷史中的 client_secret"
if git log -p --all -S "client_secret" 2>/dev/null | grep -q "client_secret"; then
    echo -e "${RED}❌ 發現 client_secret 在 Git 歷史中！${NC}"
    echo "   這是一個嚴重的安全風險！"
    echo ""
    echo "   受影響的提交（前 5 個）："
    git log -p --all -S "client_secret" --oneline | head -5
    echo ""
    FOUND_ISSUES=$((FOUND_ISSUES + 1))
else
    echo -e "${GREEN}✅ 未發現 client_secret 在歷史中${NC}"
fi
echo ""

# 檢查 5: 檢查所有提交中的敏感關鍵字
echo "檢查 5: 檢查所有提交中的敏感關鍵字"
SENSITIVE_KEYWORDS=("api_key" "secret" "password" "token" "credential")
FOUND_KEYWORDS=0

for keyword in "${SENSITIVE_KEYWORDS[@]}"; do
    if git log -p --all -S "$keyword" 2>/dev/null | grep -q "$keyword"; then
        echo -e "${YELLOW}⚠️  警告：發現 '$keyword' 在歷史中${NC}"
        FOUND_KEYWORDS=$((FOUND_KEYWORDS + 1))
    fi
done

if [ $FOUND_KEYWORDS -eq 0 ]; then
    echo -e "${GREEN}✅ 未發現明顯的敏感關鍵字${NC}"
else
    echo -e "${YELLOW}   發現 $FOUND_KEYWORDS 個敏感關鍵字${NC}"
    echo "   注意：這可能是誤報，請手動檢查"
fi
echo ""

# 檢查 6: 檢查是否有大檔案（可能包含二進制憑證）
echo "檢查 6: 檢查歷史中的大檔案（可能包含憑證）"
LARGE_FILES=$(git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {print substr($0,6)}' | sort -k2 -n -r | head -5)

if [ -n "$LARGE_FILES" ]; then
    echo -e "${YELLOW}⚠️  發現大檔案（前 5 個）：${NC}"
    echo "$LARGE_FILES" | while read line; do
        size=$(echo "$line" | awk '{print $2}')
        file=$(echo "$line" | awk '{print $3}')
        if [ "$size" -gt 1000 ]; then  # 大於 1KB
            echo "   - $file ($size bytes)"
        fi
    done
else
    echo -e "${GREEN}✅ 未發現異常大檔案${NC}"
fi
echo ""

# 總結
echo "=========================================="
if [ $FOUND_ISSUES -eq 0 ]; then
    echo -e "${GREEN}✅ Git 歷史檢查完成，未發現嚴重問題${NC}"
    echo ""
    echo "💡 建議："
    echo "   - 定期執行此檢查"
    echo "   - 如果發現問題，請參考 docs/SECURITY.md 中的修復指南"
    exit 0
else
    echo -e "${RED}❌ 發現 $FOUND_ISSUES 個嚴重安全問題！${NC}"
    echo ""
    echo "🚨 緊急行動建議："
    echo "   1. 立即更換所有受影響的憑證和密鑰"
    echo "   2. 參考 docs/SECURITY.md 中的修復指南"
    echo "   3. 考慮使用 git filter-branch 或 BFG 清理歷史"
    echo ""
    echo "📚 詳細修復指南："
    echo "   查看 docs/SECURITY.md 中的「如果已經意外提交了敏感資訊」章節"
    exit 1
fi

