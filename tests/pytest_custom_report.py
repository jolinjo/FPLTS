"""
自定義 pytest 報告插件
用於生成中文測試報告
"""
import pytest
from _pytest.terminal import TerminalReporter
from _pytest.reports import TestReport


class ChineseReporter(TerminalReporter):
    """中文測試報告器"""
    
    def __init__(self, config):
        super().__init__(config)
        self.passed_tests = []
        self.failed_tests = []
        self.skipped_tests = []
    
    def pytest_runtest_logreport(self, report: TestReport):
        """處理測試報告"""
        if report.when == 'call':  # 只在測試執行時記錄
            test_name = self._get_test_name(report)
            if report.outcome == 'passed':
                self.passed_tests.append(test_name)
            elif report.outcome == 'failed':
                self.failed_tests.append((test_name, report.longrepr))
            elif report.outcome == 'skipped':
                self.skipped_tests.append(test_name)
    
    def _get_test_name(self, report):
        """取得測試名稱"""
        # 格式：test_file.py::TestClass::test_function
        nodeid = report.nodeid
        # 簡化顯示：只顯示類別和函數名
        parts = nodeid.split('::')
        if len(parts) >= 3:
            return f"{parts[1]}::{parts[2]}"
        elif len(parts) == 2:
            return parts[1]
        return parts[0]
    
    def pytest_sessionfinish(self, session, exitstatus):
        """測試會話結束時輸出中文報告"""
        print("\n" + "="*80)
        print("測試結果摘要")
        print("="*80)
        
        total = len(self.passed_tests) + len(self.failed_tests) + len(self.skipped_tests)
        
        # 成功項目
        if self.passed_tests:
            print(f"\n✅ 通過的測試 ({len(self.passed_tests)}/{total}):")
            for i, test in enumerate(self.passed_tests, 1):
                print(f"   {i}. {test}")
        else:
            print("\n✅ 通過的測試：無")
        
        # 失敗項目
        if self.failed_tests:
            print(f"\n❌ 失敗的測試 ({len(self.failed_tests)}/{total}):")
            for i, (test, error) in enumerate(self.failed_tests, 1):
                print(f"   {i}. {test}")
                # 顯示錯誤的第一行
                if error:
                    error_lines = str(error).split('\n')
                    first_error = error_lines[0] if error_lines else ""
                    if first_error:
                        print(f"      錯誤: {first_error[:100]}...")
        else:
            print("\n❌ 失敗的測試：無")
        
        # 跳過的項目
        if self.skipped_tests:
            print(f"\n⏭️  跳過的測試 ({len(self.skipped_tests)}/{total}):")
            for i, test in enumerate(self.skipped_tests, 1):
                print(f"   {i}. {test}")
        
        # 總結
        print("\n" + "="*80)
        if len(self.failed_tests) == 0:
            print(f"🎉 所有測試通過！總共 {total} 個測試")
        else:
            print(f"⚠️  測試完成：{len(self.passed_tests)} 個通過，{len(self.failed_tests)} 個失敗，{len(self.skipped_tests)} 個跳過")
        print("="*80 + "\n")


def pytest_configure(config):
    """註冊自定義報告器"""
    if config.option.verbose >= 0:
        reporter = ChineseReporter(config)
        config.pluginmanager.register(reporter, "chinese_reporter")

