#!/bin/bash
# 安全檢查腳本 - 檢查是否有敏感資訊可能被提交到 GitHub

echo "=========================================="
echo "🔒 安全檢查 - GitHub 提交前檢查"
echo "=========================================="
echo ""

# 顏色定義
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

ERRORS=0
WARNINGS=0

# 檢查 1: 是否有 credentials.json 被追蹤
echo "檢查 1: credentials.json 檔案"
if git ls-files | grep -q "credentials.json"; then
    echo -e "${RED}❌ 錯誤：credentials.json 被 Git 追蹤！${NC}"
    echo "   這是一個嚴重的安全風險！"
    echo "   請立即執行：git rm --cached credentials.json"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ credentials.json 未被追蹤${NC}"
fi
echo ""

# 檢查 2: 是否有 .env 檔案被追蹤
echo "檢查 2: .env 檔案"
if git ls-files | grep -q "^\.env$"; then
    echo -e "${RED}❌ 錯誤：.env 被 Git 追蹤！${NC}"
    echo "   這是一個嚴重的安全風險！"
    echo "   請立即執行：git rm --cached .env"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}✅ .env 未被追蹤${NC}"
fi
echo ""

# 檢查 3: 檢查即將提交的檔案中是否有敏感資訊
echo "檢查 3: 即將提交的檔案"
STAGED_FILES=$(git diff --cached --name-only 2>/dev/null)
if [ -n "$STAGED_FILES" ]; then
    echo "   檢查已暫存的檔案..."
    
    # 檢查是否有 credentials.json
    if echo "$STAGED_FILES" | grep -q "credentials.json"; then
        echo -e "${RED}❌ 錯誤：credentials.json 在暫存區！${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    
    # 檢查是否有 .env
    if echo "$STAGED_FILES" | grep -q "^\.env$"; then
        echo -e "${RED}❌ 錯誤：.env 在暫存區！${NC}"
        ERRORS=$((ERRORS + 1))
    fi
    
    # 檢查檔案內容中是否有私鑰
    for file in $STAGED_FILES; do
        if [ -f "$file" ]; then
            if grep -q "private_key\|client_secret\|api_key" "$file" 2>/dev/null; then
                echo -e "${YELLOW}⚠️  警告：$file 可能包含敏感資訊${NC}"
                WARNINGS=$((WARNINGS + 1))
            fi
        fi
    done
    
    if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✅ 暫存的檔案看起來安全${NC}"
    fi
else
    echo "   沒有已暫存的檔案"
fi
echo ""

# 檢查 4: 檢查 .gitignore 是否正確配置
echo "檢查 4: .gitignore 配置"
if grep -q "credentials.json" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ credentials.json 在 .gitignore 中${NC}"
else
    echo -e "${YELLOW}⚠️  警告：credentials.json 不在 .gitignore 中${NC}"
    WARNINGS=$((WARNINGS + 1))
fi

if grep -q "^\.env$" .gitignore 2>/dev/null; then
    echo -e "${GREEN}✅ .env 在 .gitignore 中${NC}"
else
    echo -e "${YELLOW}⚠️  警告：.env 不在 .gitignore 中${NC}"
    WARNINGS=$((WARNINGS + 1))
fi
echo ""

# 檢查 5: 檢查是否有硬編碼的敏感資訊
echo "檢查 5: 硬編碼的敏感資訊"
if git ls-files | xargs grep -l "private_key\|client_secret" 2>/dev/null | grep -v ".gitignore\|SECURITY.md"; then
    echo -e "${YELLOW}⚠️  警告：發現可能包含敏感資訊的檔案${NC}"
    git ls-files | xargs grep -l "private_key\|client_secret" 2>/dev/null | grep -v ".gitignore\|SECURITY.md" | while read file; do
        echo "   - $file"
    done
    WARNINGS=$((WARNINGS + 1))
else
    echo -e "${GREEN}✅ 未發現明顯的硬編碼敏感資訊${NC}"
fi
echo ""

# 總結
echo "=========================================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo -e "${GREEN}✅ 安全檢查通過！可以安全提交到 GitHub${NC}"
    exit 0
elif [ $ERRORS -eq 0 ]; then
    echo -e "${YELLOW}⚠️  有 $WARNINGS 個警告，請檢查${NC}"
    exit 0
else
    echo -e "${RED}❌ 發現 $ERRORS 個錯誤和 $WARNINGS 個警告！${NC}"
    echo "   請修復這些問題後再提交到 GitHub"
    exit 1
fi

