#!/bin/bash
# 測試執行腳本（中文輸出版本）

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

# 執行測試並保存結果
TEST_OUTPUT=$(pytest "$@" 2>&1)
TEST_EXIT_CODE=$?

# 顯示原始輸出
echo "$TEST_OUTPUT"

# 解析測試結果
PASSED_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "passed" | wc -l | tr -d ' ')
FAILED_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "failed" | wc -l | tr -d ' ')
SKIPPED_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "skipped" | wc -l | tr -d ' ')
TOTAL_COUNT=$(echo "$TEST_OUTPUT" | grep -oE "[0-9]+ (passed|failed|skipped|error)" | head -1 | grep -oE "[0-9]+" | head -1)

# 提取通過的測試
echo ""
echo "=========================================="
echo "測試結果摘要（中文）"
echo "=========================================="
echo ""

if [ "$PASSED_COUNT" -gt 0 ]; then
    echo "✅ 通過的測試："
    echo "$TEST_OUTPUT" | grep "PASSED" | sed 's/.*::\(.*\)::\(.*\) PASSED.*/   ✓ \1::\2/' | head -20
    if [ "$PASSED_COUNT" -gt 20 ]; then
        echo "   ... 還有 $((PASSED_COUNT - 20)) 個測試通過"
    fi
    echo ""
fi

if [ "$FAILED_COUNT" -gt 0 ]; then
    echo "❌ 失敗的測試："
    echo "$TEST_OUTPUT" | grep "FAILED" | sed 's/.*::\(.*\)::\(.*\) FAILED.*/   ✗ \1::\2/' | head -20
    if [ "$FAILED_COUNT" -gt 20 ]; then
        echo "   ... 還有 $((FAILED_COUNT - 20)) 個測試失敗"
    fi
    echo ""
    
    # 顯示失敗詳情
    echo "失敗詳情："
    echo "$TEST_OUTPUT" | grep -A 5 "FAILURES" | grep -E "test_.*\.py::" | head -10
    echo ""
fi

if [ "$SKIPPED_COUNT" -gt 0 ]; then
    echo "⏭️  跳過的測試："
    echo "$TEST_OUTPUT" | grep "SKIPPED" | sed 's/.*::\(.*\)::\(.*\) SKIPPED.*/   ⊘ \1::\2/' | head -10
    echo ""
fi

# 總結
echo "=========================================="
if [ "$TEST_EXIT_CODE" -eq 0 ]; then
    echo "🎉 所有測試通過！"
    if [ -n "$TOTAL_COUNT" ]; then
        echo "   總共 $TOTAL_COUNT 個測試"
    fi
else
    echo "⚠️  測試完成，但有失敗項目"
    if [ -n "$TOTAL_COUNT" ]; then
        echo "   通過: $PASSED_COUNT, 失敗: $FAILED_COUNT, 跳過: $SKIPPED_COUNT"
    fi
fi
echo "=========================================="
echo ""

exit $TEST_EXIT_CODE

