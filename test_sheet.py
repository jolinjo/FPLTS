#!/usr/bin/env python3
"""
Google Sheets 服務測試腳本
測試連線、讀取和寫入功能
"""
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# 匯入服務
from services.sheet import sheet_service

def test_connection():
    """測試 Google Sheets 連線"""
    print("=" * 50)
    print("測試 1: Google Sheets 連線測試")
    print("=" * 50)
    
    if not sheet_service.client:
        print("❌ 失敗：Google Sheets 客戶端未初始化")
        print("   請檢查：")
        print("   1. credentials.json 檔案是否存在")
        print("   2. GOOGLE_SHEET_ID 是否正確設定")
        print("   3. Service Account 是否有權限存取該 Google Sheets")
        return False
    
    if not sheet_service.sheet_id:
        print("❌ 失敗：未設定 Google Sheet ID")
        return False
    
    print(f"✓ 客戶端已初始化")
    print(f"✓ Sheet ID: {sheet_service.sheet_id}")
    return True

def test_read_sheet():
    """測試讀取 Google Sheets"""
    print("\n" + "=" * 50)
    print("測試 2: 讀取 Google Sheets")
    print("=" * 50)
    
    try:
        spreadsheet = sheet_service.client.open_by_key(sheet_service.sheet_id)
        print(f"✓ 成功開啟 Google Sheets: {spreadsheet.title}")
        
        # 列出所有工作表
        worksheets = spreadsheet.worksheets()
        worksheet_names = [ws.title for ws in worksheets]
        print(f"✓ 可用工作表: {', '.join(worksheet_names)}")
        
        # 檢查 Logs 工作表是否存在
        try:
            worksheet = spreadsheet.worksheet("Logs")
            print(f"✓ 找到 'Logs' 工作表")
            
            # 讀取第一行（標題）
            try:
                headers = worksheet.row_values(1)
                if headers:
                    print(f"✓ 工作表欄位: {', '.join(headers)}")
                else:
                    print("⚠️  警告：工作表第一行為空，可能需要建立標題列")
            except Exception as e:
                print(f"⚠️  警告：無法讀取標題列: {e}")
            
            # 讀取現有資料筆數
            try:
                all_values = worksheet.get_all_values()
                row_count = len(all_values) - 1 if len(all_values) > 1 else 0  # 減去標題列
                print(f"✓ 現有資料筆數: {row_count}")
            except Exception as e:
                print(f"⚠️  警告：無法計算資料筆數: {e}")
            
            return True
        except Exception as e:
            error_msg = str(e)
            if "WorksheetNotFound" in error_msg or "not found" in error_msg.lower():
                print("❌ 失敗：找不到 'Logs' 工作表")
                print(f"   可用工作表: {', '.join(worksheet_names)}")
                print("   請在 Google Sheets 中建立名為 'Logs' 的工作表")
            else:
                print(f"❌ 失敗：無法存取 'Logs' 工作表")
                print(f"   錯誤訊息: {error_msg}")
            return False
            
    except Exception as e:
        error_msg = str(e)
        error_type = type(e).__name__
        print(f"❌ 失敗：無法讀取 Google Sheets")
        print(f"   錯誤類型: {error_type}")
        if error_msg:
            print(f"   錯誤訊息: {error_msg}")
        
        # 檢查是否為權限錯誤
        if error_type == "PermissionError" or "permission" in error_msg.lower() or "PERMISSION_DENIED" in str(e):
            print("\n   ⚠️  權限錯誤：Service Account 沒有存取權限")
            print("\n   📋 解決步驟：")
            # 嘗試讀取 Service Account Email
            try:
                import json
                with open('credentials.json', 'r') as f:
                    cred_data = json.load(f)
                    service_email = cred_data.get('client_email', '')
                    if service_email:
                        print(f"   1. 開啟您的 Google Sheets 文件")
                        print(f"   2. 點擊右上角「共用」按鈕")
                        print(f"   3. 在「新增使用者和群組」欄位輸入以下 Email：")
                        print(f"      {service_email}")
                        print(f"   4. 選擇權限為「編輯者」")
                        print(f"   5. 取消勾選「通知人員」")
                        print(f"   6. 點擊「共用」")
                    else:
                        print(f"   1. 在 Google Sheets 中分享給 Service Account")
                        print(f"   2. Service Account Email 可在 credentials.json 的 client_email 欄位找到")
            except:
                print(f"   1. 在 Google Sheets 中分享給 Service Account")
                print(f"   2. Service Account Email 可在 credentials.json 的 client_email 欄位找到")
        elif "not found" in error_msg.lower():
            print("\n   可能的解決方案：")
            print("   1. 確認 GOOGLE_SHEET_ID 是否正確")
            print("   2. Sheet ID 應從 Google Sheets 網址中取得")
        
        return False

def test_write_sheet():
    """測試寫入 Google Sheets"""
    print("\n" + "=" * 50)
    print("測試 3: 寫入 Google Sheets")
    print("=" * 50)
    
    # 準備測試資料
    test_data = {
        "timestamp": datetime.now(),
        "action": "TEST",
        "operator": "TEST_USER",
        "order": "TEST001",
        "process": "P1",
        "sku": "ST352",
        "container": "A1",
        "box_seq": "99",
        "qty": "0001",
        "status": "G",
        "cycle_time": "0",
        "scanned_barcode": "TEST-BARCODE",
        "new_barcode": ""
    }
    
    try:
        result = sheet_service.write_log(test_data)
        if result:
            print("✓ 成功寫入測試資料")
            print(f"  工單: {test_data['order']}")
            print(f"  動作: {test_data['action']}")
            print(f"  操作員: {test_data['operator']}")
            return True
        else:
            print("❌ 失敗：寫入返回 False")
            print("   請檢查上方的錯誤訊息（如果有）")
            return False
    except Exception as e:
        error_msg = str(e)
        print(f"❌ 失敗：寫入時發生錯誤")
        print(f"   錯誤訊息: {error_msg}")
        
        if "permission" in error_msg.lower() or "access" in error_msg.lower():
            print("\n   可能的解決方案：")
            print("   1. 確認已在 Google Sheets 中分享給 Service Account")
            print("   2. Service Account Email 可在 credentials.json 的 client_email 欄位找到")
        return False

def test_read_after_write():
    """測試寫入後讀取"""
    print("\n" + "=" * 50)
    print("測試 4: 驗證寫入的資料")
    print("=" * 50)
    
    try:
        logs = sheet_service.get_logs_by_order("TEST001", limit=1)
        if logs:
            print("✓ 成功讀取剛才寫入的資料")
            log = logs[0]
            print(f"  工單: {log.get('order')}")
            print(f"  動作: {log.get('action')}")
            print(f"  操作員: {log.get('operator')}")
            return True
        else:
            print("⚠️  警告：無法讀取剛才寫入的資料（可能需要稍等片刻）")
            return False
    except Exception as e:
        print(f"❌ 失敗：讀取時發生錯誤")
        print(f"   錯誤訊息: {e}")
        return False

def main():
    """主測試函數"""
    print("\n" + "=" * 50)
    print("Google Sheets 服務測試")
    print("=" * 50)
    print()
    
    results = []
    
    # 執行測試
    results.append(("連線測試", test_connection()))
    results.append(("讀取測試", test_read_sheet()))
    results.append(("寫入測試", test_write_sheet()))
    results.append(("驗證測試", test_read_after_write()))
    
    # 顯示測試結果摘要
    print("\n" + "=" * 50)
    print("測試結果摘要")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ 通過" if result else "❌ 失敗"
        print(f"{status} - {name}")
    
    print(f"\n總計: {passed}/{total} 測試通過")
    
    if passed == total:
        print("\n🎉 所有測試通過！Google Sheets 服務運作正常。")
        return 0
    else:
        print("\n⚠️  部分測試失敗，請檢查上述錯誤訊息。")
        return 1

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n測試已中斷")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 測試過程中發生未預期的錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

