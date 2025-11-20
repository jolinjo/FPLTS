#!/usr/bin/env python3
"""
PRD.md 與 Google Docs 同步工具（簡化版）

此腳本用於將 PRD.md 的內容同步到 Google Docs。
由於需要透過 MCP 工具來操作 Google Docs，此腳本主要用於：
1. 讀取 PRD.md 內容
2. 準備同步資料
3. 提供 MCP 工具調用的介面

實際同步需要透過 Cursor 的 MCP 工具執行。
"""

import os
import json
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Google Docs 文件 ID
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "1cX0dtEBVi0qZHniciqvS89tUG3c1f1FS5O5brg74aFk")
# PRD.md 在專案根目錄，同步腳本在 mcp/ 目錄下
PRD_MD_PATH = Path(__file__).parent.parent / "PRD.md"
SYNC_CONFIG_PATH = Path(__file__).parent / ".prd_sync_config.json"


def read_prd_md() -> str:
    """讀取 PRD.md 內容"""
    if not PRD_MD_PATH.exists():
        raise FileNotFoundError(f"找不到 PRD.md 檔案：{PRD_MD_PATH}")
    
    with open(PRD_MD_PATH, 'r', encoding='utf-8') as f:
        return f.read()


def save_sync_config(doc_id: str, last_sync: str):
    """儲存同步配置"""
    config = {
        "google_doc_id": doc_id,
        "last_sync_time": last_sync,
        "prd_md_path": str(PRD_MD_PATH)
    }
    with open(SYNC_CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)


def main():
    """主函數：讀取 PRD.md 並準備同步"""
    print("=" * 60)
    print("📄 PRD.md → Google Docs 同步準備")
    print("=" * 60)
    
    try:
        # 讀取 PRD.md
        print(f"📖 讀取 PRD.md: {PRD_MD_PATH}")
        content = read_prd_md()
        print(f"✅ 已讀取 {len(content)} 字元")
        
        # 儲存配置
        save_sync_config(GOOGLE_DOC_ID, datetime.now().isoformat())
        print(f"💾 已儲存同步配置")
        
        print()
        print("=" * 60)
        print("📋 同步資訊")
        print("=" * 60)
        print(f"Google Docs ID: {GOOGLE_DOC_ID}")
        print(f"文件連結: https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit")
        print()
        print("💡 下一步：")
        print("   在 Cursor 中使用 MCP 工具將內容同步到 Google Docs")
        print("   或執行：python sync_prd_to_gdocs.py --direction to-gdoc")
        print()
        
        return content
        
    except Exception as e:
        print(f"❌ 錯誤：{e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    main()

