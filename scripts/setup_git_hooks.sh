#!/bin/bash
# 設置 Git Hooks 腳本
# 此腳本會設置 pre-commit hook 來自動執行安全檢查

PROJECT_ROOT=$(git rev-parse --show-toplevel 2>/dev/null)

if [ -z "$PROJECT_ROOT" ]; then
    echo "❌ 錯誤：不在 Git 倉庫中"
    exit 1
fi

HOOKS_DIR="$PROJECT_ROOT/.git/hooks"
PRE_COMMIT_HOOK="$HOOKS_DIR/pre-commit"

echo "=========================================="
echo "🔧 設置 Git Hooks"
echo "=========================================="
echo ""

# 檢查 hooks 目錄是否存在
if [ ! -d "$HOOKS_DIR" ]; then
    echo "❌ 錯誤：找不到 .git/hooks 目錄"
    exit 1
fi

# 檢查是否已經有 pre-commit hook
if [ -f "$PRE_COMMIT_HOOK" ]; then
    echo "⚠️  警告：已存在 pre-commit hook"
    echo "   檔案位置：$PRE_COMMIT_HOOK"
    echo ""
    read -p "是否要覆蓋現有的 hook？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "取消操作"
        exit 0
    fi
    # 備份現有的 hook
    cp "$PRE_COMMIT_HOOK" "$PRE_COMMIT_HOOK.backup.$(date +%Y%m%d_%H%M%S)"
    echo "✅ 已備份現有 hook"
fi

# 創建 pre-commit hook
cat > "$PRE_COMMIT_HOOK" << 'EOF'
#!/bin/bash
# Git pre-commit hook - 自動執行安全檢查

# 獲取專案根目錄
PROJECT_ROOT=$(git rev-parse --show-toplevel)
SECURITY_CHECK_SCRIPT="$PROJECT_ROOT/scripts/check_security.sh"

# 檢查安全檢查腳本是否存在
if [ ! -f "$SECURITY_CHECK_SCRIPT" ]; then
    echo "⚠️  警告：找不到安全檢查腳本 $SECURITY_CHECK_SCRIPT"
    echo "   跳過安全檢查"
    exit 0
fi

# 執行安全檢查
echo "🔒 執行提交前安全檢查..."
echo ""

if bash "$SECURITY_CHECK_SCRIPT"; then
    echo ""
    echo "✅ 安全檢查通過，允許提交"
    exit 0
else
    echo ""
    echo "❌ 安全檢查失敗！"
    echo ""
    echo "請修復上述問題後再提交。"
    echo "如果確定要跳過檢查，可以使用："
    echo "  git commit --no-verify"
    echo ""
    exit 1
fi
EOF

# 設置執行權限
chmod +x "$PRE_COMMIT_HOOK"

echo "✅ 已設置 pre-commit hook"
echo ""
echo "📋 Hook 功能："
echo "   - 在每次 git commit 前自動執行安全檢查"
echo "   - 如果檢查失敗，會阻止提交"
echo "   - 可以使用 'git commit --no-verify' 跳過檢查"
echo ""
echo "📍 Hook 位置：$PRE_COMMIT_HOOK"
echo ""
echo "✅ 設置完成！"

