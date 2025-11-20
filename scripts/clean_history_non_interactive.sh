#!/bin/bash
# 非互動式清理 Git 歷史（用於自動化）
# 警告：此腳本會自動處理，請謹慎使用

set -e  # 遇到錯誤立即退出

PROJECT_ROOT=$(git rev-parse --show-toplevel)
cd "$PROJECT_ROOT"

echo "=========================================="
echo "🔧 清理 Git 歷史中的敏感資訊"
echo "=========================================="
echo ""

# 檢查是否有未暫存的變更
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  發現未暫存的變更，先提交..."
    git add -A
    git commit -m "chore: 清理敏感資訊前的變更" || true
fi

# 設置環境變數
export FILTER_BRANCH_SQUELCH_WARNING=1

# 清理 credentials.json
if git log --all --full-history --source -- "*credentials.json" 2>/dev/null | grep -q "credentials.json"; then
    echo "刪除 credentials.json..."
    git filter-branch --force --index-filter \
        "git rm --cached --ignore-unmatch credentials.json" \
        --prune-empty --tag-name-filter cat -- --all || true
fi

# 清理 .env
if git log --all --full-history --source -- ".env" 2>/dev/null | grep -q "\.env"; then
    echo "刪除 .env..."
    git filter-branch --force --index-filter \
        "git rm --cached --ignore-unmatch .env" \
        --prune-empty --tag-name-filter cat -- --all || true
fi

# 清理 refs
echo "清理 refs..."
git for-each-ref --format="%(refname)" refs/original/ | xargs -n 1 git update-ref -d 2>/dev/null || true

# 清理 reflog
echo "清理 reflog..."
git reflog expire --expire=now --all || true

# 清理和壓縮
echo "壓縮倉庫..."
git gc --prune=now --aggressive || true

echo ""
echo "✅ 清理完成！"
echo ""
echo "⚠️  下一步："
echo "   1. 檢查結果：git log --all --oneline | head -10"
echo "   2. 強制推送到遠端：git push --force --all"
echo "   3. 通知所有協作者重新 clone"
echo ""

