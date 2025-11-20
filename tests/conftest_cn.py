"""
中文測試報告配置
在 conftest.py 中自動啟用
"""
import pytest
import sys
from pathlib import Path

# 添加自定義報告模組到路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "tests"))


def pytest_configure(config):
    """配置 pytest 以使用中文報告"""
    # 嘗試載入自定義報告插件
    try:
        from tests.pytest_custom_report import pytest_configure as custom_configure
        custom_configure(config)
    except ImportError:
        # 如果載入失敗，使用預設行為
        pass


def pytest_sessionfinish(session, exitstatus):
    """測試會話結束時顯示中文摘要"""
    passed = []
    failed = []
    skipped = []
    
    # 收集測試結果
    for item in session.items:
        if hasattr(item, 'rep_call'):
            rep = item.rep_call
            if rep:
                test_name = f"{item.cls.__name__ if item.cls else ''}::{item.name}" if hasattr(item, 'name') else str(item)
                if rep.outcome == 'passed':
                    passed.append(test_name)
                elif rep.outcome == 'failed':
                    failed.append((test_name, rep.longrepr))
                elif rep.outcome == 'skipped':
                    skipped.append(test_name)
    
    # 從 session 的報告中收集
    for report in session.items:
        if hasattr(report, 'rep_call') and report.rep_call:
            rep = report.rep_call
            test_name = f"{report.cls.__name__ if report.cls else ''}::{report.name}" if hasattr(report, 'name') else str(report)
            if rep.outcome == 'passed':
                passed.append(test_name)
            elif rep.outcome == 'failed':
                failed.append((test_name, rep.longrepr))
            elif rep.outcome == 'skipped':
                skipped.append(test_name)
    
    # 輸出中文摘要
    if passed or failed or skipped:
        print("\n" + "="*80)
        print("測試結果摘要（中文）")
        print("="*80)
        
        total = len(passed) + len(failed) + len(skipped)
        
        if passed:
            print(f"\n✅ 通過的測試 ({len(passed)}/{total}):")
            for i, test in enumerate(passed[:20], 1):
                print(f"   {i}. {test}")
            if len(passed) > 20:
                print(f"   ... 還有 {len(passed) - 20} 個測試通過")
        
        if failed:
            print(f"\n❌ 失敗的測試 ({len(failed)}/{total}):")
            for i, (test, error) in enumerate(failed[:20], 1):
                print(f"   {i}. {test}")
                if error:
                    error_str = str(error).split('\n')[0]
                    if len(error_str) > 80:
                        error_str = error_str[:80] + "..."
                    print(f"      錯誤: {error_str}")
            if len(failed) > 20:
                print(f"   ... 還有 {len(failed) - 20} 個測試失敗")
        
        if skipped:
            print(f"\n⏭️  跳過的測試 ({len(skipped)}/{total}):")
            for i, test in enumerate(skipped[:10], 1):
                print(f"   {i}. {test}")
            if len(skipped) > 10:
                print(f"   ... 還有 {len(skipped) - 10} 個測試跳過")
        
        print("\n" + "="*80)
        if len(failed) == 0:
            print(f"🎉 所有測試通過！總共 {total} 個測試")
        else:
            print(f"⚠️  測試完成：{len(passed)} 個通過，{len(failed)} 個失敗，{len(skipped)} 個跳過")
        print("="*80 + "\n")

