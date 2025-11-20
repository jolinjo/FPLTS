#!/bin/bash
# 安全清理 Git 歷史中的敏感資訊
# 此版本會先檢查並處理未暫存的變更

echo "=========================================="
echo "⚠️  清理 Git 歷史中的敏感資訊（安全模式）"
echo "=========================================="
echo ""

# 檢查是否有未暫存的變更
if [ -n "$(git status --porcelain)" ]; then
    echo "⚠️  發現未暫存的變更"
    echo ""
    echo "選項："
    echo "1. 先提交所有變更，然後清理歷史"
    echo "2. 暫存變更（stash），清理後恢復"
    echo "3. 取消操作"
    echo ""
    read -p "請選擇 (1/2/3): " -n 1 -r
    echo
    echo ""
    
    case $REPLY in
        1)
            echo "提交所有變更..."
            git add -A
            git commit -m "chore: 清理敏感資訊前的變更"
            ;;
        2)
            echo "暫存變更..."
            git stash push -m "清理歷史前的變更"
            RESTORE_STASH=true
            ;;
        3)
            echo "取消操作"
            exit 0
            ;;
        *)
            echo "無效的選擇"
            exit 1
            ;;
    esac
fi

echo ""
echo "🚨 重要警告："
echo "   此操作會改寫 Git 歷史！"
echo "   所有協作者都需要重新 clone 倉庫！"
echo "   請確保已經備份重要資料！"
echo ""
read -p "確定要繼續嗎？(yes/no) " -r
echo

if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    if [ "$RESTORE_STASH" = true ]; then
        echo "恢復暫存的變更..."
        git stash pop
    fi
    echo "取消操作"
    exit 0
fi

echo ""
echo "選擇清理方式："
echo "1. 使用 git filter-branch（內建工具）"
echo "2. 使用 git filter-repo（推薦，需要安裝）"
echo "3. 僅刪除特定檔案（credentials.json, .env）"
echo ""
read -p "請選擇 (1/2/3): " -n 1 -r
echo
echo ""

case $REPLY in
    1)
        echo "使用 git filter-branch 清理..."
        echo ""
        
        # 設置環境變數以抑制警告
        export FILTER_BRANCH_SQUELCH_WARNING=1
        
        # 刪除 credentials.json
        if git log --all --full-history --source -- "*credentials.json" 2>/dev/null | grep -q "credentials.json"; then
            echo "刪除 credentials.json..."
            git filter-branch --force --index-filter \
                "git rm --cached --ignore-unmatch credentials.json" \
                --prune-empty --tag-name-filter cat -- --all
        fi
        
        # 刪除 .env
        if git log --all --full-history --source -- ".env" 2>/dev/null | grep -q "\.env"; then
            echo "刪除 .env..."
            git filter-branch --force --index-filter \
                "git rm --cached --ignore-unmatch .env" \
                --prune-empty --tag-name-filter cat -- --all
        fi
        
        echo ""
        echo "✅ 清理完成"
        ;;
    2)
        echo "使用 git filter-repo 清理..."
        echo ""
        
        # 檢查是否安裝了 git-filter-repo
        if ! command -v git-filter-repo &> /dev/null; then
            echo "❌ 錯誤：未安裝 git-filter-repo"
            echo ""
            echo "安裝方式："
            echo "  pip install git-filter-repo"
            echo "  或"
            echo "  brew install git-filter-repo"
            if [ "$RESTORE_STASH" = true ]; then
                git stash pop
            fi
            exit 1
        fi
        
        # 刪除 credentials.json
        if git log --all --full-history --source -- "*credentials.json" 2>/dev/null | grep -q "credentials.json"; then
            echo "刪除 credentials.json..."
            git filter-repo --path credentials.json --invert-paths --force
        fi
        
        # 刪除 .env
        if git log --all --full-history --source -- ".env" 2>/dev/null | grep -q "\.env"; then
            echo "刪除 .env..."
            git filter-repo --path .env --invert-paths --force
        fi
        
        echo ""
        echo "✅ 清理完成"
        ;;
    3)
        echo "僅刪除特定檔案..."
        echo ""
        
        export FILTER_BRANCH_SQUELCH_WARNING=1
        
        read -p "要刪除 credentials.json 嗎？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if git log --all --full-history --source -- "*credentials.json" 2>/dev/null | grep -q "credentials.json"; then
                echo "刪除 credentials.json..."
                git filter-branch --force --index-filter \
                    "git rm --cached --ignore-unmatch credentials.json" \
                    --prune-empty --tag-name-filter cat -- --all
            else
                echo "未發現 credentials.json 在歷史中"
            fi
        fi
        
        read -p "要刪除 .env 嗎？(y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if git log --all --full-history --source -- ".env" 2>/dev/null | grep -q "\.env"; then
                echo "刪除 .env..."
                git filter-branch --force --index-filter \
                    "git rm --cached --ignore-unmatch .env" \
                    --prune-empty --tag-name-filter cat -- --all
            else
                echo "未發現 .env 在歷史中"
            fi
        fi
        
        echo ""
        echo "✅ 清理完成"
        ;;
    *)
        echo "無效的選擇"
        if [ "$RESTORE_STASH" = true ]; then
            git stash pop
        fi
        exit 1
        ;;
esac

# 恢復暫存的變更
if [ "$RESTORE_STASH" = true ]; then
    echo ""
    echo "恢復暫存的變更..."
    git stash pop
fi

echo ""
echo "=========================================="
echo "⚠️  重要提醒："
echo "=========================================="
echo "1. 此操作已改寫本地 Git 歷史"
echo "2. 需要強制推送到遠端：git push --force --all"
echo "3. 通知所有協作者："
echo "   - 刪除本地倉庫"
echo "   - 重新 clone：git clone <repository-url>"
echo "4. 立即更換所有受影響的憑證和密鑰"
echo "5. 檢查 GitHub 的 Security 頁面，確認敏感資訊已移除"
echo ""

