#!/usr/bin/env python3
"""
中文測試報告生成器
執行 pytest 並生成中文測試報告
"""
import subprocess
import sys
import os
import re
from pathlib import Path
from collections import defaultdict

# 切換到專案根目錄（腳本位於 scripts/ 目錄下）
script_dir = Path(__file__).parent
project_root = script_dir.parent
os.chdir(project_root)


def parse_pytest_output(output):
    """解析 pytest 輸出"""
    lines = output.split('\n')
    
    passed = []
    failed = []
    skipped = []
    errors = defaultdict(str)
    
    current_test = None
    in_failure = False
    failure_lines = []
    
    for i, line in enumerate(lines):
        # 匹配測試結果行 - 支援多種格式
        # 格式1: tests/test_file.py::TestClass::test_function PASSED
        # 格式2: tests/test_file.py::test_function PASSED
        if 'PASSED' in line:
            # 嘗試匹配完整格式
            match = re.search(r'tests/([^:]+)::([^:]+)::([^ ]+)\s+PASSED', line)
            if match:
                file_name, class_name, test_name = match.groups()
                passed.append(f"{class_name}::{test_name}")
            else:
                # 嘗試匹配無類別格式
                match = re.search(r'tests/([^:]+)::([^ ]+)\s+PASSED', line)
                if match:
                    file_name, test_name = match.groups()
                    passed.append(test_name)
        
        elif 'FAILED' in line:
            # 嘗試匹配完整格式
            match = re.search(r'tests/([^:]+)::([^:]+)::([^ ]+)\s+FAILED', line)
            if match:
                file_name, class_name, test_name = match.groups()
                current_test = f"{class_name}::{test_name}"
                failed.append(current_test)
                in_failure = True
                failure_lines = []
            else:
                # 嘗試匹配無類別格式
                match = re.search(r'tests/([^:]+)::([^ ]+)\s+FAILED', line)
                if match:
                    file_name, test_name = match.groups()
                    current_test = test_name
                    failed.append(current_test)
                    in_failure = True
                    failure_lines = []
        
        elif 'SKIPPED' in line:
            match = re.search(r'tests/([^:]+)::([^:]+)::([^ ]+)\s+SKIPPED', line)
            if match:
                file_name, class_name, test_name = match.groups()
                skipped.append(f"{class_name}::{test_name}")
            else:
                match = re.search(r'tests/([^:]+)::([^ ]+)\s+SKIPPED', line)
                if match:
                    file_name, test_name = match.groups()
                    skipped.append(test_name)
        
        # 收集失敗詳情
        if in_failure and current_test:
            if line.strip().startswith('E '):
                error_msg = line.strip()[2:].strip()  # 移除 'E ' 前綴
                if error_msg and error_msg not in failure_lines:
                    failure_lines.append(error_msg)
            elif line.strip() and line.strip().startswith('assert'):
                failure_lines.append(line.strip())
            elif 'FAILURES' in line or 'short test summary' in line.lower() or 'assert' in line:
                if failure_lines:
                    errors[current_test] = ' | '.join(failure_lines[:2])  # 只保留前2行
                in_failure = False
                current_test = None
    
    # 如果還有未處理的失敗詳情
    if in_failure and current_test and failure_lines:
        errors[current_test] = ' | '.join(failure_lines[:2])
    
    # 提取總數 - 匹配多種格式
    total_match = re.search(r'(\d+)\s+(passed|failed|skipped|error)', output, re.IGNORECASE)
    if total_match:
        total_info = total_match.group(0)
    else:
        # 嘗試匹配完整格式: "92 passed, 4 failed, 0 skipped in 1.41s"
        total_match = re.search(r'(\d+)\s+passed[,\s]+(\d+)\s+failed[,\s]+(\d+)\s+skipped', output, re.IGNORECASE)
        if total_match:
            total_info = f"{total_match.group(1)} passed, {total_match.group(2)} failed, {total_match.group(3)} skipped"
        else:
            total_info = ""
    
    return passed, failed, skipped, errors, total_info


def print_chinese_report(passed, failed, skipped, errors, total_info, exit_code):
    """輸出中文測試報告"""
    print("\n" + "="*80)
    print("測試結果摘要（中文）")
    print("="*80)
    
    total = len(passed) + len(failed) + len(skipped)
    
    # 通過的測試
    if passed:
        print(f"\n✅ 通過的測試 ({len(passed)}/{total}):")
        for i, test in enumerate(passed[:30], 1):
            print(f"   {i}. {test}")
        if len(passed) > 30:
            print(f"   ... 還有 {len(passed) - 30} 個測試通過")
    else:
        print("\n✅ 通過的測試：無")
    
    # 失敗的測試
    if failed:
        print(f"\n❌ 失敗的測試 ({len(failed)}/{total}):")
        for i, test in enumerate(failed[:30], 1):
            print(f"   {i}. {test}")
            if test in errors:
                error_msg = errors[test]
                if len(error_msg) > 100:
                    error_msg = error_msg[:100] + "..."
                print(f"      錯誤: {error_msg}")
        if len(failed) > 30:
            print(f"   ... 還有 {len(failed) - 30} 個測試失敗")
    else:
        print("\n❌ 失敗的測試：無")
    
    # 跳過的測試
    if skipped:
        print(f"\n⏭️  跳過的測試 ({len(skipped)}/{total}):")
        for i, test in enumerate(skipped[:10], 1):
            print(f"   {i}. {test}")
        if len(skipped) > 10:
            print(f"   ... 還有 {len(skipped) - 10} 個測試跳過")
    
    # 總結
    print("\n" + "="*80)
    if exit_code == 0:
        print(f"🎉 所有測試通過！總共 {total} 個測試")
        if total_info:
            print(f"   ({total_info})")
    else:
        print(f"⚠️  測試完成：{len(passed)} 個通過，{len(failed)} 個失敗，{len(skipped)} 個跳過")
        if total_info:
            print(f"   ({total_info})")
    print("="*80 + "\n")


def main():
    """主函數"""
    # 執行 pytest
    # 如果參數中包含 --no-cov，移除覆蓋率相關選項
    args = sys.argv[1:]
    if '--no-cov' in args:
        args.remove('--no-cov')
        # 從 pytest.ini 讀取的選項中移除覆蓋率相關的
        # 我們通過環境變數或直接修改命令來處理
    
    # 確保測試路徑正確
    cmd = ['pytest', 'tests/unit', 'tests/integration', 'tests/api'] + args
    
    print("="*80)
    print("執行測試套件")
    print("="*80)
    print()
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        
        # 顯示原始輸出
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            # 過濾掉一些警告訊息
            stderr_lines = result.stderr.split('\n')
            filtered_stderr = []
            for line in stderr_lines:
                # 過濾掉插件導入錯誤（如果有的話）
                if 'pytest_custom_report' not in line and 'ImportError' not in line:
                    filtered_stderr.append(line)
                elif 'WARNING' in line or 'Warning' in line:
                    # 保留警告但簡化顯示
                    pass
            if filtered_stderr:
                print('\n'.join(filtered_stderr), file=sys.stderr)
        
        # 解析並顯示中文報告
        full_output = result.stdout + result.stderr
        passed, failed, skipped, errors, total_info = parse_pytest_output(full_output)
        print_chinese_report(passed, failed, skipped, errors, total_info, result.returncode)
        
        sys.exit(result.returncode)
        
    except KeyboardInterrupt:
        print("\n\n測試被中斷")
        sys.exit(130)
    except Exception as e:
        print(f"\n執行測試時發生錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()

