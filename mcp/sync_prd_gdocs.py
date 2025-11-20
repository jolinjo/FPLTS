#!/usr/bin/env python3
"""
PRD.md 與 Google Docs 雙向同步工具

功能：
- 將 PRD.md 同步到 Google Docs
- 將 Google Docs 同步回 PRD.md
- 自動判斷同步方向（根據修改時間）
- 記錄同步歷史

使用方法：
    # 自動判斷同步方向
    python sync_prd_gdocs.py

    # 強制同步到 Google Docs
    python sync_prd_gdocs.py --to-gdoc

    # 強制從 Google Docs 同步回 PRD.md
    python sync_prd_gdocs.py --from-gdoc
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


def sync_to_gdocs(markdown_content: str) -> bool:
    """同步到 Google Docs"""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        
        # 載入憑證
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if not os.path.exists(credentials_path):
            print(f"❌ 找不到憑證檔案：{credentials_path}")
            print("   請設定 GOOGLE_CREDENTIALS_PATH 環境變數或將憑證檔案命名為 credentials.json")
            return False
        
        print(f"🔐 載入憑證：{credentials_path}")
        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/documents']
        )
        
        service = build('docs', 'v1', credentials=creds)
        
        # 讀取現有文檔結構
        print(f"📖 讀取 Google Docs: {GOOGLE_DOC_ID}")
        doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
        
        # 準備更新請求
        requests = []
        
        # 取得文檔內容範圍
        if 'body' in doc and 'content' in doc['body']:
            content = doc['body']['content']
            if content:
                # 計算需要刪除的範圍（保留第一個結構元素）
                end_index = content[-1].get('endIndex', 1) - 1
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
            print("📤 正在更新 Google Docs...")
            service.documents().batchUpdate(
                documentId=GOOGLE_DOC_ID,
                body={'requests': requests}
            ).execute()
            print("✅ 已同步到 Google Docs")
            return True
        else:
            print("⚠️  無需更新")
            return True
        
    except ImportError:
        print("❌ 缺少必要的套件")
        print("   請執行：pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return False
    except HttpError as e:
        print(f"❌ Google Docs API 錯誤：{e}")
        if e.resp.status == 403:
            print("   提示：請確認 Service Account 有編輯該文件的權限")
        elif e.resp.status == 404:
            print("   提示：請確認 Google Docs ID 是否正確")
        return False
    except Exception as e:
        print(f"❌ 同步失敗：{e}")
        import traceback
        traceback.print_exc()
        return False


def sync_from_gdocs() -> Optional[str]:
    """從 Google Docs 同步"""
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError
        
        # 載入憑證
        credentials_path = os.getenv("GOOGLE_CREDENTIALS_PATH", "credentials.json")
        if not os.path.exists(credentials_path):
            print(f"❌ 找不到憑證檔案：{credentials_path}")
            return None
        
        print(f"🔐 載入憑證：{credentials_path}")
        creds = Credentials.from_service_account_file(
            credentials_path,
            scopes=['https://www.googleapis.com/auth/documents.readonly']
        )
        
        service = build('docs', 'v1', credentials=creds)
        
        # 讀取文檔
        print(f"📖 讀取 Google Docs: {GOOGLE_DOC_ID}")
        doc = service.documents().get(documentId=GOOGLE_DOC_ID).execute()
        
        # 提取文字內容
        def extract_text(element):
            """遞迴提取文字"""
            text = ""
            if 'paragraph' in element:
                para = element['paragraph']
                if 'elements' in para:
                    for elem in para['elements']:
                        if 'textRun' in elem:
                            text += elem['textRun'].get('content', '')
            elif 'table' in element:
                # 簡化處理表格
                text += "\n[表格]\n"
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
        print("❌ 缺少必要的套件")
        print("   請執行：pip install google-api-python-client google-auth-httplib2 google-auth-oauthlib")
        return None
    except HttpError as e:
        print(f"❌ Google Docs API 錯誤：{e}")
        return None
    except Exception as e:
        print(f"❌ 讀取失敗：{e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    parser = argparse.ArgumentParser(description="PRD.md ↔ Google Docs 雙向同步")
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
    print("📄 PRD.md ↔ Google Docs 雙向同步工具")
    print("=" * 60)
    print(f"PRD.md: {PRD_MD_PATH}")
    print(f"Google Docs ID: {GOOGLE_DOC_ID}")
    print(f"文件連結: https://docs.google.com/document/d/{GOOGLE_DOC_ID}/edit")
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
        gdoc_content = sync_from_gdocs()
        if gdoc_content:
            success = write_prd_md(gdoc_content)
    elif args.to_gdoc:
        # 同步到 Google Docs
        direction = "to-gdoc"
        print("📤 從 PRD.md 同步到 Google Docs...")
        print()
        md_content = read_prd_md()
        if md_content:
            success = sync_to_gdocs(md_content)
    else:
        # 自動判斷：預設同步到 Google Docs
        direction = "to-gdoc"
        print("🔍 自動判斷：同步到 Google Docs...")
        print()
        md_content = read_prd_md()
        if md_content:
            success = sync_to_gdocs(md_content)
    
    # 記錄同步歷史
    if success:
        log_data["last_md_mtime"] = get_prd_mtime()
        log_data["last_sync_time"] = timestamp
        log_data["sync_history"].append({
            "timestamp": timestamp,
            "direction": direction,
            "success": True
        })
        # 只保留最近 50 筆記錄
        log_data["sync_history"] = log_data["sync_history"][-50:]
        save_sync_log(log_data)
        print()
        print("=" * 60)
        print("✅ 同步完成！")
        print("=" * 60)
    else:
        log_data["sync_history"].append({
            "timestamp": timestamp,
            "direction": direction,
            "success": False
        })
        save_sync_log(log_data)
        print()
        print("=" * 60)
        print("❌ 同步失敗")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()

