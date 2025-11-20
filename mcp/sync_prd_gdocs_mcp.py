#!/usr/bin/env python3
"""
PRD.md 與 Google Docs 雙向同步工具（使用 MCP）

此版本使用 MCP 工具來同步，不需要 Google Service Account 憑證。
只需要在 Cursor 中完成 OAuth 認證即可。

功能：
- 將 PRD.md 同步到 Google Docs（使用 MCP）
- 將 Google Docs 同步回 PRD.md（使用 MCP）
- 自動判斷同步方向（根據修改時間）
- 記錄同步歷史

使用方法：
    # 在 Cursor 中執行（需要 MCP 連線）
    python mcp/sync_prd_gdocs_mcp.py --to-gdoc
    
    # 從 Google Docs 同步回 PRD.md
    python mcp/sync_prd_gdocs_mcp.py --from-gdoc
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

load_dotenv()

# 配置
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "1cX0dtEBVi0qZHniciqvS89tUG3c1f1FS5O5brg74aFk")
# PRD.md 在專案根目錄，同步腳本在 mcp/ 目錄下
PRD_MD_PATH = Path(__file__).parent.parent / "PRD.md"
SYNC_LOG_PATH = Path(__file__).parent / ".prd_sync_log.json"


def load_sync_log() -> Dict[str, Any]:
    """載入同步記錄"""
    if SYNC_LOG_PATH.exists():
        try:
            with open(SYNC_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "last_md_mtime": None,
        "last_sync_time": None,
        "sync_history": []
    }


def save_sync_log(log_data: Dict[str, Any]):
    """儲存同步記錄"""
    with open(SYNC_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log_data, f, ensure_ascii=False, indent=2)


def read_prd_md() -> Optional[str]:
    """讀取 PRD.md"""
    try:
        with open(PRD_MD_PATH, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"❌ 讀取 PRD.md 失敗：{e}")
        return None


def write_prd_md(content: str) -> bool:
    """寫入 PRD.md"""
    try:
        with open(PRD_MD_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ 已更新 PRD.md")
        return True
    except Exception as e:
        print(f"❌ 寫入 PRD.md 失敗：{e}")
        return False


def get_prd_mtime() -> Optional[float]:
    """取得 PRD.md 修改時間"""
    if PRD_MD_PATH.exists():
        return PRD_MD_PATH.stat().st_mtime
    return None


def sync_to_gdocs_mcp(markdown_content: str) -> bool:
    """
    使用 MCP 工具同步到 Google Docs
    
    注意：此功能需要在 Cursor 中執行，並且需要 MCP 連線已建立。
    實際的同步操作會透過 MCP 工具完成。
    """
    print("📤 使用 MCP 工具同步到 Google Docs...")
    print(f"   文件 ID: {GOOGLE_DOC_ID}")
    print()
    print("⚠️  注意：此功能需要在 Cursor 中使用 MCP 工具執行")
    print("   請在 Cursor 中執行以下操作：")
    print()
    print("   1. 使用 MCP 工具刪除現有內容")
    print("   2. 使用 MCP 工具插入新內容")
    print()
    print("   或者，您可以使用以下 MCP 工具：")
    print("   - GOOGLEDOCS_DELETE_CONTENT_RANGE")
    print("   - GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN (重新創建)")
    print()
    print("💡 建議：使用 GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN 重新創建文檔")
    print("   這樣可以確保格式正確，並且不需要手動刪除內容")
    print()
    
    # 返回 False，表示需要手動使用 MCP 工具
    return False


def sync_from_gdocs_mcp() -> Optional[str]:
    """
    使用 MCP 工具從 Google Docs 讀取內容
    
    注意：目前 MCP 工具可能沒有直接讀取文檔內容的功能。
    需要檢查可用的 MCP 工具。
    """
    print("📥 使用 MCP 工具從 Google Docs 讀取...")
    print(f"   文件 ID: {GOOGLE_DOC_ID}")
    print()
    print("⚠️  注意：此功能需要在 Cursor 中使用 MCP 工具執行")
    print("   目前 MCP 工具可能沒有直接讀取文檔內容的功能")
    print("   建議使用 Google Docs API 版本（需要憑證）")
    print()
    
    return None


def main():
    parser = argparse.ArgumentParser(description="PRD.md ↔ Google Docs 雙向同步（MCP 版本）")
    parser.add_argument(
        '--to-gdoc',
        action='store_true',
        help='同步到 Google Docs'
    )
    parser.add_argument(
        '--from-gdoc',
        action='store_true',
        help='從 Google Docs 同步回 PRD.md'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📄 PRD.md ↔ Google Docs 雙向同步工具（MCP 版本）")
    print("=" * 60)
    print(f"PRD.md: {PRD_MD_PATH}")
    print(f"Google Docs ID: {GOOGLE_DOC_ID}")
    print(f"文件連結: https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit")
    print()
    print("ℹ️  此版本使用 MCP 工具，不需要 Google Service Account 憑證")
    print("   但需要在 Cursor 中使用 MCP 工具手動執行同步操作")
    print()
    
    # 載入同步記錄
    log_data = load_sync_log()
    
    success = False
    timestamp = datetime.now().isoformat()
    direction = None
    
    if args.from_gdoc:
        # 從 Google Docs 同步
        direction = "from-gdoc"
        print("📥 從 Google Docs 同步到 PRD.md...")
        print()
        print("❌ 目前 MCP 工具不支援直接讀取 Google Docs 內容")
        print("   請使用 Google Docs API 版本：python mcp/sync_prd_gdocs.py --from-gdoc")
        print("   或手動從 Google Docs 複製內容到 PRD.md")
        
    elif args.to_gdoc:
        # 同步到 Google Docs
        direction = "to-gdoc"
        print("📤 從 PRD.md 同步到 Google Docs...")
        print()
        md_content = read_prd_md()
        if md_content:
            print("✅ 已讀取 PRD.md 內容")
            print()
            print("=" * 60)
            print("📋 請在 Cursor 中使用以下 MCP 工具完成同步：")
            print("=" * 60)
            print()
            print("⚠️  重要：請更新現有文件，不要創建新文件")
            print(f"   現有文件 ID: {GOOGLE_DOC_ID}")
            print()
            print("更新步驟：")
            print("  1. 使用 GOOGLEDOCS_DELETE_CONTENT_RANGE 刪除現有內容")
            print("  2. 使用 GOOGLEDOCS_CREATE_DOCUMENT_MARKDOWN 重新創建內容")
            print("     （注意：在同一個文件中，使用相同的文件 ID）")
            print()
            print("=" * 60)
            print("💡 提示：您也可以直接告訴 AI 助手：")
            print("   '請使用 MCP 工具將 PRD.md 的內容同步到 Google Docs'")
            print("=" * 60)
            
            # 將內容保存到臨時文件，方便 MCP 工具讀取
            temp_file = Path(__file__).parent / ".prd_content_temp.md"
            try:
                with open(temp_file, 'w', encoding='utf-8') as f:
                    f.write(md_content)
                print()
                print(f"💾 PRD.md 內容已保存到臨時文件：{temp_file}")
                print("   您可以在 Cursor 中讓 AI 助手讀取此文件並同步到 Google Docs")
            except Exception as e:
                print(f"⚠️  無法保存臨時文件：{e}")
            
            # 不標記為成功，因為需要手動操作
            success = False
    else:
        # 自動判斷：預設同步到 Google Docs
        direction = "to-gdoc"
        print("🔍 自動判斷：同步到 Google Docs...")
        print()
        md_content = read_prd_md()
        if md_content:
            print("✅ 已讀取 PRD.md 內容")
            print()
            print("請使用 --to-gdoc 參數來執行同步")
            print("或告訴 AI 助手：'請使用 MCP 工具將 PRD.md 同步到 Google Docs'")
    
    # 記錄同步歷史
    log_data["last_md_mtime"] = get_prd_mtime()
    log_data["last_sync_time"] = timestamp
    log_data["sync_history"].append({
        "timestamp": timestamp,
        "direction": direction,
        "success": success,
        "method": "mcp"
    })
    # 只保留最近 50 筆記錄
    log_data["sync_history"] = log_data["sync_history"][-50:]
    save_sync_log(log_data)
    
    if not success:
        print()
        print("=" * 60)
        print("ℹ️  此腳本僅提供指引，實際同步需要透過 MCP 工具完成")
        print("=" * 60)
        sys.exit(0)  # 退出碼 0，因為這是預期的行為


if __name__ == "__main__":
    main()

