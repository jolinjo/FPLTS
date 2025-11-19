#!/usr/bin/env python3
"""
設定 Google Sheets 標題列腳本
在 Logs 工作表中建立標準標題列
"""
from services.sheet import sheet_service, COLUMN_HEADERS

def setup_headers():
    """在 Logs 工作表中建立標題列"""
    if not sheet_service.client or not sheet_service.sheet_id:
        print("❌ Google Sheets 客戶端未初始化")
        return False
    
    try:
        spreadsheet = sheet_service.client.open_by_key(sheet_service.sheet_id)
        worksheet = spreadsheet.worksheet("Logs")
        
        # 檢查第一行是否已有標題
        try:
            existing_headers = worksheet.row_values(1)
            if existing_headers and len(existing_headers) > 0:
                print(f"⚠️  工作表第一行已有內容：{existing_headers}")
                print("   是否要覆蓋？(y/n): ", end="")
                response = input().strip().lower()
                if response != 'y':
                    print("   取消操作")
                    return False
        except:
            pass  # 第一行為空，繼續
        
        # 清除第一行並寫入標題（使用帶中文說明的標題）
        worksheet.clear()
        worksheet.append_row(COLUMN_HEADERS)
        
        print("✓ 成功建立標題列")
        print(f"  欄位：{', '.join(COLUMN_HEADERS)}")
        return True
        
    except Exception as e:
        print(f"❌ 設定標題列失敗：{e}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("Google Sheets 標題列設定")
    print("=" * 50)
    print()
    
    if setup_headers():
        print("\n✓ 設定完成！")
    else:
        print("\n❌ 設定失敗")

