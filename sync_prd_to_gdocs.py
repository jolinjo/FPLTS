#!/usr/bin/env python3
"""
PRD.md 與 Google Docs 雙向同步腳本

功能：
1. 將 PRD.md 的內容同步到 Google Docs
2. 將 Google Docs 的內容同步回 PRD.md
3. 根據修改時間決定同步方向
4. 記錄同步歷史

使用方法：
    python sync_prd_to_gdocs.py --direction auto    # 自動判斷同步方向
    python sync_prd_to_gdocs.py --direction to-gdoc # 強制同步到 Google Docs
    python sync_prd_to_gdocs.py --direction to-md   # 強制同步到 PRD.md
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# Google Docs 文件 ID（從之前創建的文件中取得）
GOOGLE_DOC_ID = os.getenv("GOOGLE_DOC_ID", "1cX0dtEBVi0qZHniciqvS89tUG3c1f1FS5O5brg74aFk")
PRD_MD_PATH = Path(__file__).parent / "PRD.md"
SYNC_LOG_PATH = Path(__file__).parent / ".prd_sync_log.json"


def load_sync_log() -> Dict[str, Any]:
    """載入同步記錄"""
    if SYNC_LOG_PATH.exists():
        try:
            with open(SYNC_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️  讀取同步記錄失敗：{e}")
    return {
        "last_md_mtime": None,
        "last_gdoc_mtime": None,
        "sync_history": []
    }


def save_sync_log(log_data: Dict[str, Any]):
    """儲存同步記錄"""
    try:
        with open(SYNC_LOG_PATH, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠️  儲存同步記錄失敗：{e}")


def read_prd_md() -> Optional[str]:
    """讀取 PRD.md 內容"""
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
    """取得 PRD.md 的修改時間"""
    if PRD_MD_PATH.exists():
        return PRD_MD_PATH.stat().st_mtime
    return None


def sync_to_gdocs_via_mcp(markdown_content: str) -> bool:
    """
    透過 MCP 工具同步到 Google Docs
    
    注意：由於 MCP 工具的限制，我們需要：
    1. 先刪除現有內容
    2. 再插入新內容
    或者使用更新功能（如果可用）
    """
    print("📤 正在同步到 Google Docs...")
    print("   注意：此功能需要透過 MCP 工具執行")
    print(f"   文件 ID: {GOOGLE_DOC_ID}")
    print("   請在 Cursor 中使用 MCP 工具來完成同步")
    return False


def sync_from_gdocs_via_mcp() -> Optional[str]:
    """
    透過 MCP 工具從 Google Docs 讀取內容
    
    注意：需要檢查 MCP 工具是否支援讀取功能
    """
    print("📥 正在從 Google Docs 讀取...")
    print("   注意：此功能需要透過 MCP 工具執行")
    print(f"   文件 ID: {GOOGLE_DOC_ID}")
    print("   請在 Cursor 中使用 MCP 工具來完成同步")
    return None


def sync_to_gdocs_direct(markdown_content: str) -> bool:
    """
    直接使用 Google Docs API 同步到 Google Docs
    需要安裝 google-api-python-client
    """
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        
        # 載入憑證
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if not os.path.exists(credentials_path):
            print(f"❌ 找不到憑證檔案：{credentials_path}")
            return False
        
        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/documents']
        )
        
        service = build('docs', 'v1', credentials=creds)
        
        # 讀取現有文檔
        doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
        
        # 取得文檔內容的範圍
        if 'body' in doc and 'content' in doc['body']:
            # 計算需要刪除的範圍
            # 找到最後一個元素的索引
            content = doc['body']['content']
            if content:
                # 刪除所有現有內容（除了最後一個換行）
                requests = []
                # 從第二個元素開始刪除（第一個是文檔結構）
                if len(content) > 1:
                    end_index = content[-1]['endIndex'] - 1
                    if end_index > 1:
                        requests.append({
                            'deleteContentRange': {
                                'range': {
                                    'startIndex': 1,
                                    'endIndex': end_index
                                }
                            }
                        })
                
                # 插入新內容
                requests.append({
                    'insertText': {
                        'location': {'index': 1},
                        'text': markdown_content
                    }
                })
                
                # 執行批次更新
                if requests:
                    service.documents().batchUpdate(
                        documentId=GOOGLE_DOC_ID,
                        body={'requests': requests}
                    ).execute()
                    print("✅ 已同步到 Google Docs")
                    return True
        
        print("⚠️  文檔結構異常，無法更新")
        return False
        
    except ImportError:
        print("❌ 缺少 google-api-python-client 套件")
        print("   請執行：pip install google-api-python-client")
        return False
    except HttpError as e:
        print(f"❌ Google Docs API 錯誤：{e}")
        return False
    except Exception as e:
        print(f"❌ 同步到 Google Docs 失敗：{e}")
        import traceback
        traceback.print_exc()
        return False


def sync_from_gdocs_direct() -> Optional[str]:
    """
    直接使用 Google Docs API 從 Google Docs 讀取內容
    """
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        
        # 載入憑證
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if not os.path.exists(credentials_path):
            print(f"❌ 找不到憑證檔案：{credentials_path}")
            return None
        
        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )
        
        service = build('docs', 'v1', credentials=creds)
        
        # 讀取文檔
        doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
        
        # 提取文字內容
        def extract_text(element):
            """遞迴提取文字內容"""
            text = ""
            if 'paragraph' in element:
                para = element['paragraph']
                if 'elements' in para:
                    for elem in para['elements']:
                        if 'textRun' in elem:
                            text += elem['textRun'].get('content', '')
            elif 'table' in element:
                # 處理表格（簡化版）
                text += "\n[表格內容]\n"
            elif 'sectionBreak' in element:
                text += "\n---\n"
            return text
        
        content = ""
        if 'body' in doc and 'content' in doc['body']:
            for element in doc['body']['content']:
                content += extract_text(element)
        
        print("✅ 已從 Google Docs 讀取內容")
        return content
        
    except ImportError:
        print("❌ 缺少 google-api-python-client 套件")
        print("   請執行：pip install google-api-python-client")
        return None
    except HttpError as e:
        print(f"❌ Google Docs API 錯誤：{e}")
        return None
    except Exception as e:
        print(f"❌ 從 Google Docs 讀取失敗：{e}")
        import traceback
        traceback.print_exc()
        return None


def determine_sync_direction(log_data: Dict[str, Any]) -> str:
    """根據修改時間決定同步方向"""
    md_mtime = get_prd_mtime()
    last_md_mtime = log_data.get("last_md_mtime")
    last_gdoc_mtime = log_data.get("last_gdoc_mtime")
    
    if md_mtime is None:
        return "to-gdoc"  # PRD.md 不存在，只能同步到 Google Docs
    
    if last_md_mtime is None and last_gdoc_mtime is None:
        return "to-gdoc"  # 首次同步，預設同步到 Google Docs
    
    # 比較修改時間
    if last_md_mtime and md_mtime > last_md_mtime:
        return "to-gdoc"  # PRD.md 有更新
    
    # 如果 Google Docs 有更新（需要透過 API 檢查，這裡簡化處理）
    # 實際應用中，可以透過 Google Docs API 取得修改時間
    return "to-gdoc"  # 預設同步到 Google Docs


def main():
    parser = argparse.ArgumentParser(description="PRD.md 與 Google Docs 雙向同步")
    parser.add_argument(
        '--direction',
        choices=['auto', 'to-gdoc', 'to-md'],
        default='auto',
        help='同步方向：auto=自動判斷, to-gdoc=同步到Google Docs, to-md=同步到PRD.md'
    )
    parser.add_argument(
        '--use-mcp',
        action='store_true',
        help='使用 MCP 工具（需要 Cursor 環境）'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("📄 PRD.md ↔ Google Docs 雙向同步工具")
    print("=" * 60)
    print(f"PRD.md 路徑: {PRD_MD_PATH}")
    print(f"Google Docs ID: {GOOGLE_DOC_ID}")
    print()
    
    # 載入同步記錄
    log_data = load_sync_log()
    
    # 決定同步方向
    if args.direction == 'auto':
        direction = determine_sync_direction(log_data)
        print(f"🔍 自動判斷同步方向：{direction}")
    else:
        direction = args.direction
        print(f"📌 指定同步方向：{direction}")
    
    print()
    
    success = False
    timestamp = datetime.now().isoformat()
    
    if direction == 'to-gdoc':
        # 同步到 Google Docs
        md_content = read_prd_md()
        if md_content:
            if args.use_mcp:
                success = sync_to_gdocs_via_mcp(md_content)
            else:
                success = sync_to_gdocs_direct(md_content)
            
            if success:
                log_data["last_md_mtime"] = get_prd_mtime()
                log_data["sync_history"].append({
                    "timestamp": timestamp,
                    "direction": "to-gdoc",
                    "success": True
                })
                save_sync_log(log_data)
    
    elif direction == 'to-md':
        # 從 Google Docs 同步到 PRD.md
        if args.use_mcp:
            gdoc_content = sync_from_gdocs_via_mcp()
        else:
            gdoc_content = sync_from_gdocs_direct()
        
        if gdoc_content:
            success = write_prd_md(gdoc_content)
            if success:
                log_data["last_md_mtime"] = get_prd_mtime()
                log_data["sync_history"].append({
                    "timestamp": timestamp,
                    "direction": "to-md",
                    "success": True
                })
                save_sync_log(log_data)
    
    if not success:
        print()
        print("⚠️  同步未完成，請檢查錯誤訊息")
        log_data["sync_history"].append({
            "timestamp": timestamp,
            "direction": direction,
            "success": False
        })
        save_sync_log(log_data)
        sys.exit(1)
    
    print()
    print("=" * 60)
    print("✅ 同步完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

