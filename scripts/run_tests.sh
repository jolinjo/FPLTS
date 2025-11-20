#!/bin/bash
# 測試執行腳本（支援中文輸出）

# 切換到專案根目錄（腳本位於 scripts/ 目錄下）
cd "$(dirname "$0")/.."

# 檢查是否使用中文輸出模式
if [ "$1" = "--cn" ] || [ "$1" = "--chinese" ]; then
    shift
    # 使用簡化版腳本生成中文報告
    if [ -f "tests/run_tests_simple_cn.sh" ]; then
        bash tests/run_tests_simple_cn.sh "$@"
        exit $?
    fi
fi

echo "=========================================="
echo "執行測試套件"
echo "=========================================="

# 檢查是否在虛擬環境中
if [ -z "$VIRTUAL_ENV" ]; then
    echo "警告：未偵測到虛擬環境"
    echo "建議先啟動虛擬環境：source venv/bin/activate"
    read -p "是否繼續？(y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# 檢查 pytest 是否安裝
if ! command -v pytest &> /dev/null; then
    echo "錯誤：pytest 未安裝"
    echo "請執行：pip install -r requirements.txt"
    exit 1
fi

# 執行測試並捕獲輸出
echo ""
echo "執行所有測試..."
echo ""

# 執行測試並保存結果到臨時文件
TEMP_OUTPUT=$(mktemp)
pytest "$@" 2>&1 | tee "$TEMP_OUTPUT"
TEST_EXIT_CODE=${PIPESTATUS[0]}

# 解析測試結果
PASSED_TESTS=$(grep -E "PASSED|passed" "$TEMP_OUTPUT" | wc -l | tr -d ' ')
FAILED_TESTS=$(grep -E "FAILED|failed" "$TEMP_OUTPUT" | wc -l | tr -d ' ')
SKIPPED_TESTS=$(grep -E "SKIPPED|skipped" "$TEMP_OUTPUT" | wc -l | tr -d ' ')
TOTAL_LINE=$(grep -E "[0-9]+ (passed|failed|skipped|error)" "$TEMP_OUTPUT" | tail -1)

# 顯示中文摘要
echo ""
echo "=========================================="
echo "測試結果摘要（中文）"
echo "=========================================="
echo ""

# 通過的測試
if [ "$PASSED_TESTS" -gt 0 ]; then
    echo "✅ 通過的測試 ($PASSED_TESTS 個):"
    grep "PASSED" "$TEMP_OUTPUT" | sed -E 's/.*::([^:]+)::([^ ]+).*/   ✓ \1::\2/' | head -30
    if [ "$PASSED_TESTS" -gt 30 ]; then
        echo "   ... 還有 $((PASSED_TESTS - 30)) 個測試通過"
    fi
    echo ""
fi

# 失敗的測試
if [ "$FAILED_TESTS" -gt 0 ]; then
    echo "❌ 失敗的測試 ($FAILED_TESTS 個):"
    grep "FAILED" "$TEMP_OUTPUT" | sed -E 's/.*::([^:]+)::([^ ]+).*/   ✗ \1::\2/' | head -30
    if [ "$FAILED_TESTS" -gt 30 ]; then
        echo "   ... 還有 $((FAILED_TESTS - 30)) 個測試失敗"
    fi
    echo ""
    
    # 顯示失敗詳情標題
    if grep -q "FAILURES" "$TEMP_OUTPUT"; then
        echo "失敗詳情："
        grep -A 3 "FAILURES" "$TEMP_OUTPUT" | grep -E "test_.*\.py::" | head -5 | sed 's/^/   /'
        echo ""
    fi
fi

# 跳過的測試
if [ "$SKIPPED_TESTS" -gt 0 ]; then
    echo "⏭️  跳過的測試 ($SKIPPED_TESTS 個):"
    grep "SKIPPED" "$TEMP_OUTPUT" | sed -E 's/.*::([^:]+)::([^ ]+).*/   ⊘ \1::\2/' | head -10
    echo ""
fi

# 總結
echo "=========================================="
if [ "$TEST_EXIT_CODE" -eq 0 ]; then
    echo "🎉 所有測試通過！"
    if [ -n "$TOTAL_LINE" ]; then
        echo "   $TOTAL_LINE"
    fi
else
    echo "⚠️  測試完成，但有失敗項目"
    if [ -n "$TOTAL_LINE" ]; then
        echo "   $TOTAL_LINE"
    fi
fi
echo "=========================================="
echo ""

# 清理臨時文件
rm -f "$TEMP_OUTPUT"

exit $TEST_EXIT_CODE

