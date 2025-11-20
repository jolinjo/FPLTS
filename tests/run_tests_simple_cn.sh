#!/bin/bash
# 簡化版中文測試報告腳本

echo "================================================================================
執行測試套件
================================================================================
"

# 執行測試並捕獲輸出
OUTPUT=$(pytest -v 2>&1)
EXIT_CODE=$?

# 顯示原始輸出
echo "$OUTPUT"

# 解析並顯示中文摘要
echo ""
echo "================================================================================
測試結果摘要（中文）
================================================================================
"

# 提取通過的測試
PASSED=$(echo "$OUTPUT" | grep -E "PASSED" | wc -l | tr -d ' ')
if [ "$PASSED" -gt 0 ]; then
    echo ""
    echo "✅ 通過的測試 ($PASSED 個):"
    echo "$OUTPUT" | grep "PASSED" | sed -E 's/.*::([^:]+)::([^ ]+).*/   ✓ \1::\2/' | head -30
    if [ "$PASSED" -gt 30 ]; then
        REMAINING=$((PASSED - 30))
        echo "   ... 還有 $REMAINING 個測試通過"
    fi
fi

# 提取失敗的測試
FAILED=$(echo "$OUTPUT" | grep -E "FAILED" | wc -l | tr -d ' ')
if [ "$FAILED" -gt 0 ]; then
    echo ""
    echo "❌ 失敗的測試 ($FAILED 個):"
    echo "$OUTPUT" | grep "FAILED" | sed -E 's/.*::([^:]+)::([^ ]+).*/   ✗ \1::\2/' | head -30
    if [ "$FAILED" -gt 30 ]; then
        REMAINING=$((FAILED - 30))
        echo "   ... 還有 $REMAINING 個測試失敗"
    fi
fi

# 提取跳過的測試
SKIPPED=$(echo "$OUTPUT" | grep -E "SKIPPED" | wc -l | tr -d ' ')
if [ "$SKIPPED" -gt 0 ]; then
    echo ""
    echo "⏭️  跳過的測試 ($SKIPPED 個):"
    echo "$OUTPUT" | grep "SKIPPED" | sed -E 's/.*::([^:]+)::([^ ]+).*/   ⊘ \1::\2/' | head -10
fi

# 提取總數資訊
TOTAL_INFO=$(echo "$OUTPUT" | grep -E "[0-9]+ (passed|failed|skipped)" | tail -1)

# 總結
echo ""
echo "================================================================================"
if [ "$EXIT_CODE" -eq 0 ]; then
    echo "🎉 所有測試通過！"
    if [ -n "$TOTAL_INFO" ]; then
        echo "   $TOTAL_INFO"
    fi
else
    echo "⚠️  測試完成，但有失敗項目"
    if [ -n "$TOTAL_INFO" ]; then
        echo "   $TOTAL_INFO"
    fi
fi
echo "================================================================================
"

exit $EXIT_CODE

