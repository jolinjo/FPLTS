/**
 * 前端控制邏輯
 * iOS 風格行動端應用
 */

// 應用狀態
const AppState = {
    operatorId: null,
    currentStationId: null,
    currentMode: null, // 'inbound', 'outbound', 'trace', 'first'
    apiBaseUrl: '', // 使用相對路徑，自動適配
    seriesOptions: [], // 產品線選項
    modelOptions: [],  // 機種選項
    containerOptions: [], // 容器選項
    processOptions: [], // 製程站點選項
    statusOptions: [], // 貨態選項
    currentInboundQty: null // 當前遷出頁面的投入量
};

// 初始化
document.addEventListener('DOMContentLoaded', async () => {
    // 先載入配置選項，再檢查登入狀態
    await loadConfigOptions();
    checkAuth();
    setupEventListeners();
    // 檢查 URL 參數，如果有條碼則自動填入
    checkUrlParams();
});

/**
 * 檢查登入狀態（強制登入機制）
 */
function checkAuth() {
    const operatorId = localStorage.getItem('operatorId');
    const currentStationId = localStorage.getItem('currentStationId');
    
    if (!operatorId || !currentStationId) {
        // 未登入，顯示設定頁
        showSetupPage();
    } else {
        // 已登入，顯示主功能頁
        AppState.operatorId = operatorId;
        AppState.currentStationId = currentStationId;
        showMainPage();
    }
}

/**
 * 顯示設定頁
 */
function showSetupPage() {
    document.getElementById('setupPage').classList.remove('hidden');
    document.getElementById('mainPage').classList.add('hidden');
    
    // 停止主頁面遷入條碼自動更新
    stopMainPageInboundBarcodesUpdate();
    
    // 確保下拉選單已更新（如果選項已載入）
    // 使用 setTimeout 確保 DOM 元素已經可見
    setTimeout(() => {
        if (AppState.processOptions && AppState.processOptions.length > 0) {
            updateProcessSelect();
        } else {
            // 如果選項還沒載入，重新載入
            loadConfigOptions();
        }
    }, 100);
    
    // 載入已儲存的值（如果有的話）
    const savedOperator = localStorage.getItem('operatorId');
    const savedStation = localStorage.getItem('currentStationId');
    
    if (savedOperator) {
        document.getElementById('operatorInput').value = savedOperator;
    }
    // 注意：savedStation 的設置應該在 updateProcessSelect() 之後
    // 所以我們在 updateProcessSelect() 內部處理
}

/**
 * 顯示主功能頁
 */
function showMainPage() {
    document.getElementById('setupPage').classList.add('hidden');
    document.getElementById('mainPage').classList.remove('hidden');
    
    // 更新顯示資訊
    const operatorDisplay = document.getElementById('operatorDisplay');
    if (operatorDisplay) {
        operatorDisplay.textContent = AppState.operatorId || '-';
    }
    updateStationDisplay();
    
    // 檢查操作員是否已設定
    if (!AppState.operatorId || !/^\d{7}$/.test(AppState.operatorId)) {
        // 沒有有效的操作員，禁用所有功能並顯示提示
        disableAllFunctions();
        showMainPageMessage('請先登入操作員（工號必須為7位數字）', 'warning');
        return;
    }
    
    // 有有效的操作員，啟用所有功能
    enableAllFunctions();
    
    // 根據當前站點顯示/隱藏首站遷出按鈕
    updateFirstStationButtonVisibility();
    
    // 更新遷入條碼列表
    updateMainPageInboundBarcodes();
    
    // 啟動自動更新定時器
    startMainPageInboundBarcodesUpdate();
}

/**
 * 打開設定底部工作表（從站點卡片點擊時使用）
 */
function openSetupBottomSheet() {
    const overlay = document.getElementById('bottomSheetOverlay');
    const setupSheet = document.getElementById('setupBottomSheet');
    
    if (!overlay || !setupSheet) {
        console.error('找不到設定底部工作表元素');
        return;
    }
    
    // 更新單選按鈕列表
    updateStationRadioGroup();
    
    // 顯示遮罩和底部工作表
    overlay.classList.add('open');
    setupSheet.classList.add('open');
}

/**
 * 關閉設定底部工作表
 */
function closeSetupBottomSheet() {
    const overlay = document.getElementById('bottomSheetOverlay');
    const setupSheet = document.getElementById('setupBottomSheet');
    
    if (overlay) {
        overlay.classList.remove('open');
    }
    if (setupSheet) {
        setupSheet.classList.remove('open');
    }
}

/**
 * 更新站點單選按鈕列表
 */
function updateStationRadioGroup() {
    const radioGroup = document.getElementById('stationRadioGroup');
    if (!radioGroup) {
        console.error('找不到站點單選按鈕組元素');
        return;
    }
    
    // 檢查是否有選項數據
    if (!AppState.processOptions || AppState.processOptions.length === 0) {
        radioGroup.innerHTML = '<p class="text-small" style="color: var(--ios-text-secondary); padding: 16px;">載入中...</p>';
        return;
    }
    
    // 清空現有內容
    radioGroup.innerHTML = '';
    
    // 獲取當前選中的站點
    const currentStation = localStorage.getItem('currentStationId') || AppState.currentStationId || '';
    
    // 過濾掉 ZZ 製程（新工單），不顯示在選單中
    AppState.processOptions
        .filter(process => process.code.toUpperCase() !== 'ZZ')
        .forEach(process => {
            const radioOption = document.createElement('div');
            radioOption.className = 'radio-option';
            
            const radioId = `stationRadio_${process.code}`;
            const isChecked = process.code === currentStation;
            
            const codeUpper = process.code.toUpperCase();
            const nameUpper = process.name.toUpperCase();
            
            radioOption.innerHTML = `
                <input 
                    type="radio" 
                    id="${radioId}" 
                    name="stationRadio" 
                    value="${process.code}"
                    ${isChecked ? 'checked' : ''}
                >
                <label for="${radioId}">${codeUpper} - ${nameUpper}</label>
            `;
            
            // 為整個選項區域添加點擊事件，確保點擊任何地方都能切換
            radioOption.addEventListener('click', (e) => {
                // 如果點擊的不是 radio 按鈕本身，則觸發 radio 按鈕的點擊
                if (e.target.tagName !== 'INPUT') {
                    const radioInput = radioOption.querySelector('input[type="radio"]');
                    if (radioInput && !radioInput.checked) {
                        radioInput.checked = true;
                        radioInput.dispatchEvent(new Event('change', { bubbles: true }));
                    }
                }
            });
            
            // 為單選按鈕添加 change 事件監聽器，選中後立即保存
            const radioInput = radioOption.querySelector('input[type="radio"]');
            if (radioInput) {
                radioInput.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        saveStationSelection(e.target.value);
                    }
                });
            }
            
            radioGroup.appendChild(radioOption);
        });
    
    if (radioGroup.children.length === 0) {
        radioGroup.innerHTML = '<p class="text-small" style="color: var(--ios-text-secondary); padding: 16px;">暫無可用站點</p>';
    }
}

/**
 * 保存站點選擇（立即生效）
 */
function saveStationSelection(currentStationId) {
    if (!currentStationId) {
        return;
    }
    
    // 儲存到 localStorage
    localStorage.setItem('currentStationId', currentStationId);
    
    // 更新應用狀態
    AppState.currentStationId = currentStationId;
    
    // 更新顯示資訊
    updateStationDisplay();
    
    // 根據當前站點顯示/隱藏首站遷出按鈕
    updateFirstStationButtonVisibility();
    
    // 更新遷入條碼列表
    updateMainPageInboundBarcodes();
    
    // 關閉底部工作表
    closeSetupBottomSheet();
    
    // 顯示成功訊息（包含站點中文名稱，統一轉換為大寫顯示）
    const process = AppState.processOptions.find(p => p.code === currentStationId);
    const stationCodeUpper = currentStationId ? currentStationId.toUpperCase() : '';
    const nameUpper = process ? process.name.toUpperCase() : '';
    const stationDisplay = process ? `${stationCodeUpper} - ${nameUpper}` : stationCodeUpper;
    showSuccess('站點已更新', `當前站點：${stationDisplay}`);
}

/**
 * 更新站點顯示（包含中文名稱）
 */
function updateStationDisplay() {
    const stationDisplay = document.getElementById('stationDisplay');
    const stationDisplayCenter = document.getElementById('stationDisplayCenter');
    
    if (!AppState.currentStationId) {
        return;
    }
    
    // 查找對應的站點名稱（統一轉換為大寫顯示）
    const process = AppState.processOptions.find(p => p.code === AppState.currentStationId);
    const stationCodeUpper = AppState.currentStationId ? AppState.currentStationId.toUpperCase() : '';
    const displayText = process 
        ? `${stationCodeUpper} - ${process.name.toUpperCase()}`
        : stationCodeUpper;
    
    // 更新頂部卡片中的站點顯示
    if (stationDisplay) {
        stationDisplay.textContent = displayText;
    }
    
    // 更新中間的站點顯示
    if (stationDisplayCenter) {
        stationDisplayCenter.textContent = displayText;
    }
}

/**
 * 檢查 URL 參數，如果有條碼則自動填入並開啟遷入功能
 */
function checkUrlParams() {
    const urlParams = new URLSearchParams(window.location.search);
    const barcode = urlParams.get('b'); // 簡化參數名稱
    
    if (barcode) {
        // 如果有條碼參數，保存到 sessionStorage（即使未登入也能保存）
        sessionStorage.setItem('pendingBarcode', barcode);
        
        // 清除 URL 參數，避免重新整理時重複觸發
        const newUrl = window.location.pathname;
        window.history.replaceState({}, document.title, newUrl);
        
        // 如果已經登入，立即處理條碼
        if (AppState.operatorId && AppState.currentStationId) {
            processPendingBarcode();
        }
    } else {
        // 如果 URL 沒有條碼參數，檢查是否有待處理的條碼（從 sessionStorage）
        // 只有在已登入時才處理
        if (AppState.operatorId && AppState.currentStationId) {
            processPendingBarcode();
        }
    }
}

/**
 * 解析條碼，移除所有 - 後按照固定位置解析
 * 條碼格式：工單8碼-製程2碼-SKU5碼-容器2碼-箱號2碼-貨態1碼-數量4碼-校驗3碼
 * 移除 - 後總長度：8+2+5+2+2+1+4+3 = 27碼
 */
function parseBarcode(barcode) {
    // 移除所有 - 符號
    const cleanBarcode = barcode.replace(/-/g, '');
    
    // 按照固定位置解析
    // 工單：0-7 (8碼)
    // 製程：8-9 (2碼)
    // SKU：10-14 (5碼)
    // 容器：15-16 (2碼)
    // 箱號：17-18 (2碼)
    // 貨態：19 (1碼)
    // 數量：20-23 (4碼)
    // 校驗：24-26 (3碼)
    
    if (cleanBarcode.length < 27) {
        // 如果長度不足，嘗試用 split 方式解析（有 - 的情況）
        const parts = barcode.split('-');
        if (parts.length >= 2) {
            return {
                order: parts[0] || '',
                process: parts[1] || '',
                sku: parts[2] || '',
                container: parts[3] || '',
                boxSeq: parts[4] || '',
                status: parts[5] || '',
                qty: parts[6] || '',
                crc: parts[7] || ''
            };
        }
        return null;
    }
    
    return {
        order: cleanBarcode.substring(0, 8),
        process: cleanBarcode.substring(8, 10),
        sku: cleanBarcode.substring(10, 15),
        container: cleanBarcode.substring(15, 17),
        boxSeq: cleanBarcode.substring(17, 19),
        status: cleanBarcode.substring(19, 20),
        qty: cleanBarcode.substring(20, 24),
        crc: cleanBarcode.substring(24, 27)
    };
}

/**
 * 處理待處理的條碼（從 sessionStorage 或 URL 參數）
 * 立即檢查條碼狀態，自動跳轉到對應功能
 */
async function processPendingBarcode() {
    console.log('[processPendingBarcode] 開始執行');
    const pendingBarcode = sessionStorage.getItem('pendingBarcode');
    console.log('[processPendingBarcode] 待處理條碼：', pendingBarcode);
    console.log('[processPendingBarcode] 操作員ID：', AppState.operatorId);
    console.log('[processPendingBarcode] 當前站點：', AppState.currentStationId);
    
    if (pendingBarcode && AppState.operatorId && AppState.currentStationId) {
        console.log('[processPendingBarcode] 條件滿足，開始處理條碼');
        // 清除待處理的條碼
        sessionStorage.removeItem('pendingBarcode');
        
        // 清理條碼（移除可能的 b= 前綴）
        let cleanBarcode = pendingBarcode.trim();
        if (cleanBarcode.startsWith('b=')) {
            cleanBarcode = cleanBarcode.substring(2);
        }
        console.log('[processPendingBarcode] 清理後的條碼：', cleanBarcode);
        
        // 顯示處理動畫（URL 帶入條碼時）
        showProcessing('讀取中...', '正在檢查條碼狀態');
        
        // 立即檢查條碼狀態
        try {
            const response = await fetch('/api/scan/check', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    barcode: cleanBarcode,
                    current_station_id: AppState.currentStationId
                })
            });
            
            if (!response.ok) {
                // API 請求失敗（可能是速率限制或其他錯誤）
                throw new Error(`API 請求失敗：${response.status}`);
            }
            
            const data = await response.json();
            console.log('[processPendingBarcode] API 響應：', data);
            
            if (data.success && data.suggested_action) {
                console.log('[processPendingBarcode] 建議操作：', data.suggested_action);
                const action = data.suggested_action;
                console.log('[processPendingBarcode] 執行操作：', action);
                
                // 立即處理，不需要延遲
                if (action === 'first') {
                        // 隱藏處理動畫（檢查完成，準備開啟工作表）
                        hideProcessing();
                        // 首站遷出
                        openBottomSheet('first', '首站遷出');
                        // 如果有工單號，自動填入
                        if (data.data && data.data.order) {
                            setTimeout(() => {
                                const orderInput = document.getElementById('orderInput');
                                if (orderInput) {
                                    let orderValue = data.data.order.replace(/^0+/, '');
                                    orderInput.value = orderValue || data.data.order;
                                    orderInput.focus();
                                }
                                // 如果有產品線和機種，自動填入
                                if (data.data.series_code && data.data.model_code) {
                                    const seriesSelect = document.getElementById('seriesSelect');
                                    const modelSelect = document.getElementById('modelSelect');
                                    if (seriesSelect) {
                                        seriesSelect.value = data.data.series_code;
                                    }
                                    if (modelSelect) {
                                        // 處理前導零（例如：001 和 1）
                                        const modelCode = data.data.model_code.replace(/^0+/, '') || data.data.model_code;
                                        // 嘗試匹配機種代碼
                                        for (let option of modelSelect.options) {
                                            if (option.value === data.data.model_code || 
                                                option.value === modelCode ||
                                                option.value.replace(/^0+/, '') === modelCode) {
                                                modelSelect.value = option.value;
                                                break;
                                            }
                                        }
                                    }
                                }
                            }, 350);
                        }
                    } else if (action === 'outbound') {
                        console.log('[processPendingBarcode] 執行遷出操作，條碼：', cleanBarcode);
                        // 隱藏處理動畫（檢查完成，準備開啟工作表）
                        hideProcessing();
                        // 遷出 - 立即打開，不延遲
                        console.log('[processPendingBarcode] 準備打開遷出工作表');
                        openBottomSheet('outbound', '貨物遷出', cleanBarcode);
                        console.log('[processPendingBarcode] 已調用 openBottomSheet');
                    } else if (action === 'trace') {
                        // 只允許查詢（直接執行查詢，不顯示提示）
                        // 更新處理動畫訊息（繼續顯示，不隱藏）
                        showProcessing('查詢中...', '正在查詢追溯記錄');
                        // 直接執行查詢
                        setTimeout(() => {
                            const barcodeInput = document.getElementById('barcodeInput');
                            if (barcodeInput) {
                                barcodeInput.value = cleanBarcode;
                            }
                            handleTrace();
                        }, 300);
                    } else if (action === 'inbound' || !action) {
                        // 遷入操作：查詢相同工單的上一站條碼，然後直接進入遷入功能
                        // 繼續顯示處理動畫，查詢上一站條碼
                        showProcessing('查詢中...', '正在查詢相同工單的上一站條碼');
                        
                        // 解析條碼取得工單號
                        const parsed = parseBarcode(cleanBarcode);
                        if (parsed && parsed.order) {
                            const order = parsed.order.replace(/^0+/, '') || parsed.order;
                            
                            // 查詢上一站條碼
                            fetch(`/api/scan/previous-barcodes?order=${encodeURIComponent(order)}&current_station_id=${encodeURIComponent(AppState.currentStationId)}`)
                                .then(queryResponse => {
                                    if (!queryResponse.ok) {
                                        throw new Error('查詢上一站條碼失敗');
                                    }
                                    return queryResponse.json();
                                })
                                .then(queryData => {
                                    // 隱藏處理動畫
                                    hideProcessing();
                                    
                                    // 準備條碼列表（包含掃描的條碼）
                                    let barcodesToShow = [];
                                    
                                    // 如果有上一站條碼，添加到列表
                                    if (queryData.success && queryData.data && queryData.data.length > 0) {
                                        barcodesToShow = [...queryData.data];
                                        
                                        // 檢查掃描的條碼是否也在列表中
                                        const scannedBarcodeInList = barcodesToShow.some(item => item.barcode === cleanBarcode);
                                        
                                        // 如果掃描的條碼不在列表中，添加到列表開頭
                                        if (!scannedBarcodeInList) {
                                            if (parsed) {
                                                barcodesToShow.unshift({
                                                    barcode: cleanBarcode,
                                                    box_seq: parsed.box_seq || '',
                                                    qty: parsed.qty || '',
                                                    status: parsed.status || '',
                                                    container: parsed.container || '',
                                                    process: parsed.process || ''
                                                });
                                            }
                                        }
                                    } else {
                                        // 沒有上一站條碼，只顯示掃描的條碼
                                        if (parsed) {
                                            barcodesToShow = [{
                                                barcode: cleanBarcode,
                                                box_seq: parsed.box_seq || '',
                                                qty: parsed.qty || '',
                                                status: parsed.status || '',
                                                container: parsed.container || '',
                                                process: parsed.process || ''
                                            }];
                                        }
                                    }
                                    
                                    // 打開遷入底部工作表（隱藏輸入框和提交按鈕）
                                    openBottomSheet('inbound', '貨物遷入', cleanBarcode, true);
                                    
                                    // 直接顯示條碼選擇列表（預設全選）
                                    setTimeout(() => {
                                        if (barcodesToShow.length > 0) {
                                            showBarcodeSelection(barcodesToShow, cleanBarcode, async (selectedBarcodesList) => {
                                                // 使用者確認選擇後，執行批量遷入
                                                await performInbound(selectedBarcodesList);
                                            });
                                        }
                                    }, 100);
                                })
                                .catch(error => {
                                    console.error('查詢上一站條碼失敗：', error);
                                    // 查詢失敗，仍然打開遷入工作表
                                    hideProcessing();
                                    openBottomSheet('inbound', '貨物遷入', cleanBarcode);
                                });
                        } else {
                            // 無法解析條碼，直接打開遷入工作表
                            hideProcessing();
                            openBottomSheet('inbound', '貨物遷入', cleanBarcode);
                        }
                    } else {
                        // 其他情況，隱藏處理動畫並預設開啟遷入
                        hideProcessing();
                        openBottomSheet('inbound', '貨物遷入', cleanBarcode);
                    }
            } else {
                // 檢查失敗，隱藏處理動畫並預設開啟遷入
                console.warn('[processPendingBarcode] API 響應格式不正確或沒有 suggested_action：', data);
                hideProcessing();
                setTimeout(() => {
                    openBottomSheet('inbound', '貨物遷入');
                    setTimeout(() => {
                        const barcodeInput = document.getElementById('barcodeInput');
                        if (barcodeInput) {
                            barcodeInput.value = cleanBarcode;
                            barcodeInput.focus();
                        }
                    }, 350);
                }, 500);
            }
        } catch (error) {
            // 隱藏處理動畫（發生錯誤）
            hideProcessing();
            console.error('檢查條碼失敗：', error);
            showAlert('錯誤', '處理條碼時發生錯誤', 'error');
            
            // 檢查失敗，嘗試查詢相同工單的上一站條碼，然後開啟遷入
            const parsed = parseBarcode(cleanBarcode);
            if (parsed && parsed.order) {
                const order = parsed.order.replace(/^0+/, '') || parsed.order;
                
                // 顯示處理動畫，查詢上一站條碼
                showProcessing('查詢中...', '正在查詢相同工單的上一站條碼');
                
                // 查詢上一站條碼
                fetch(`/api/scan/previous-barcodes?order=${encodeURIComponent(order)}&current_station_id=${encodeURIComponent(AppState.currentStationId)}`)
                    .then(queryResponse => {
                        if (!queryResponse.ok) {
                            throw new Error('查詢上一站條碼失敗');
                        }
                        return queryResponse.json();
                    })
                    .then(queryData => {
                        // 隱藏處理動畫
                        hideProcessing();
                        
                        // 打開遷入底部工作表
                        openBottomSheet('inbound', '貨物遷入', cleanBarcode);
                        
                        // 隱藏條碼輸入框和提交按鈕（URL 帶入時不需要）
                        setTimeout(() => {
                            const barcodeInput = document.getElementById('barcodeInput');
                            const submitBtn = document.getElementById('submitBtn');
                            if (barcodeInput) {
                                barcodeInput.style.display = 'none';
                            }
                            if (submitBtn) {
                                submitBtn.style.display = 'none';
                            }
                            
                            // 準備條碼列表（包含掃描的條碼）
                            let barcodesToShow = [];
                            
                            // 如果有上一站條碼，添加到列表
                            if (queryData.success && queryData.data && queryData.data.length > 0) {
                                barcodesToShow = [...queryData.data];
                                
                                // 檢查掃描的條碼是否也在列表中
                                const scannedBarcodeInList = barcodesToShow.some(item => item.barcode === cleanBarcode);
                                
                                // 如果掃描的條碼不在列表中，添加到列表開頭
                                if (!scannedBarcodeInList) {
                                    if (parsed) {
                                        barcodesToShow.unshift({
                                            barcode: cleanBarcode,
                                            box_seq: parsed.box_seq || '',
                                            qty: parsed.qty || '',
                                            status: parsed.status || '',
                                            container: parsed.container || '',
                                            process: parsed.process || ''
                                        });
                                    }
                                }
                            } else {
                                // 沒有上一站條碼，只顯示掃描的條碼
                                if (parsed) {
                                    barcodesToShow = [{
                                        barcode: cleanBarcode,
                                        box_seq: parsed.box_seq || '',
                                        qty: parsed.qty || '',
                                        status: parsed.status || '',
                                        container: parsed.container || '',
                                        process: parsed.process || ''
                                    }];
                                }
                            }
                            
                            // 直接顯示條碼選擇列表（預設全選）
                            if (barcodesToShow.length > 0) {
                                showBarcodeSelection(barcodesToShow, cleanBarcode, async (selectedBarcodesList) => {
                                    // 使用者確認選擇後，執行批量遷入
                                    await performInbound(selectedBarcodesList);
                                });
                            }
                        }, 100);
                    })
                    .catch(err => {
                        console.error('查詢上一站條碼失敗：', err);
                        // 查詢失敗，仍然打開遷入工作表
                        hideProcessing();
                        openBottomSheet('inbound', '貨物遷入', cleanBarcode);
                    });
            } else {
                // 無法解析條碼，直接打開遷入工作表
                openBottomSheet('inbound', '貨物遷入', cleanBarcode);
            }
        }
    }
}

/**
 * 設定事件監聽器
 */
function setupEventListeners() {
    // 設定頁
    const saveSetupBtn = document.getElementById('saveSetupBtn');
    if (saveSetupBtn) {
        saveSetupBtn.addEventListener('click', saveSetup);
    }
    
    // 主功能頁
    // 站點卡片點擊進入設定（使用底部工作表）
    const stationCard = document.getElementById('stationCard');
    if (stationCard) {
        stationCard.addEventListener('click', () => {
            openSetupBottomSheet();
        });
    }
    
    // 關閉設定底部工作表按鈕
    const closeSetupSheetBtn = document.getElementById('closeSetupSheetBtn');
    if (closeSetupSheetBtn) {
        closeSetupSheetBtn.addEventListener('click', closeSetupBottomSheet);
    }
    
    // 操作者卡片點擊進入設定（使用底部工作表）
    const operatorCard = document.getElementById('operatorCard');
    if (operatorCard) {
        operatorCard.addEventListener('click', () => {
            openOperatorBottomSheet();
        });
    }
    
    // 關閉操作者設定底部工作表按鈕
    const closeOperatorSheetBtn = document.getElementById('closeOperatorSheetBtn');
    if (closeOperatorSheetBtn) {
        closeOperatorSheetBtn.addEventListener('click', closeOperatorBottomSheet);
    }
    
    // 操作者設定底部工作表儲存按鈕
    const saveOperatorBtn = document.getElementById('saveOperatorBtn');
    if (saveOperatorBtn) {
        saveOperatorBtn.addEventListener('click', saveOperatorSetup);
    }
    
    // 操作者設定底部工作表工號輸入自動轉大寫
    const operatorInputBottom = document.getElementById('operatorInputBottom');
    if (operatorInputBottom) {
        operatorInputBottom.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    }
    
    const inboundBtn = document.getElementById('inboundBtn');
    if (inboundBtn) {
        inboundBtn.addEventListener('click', () => {
            // 如果按鈕被禁用，不執行操作
            if (inboundBtn.disabled) {
                return;
            }
            // 檢查操作員是否已登入
            if (!checkOperatorLogin()) {
                return;
            }
            openBottomSheet('inbound', '貨物遷入');
        });
    }
    
    const outboundBtn = document.getElementById('outboundBtn');
    if (outboundBtn) {
        outboundBtn.addEventListener('click', () => {
            // 如果按鈕被禁用，不執行操作
            if (outboundBtn.disabled) {
                return;
            }
            // 檢查操作員是否已登入
            if (!checkOperatorLogin()) {
                return;
            }
            openBottomSheet('outbound', '貨物遷出');
        });
    }
    
    const traceBtn = document.getElementById('traceBtn');
    if (traceBtn) {
        traceBtn.addEventListener('click', () => {
            // 如果按鈕被禁用，不執行操作
            if (traceBtn.disabled) {
                return;
            }
            // 檢查操作員是否已登入
            if (!checkOperatorLogin()) {
                return;
            }
            openBottomSheet('trace', '追溯查詢');
        });
    }
    
    const firstBtn = document.getElementById('firstBtn');
    if (firstBtn) {
        firstBtn.addEventListener('click', () => {
            // 如果按鈕被禁用，不執行操作
            if (firstBtn.disabled) {
                return;
            }
            // 檢查操作員是否已登入
            if (!checkOperatorLogin()) {
                return;
            }
            openBottomSheet('first', '首站遷出');
        });
    }
    
    // 底部工作表
    const closeSheetBtn = document.getElementById('closeSheetBtn');
    if (closeSheetBtn) {
        closeSheetBtn.addEventListener('click', closeBottomSheet);
    }
    
    // 背景遮罩點擊關閉（處理所有底部工作表）
    const bottomSheetOverlay = document.getElementById('bottomSheetOverlay');
    if (bottomSheetOverlay) {
        bottomSheetOverlay.addEventListener('click', (e) => {
            // 檢查是否有設定工作表打開
            const setupSheet = document.getElementById('setupBottomSheet');
            const operatorSheet = document.getElementById('operatorBottomSheet');
            if (setupSheet && setupSheet.classList.contains('open')) {
                closeSetupBottomSheet();
            } else if (operatorSheet && operatorSheet.classList.contains('open')) {
                closeOperatorBottomSheet();
            } else {
                // 否則關閉其他底部工作表
                closeBottomSheet();
            }
        });
    }
    
    // 阻止底部工作表內部的點擊事件冒泡到遮罩
    const bottomSheet = document.getElementById('bottomSheet');
    if (bottomSheet) {
        bottomSheet.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }
    
    // 追溯結果頁面關閉按鈕
    const closeTracePageBtn = document.getElementById('closeTracePageBtn');
    if (closeTracePageBtn) {
        closeTracePageBtn.addEventListener('click', closeTracePage);
    }
    
    const submitBtn = document.getElementById('submitBtn');
    if (submitBtn) {
        submitBtn.addEventListener('click', handleSubmit);
    }
    
    // 警示視窗
    const alertOkBtn = document.getElementById('alertOkBtn');
    if (alertOkBtn) {
        alertOkBtn.addEventListener('click', closeAlert);
    }
    
    // QR Code 關閉按鈕
    const closeQrcodeBtn = document.getElementById('closeQrcodeBtn');
    if (closeQrcodeBtn) {
        closeQrcodeBtn.addEventListener('click', closeQRCodeModal);
    }
    
    // QR Code 彈出視窗背景點擊關閉
    const qrcodeOverlay = document.getElementById('qrcodeOverlay');
    if (qrcodeOverlay) {
        qrcodeOverlay.addEventListener('click', (e) => {
            if (e.target === qrcodeOverlay) {
                closeQRCodeModal();
            }
        });
    }
    
    // 條碼選擇彈出視窗背景點擊關閉
    const barcodeSelectionOverlay = document.getElementById('barcodeSelectionOverlay');
    if (barcodeSelectionOverlay) {
        barcodeSelectionOverlay.addEventListener('click', (e) => {
            if (e.target === barcodeSelectionOverlay) {
                barcodeSelectionOverlay.classList.add('hidden');
            }
        });
    }
    
    // 條碼輸入框事件監聽
    const barcodeInput = document.getElementById('barcodeInput');
    if (barcodeInput) {
        // Enter 鍵提交
        barcodeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    });
        
        // 輸入完成後自動檢查條碼（僅在掃描模式下）
        // 延遲 500ms，避免每次輸入都檢查
        let checkTimeout = null;
        barcodeInput.addEventListener('input', (e) => {
            // 只在掃描模式下自動檢查
            if (AppState.currentMode !== 'scan') {
                return;
            }
            
            const barcode = e.target.value.trim();
            
            // 清除之前的定時器
            if (checkTimeout) {
                clearTimeout(checkTimeout);
            }
            
            // 如果條碼長度足夠（至少 20 個字符），延遲檢查
            if (barcode.length >= 20) {
                checkTimeout = setTimeout(() => {
                    checkBarcodeAndSwitch(barcode);
                }, 500);
            }
        });
    }
    
    // 工單號輸入框自動轉換為大寫
    const orderInput = document.getElementById('orderInput');
    if (orderInput) {
        orderInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    }
}

/**
 * 儲存設定（從全屏設定頁面）
 */
function saveSetup() {
    const operatorId = document.getElementById('operatorInput').value.trim();
    const currentStationId = document.getElementById('stationSelect').value;
    
    if (!operatorId) {
        showAlert('錯誤', '請輸入工號', 'error');
        return;
    }
    
    if (!currentStationId) {
        showAlert('錯誤', '請選擇當前站點', 'error');
        return;
    }
    
    // 儲存到 localStorage
    localStorage.setItem('operatorId', operatorId);
    localStorage.setItem('currentStationId', currentStationId);
    
    // 更新應用狀態
    AppState.operatorId = operatorId;
    AppState.currentStationId = currentStationId;
    
    // 顯示主功能頁
    showMainPage();
    
    // 顯示成功訊息（包含站點中文名稱，統一轉換為大寫顯示）
    const process = AppState.processOptions.find(p => p.code === currentStationId);
    const stationCodeUpper = currentStationId ? currentStationId.toUpperCase() : '';
    const nameUpper = process ? process.name.toUpperCase() : '';
    const stationDisplay = process ? `${stationCodeUpper} - ${nameUpper}` : stationCodeUpper;
    showSuccess('設定已儲存', `操作員：${operatorId}，站點：${stationDisplay}`);
    
    // 檢查是否有待處理的條碼（從 QR code 掃描）
    processPendingBarcode();
}

/**
 * 打開操作者設定底部工作表
 */
function openOperatorBottomSheet() {
    const overlay = document.getElementById('bottomSheetOverlay');
    const operatorSheet = document.getElementById('operatorBottomSheet');
    
    if (!overlay || !operatorSheet) {
        console.error('找不到操作者設定底部工作表元素');
        return;
    }
    
    // 載入已儲存的值
    const savedOperator = localStorage.getItem('operatorId');
    const operatorInput = document.getElementById('operatorInputBottom');
    if (operatorInput) {
        operatorInput.value = savedOperator || '';
    }
    
    // 顯示遮罩和底部工作表
    overlay.classList.add('open');
    operatorSheet.classList.add('open');
}

/**
 * 關閉操作者設定底部工作表
 */
function closeOperatorBottomSheet() {
    const overlay = document.getElementById('bottomSheetOverlay');
    const operatorSheet = document.getElementById('operatorBottomSheet');
    
    if (overlay) {
        overlay.classList.remove('open');
    }
    if (operatorSheet) {
        operatorSheet.classList.remove('open');
    }
}

/**
 * 儲存操作者設定
 */
function saveOperatorSetup() {
    const operatorInput = document.getElementById('operatorInputBottom');
    const operatorId = operatorInput ? operatorInput.value.trim() : '';
    
    if (!operatorId) {
        showAlert('錯誤', '請輸入工號', 'error');
        return;
    }
    
    // 驗證工號必須為7位數字
    if (!/^\d{7}$/.test(operatorId)) {
        showAlert('錯誤', '工號必須為7位數字（例如：1810002）', 'error');
        return;
    }
    
    // 儲存到 localStorage
    localStorage.setItem('operatorId', operatorId);
    
    // 更新應用狀態
    AppState.operatorId = operatorId;
    
    // 更新顯示資訊
    const operatorDisplay = document.getElementById('operatorDisplay');
    if (operatorDisplay) {
        operatorDisplay.textContent = operatorId;
    }
    
    // 啟用所有功能
    enableAllFunctions();
    
    // 關閉底部工作表
    closeOperatorBottomSheet();
    
    // 顯示成功訊息
    showSuccess('設定已儲存', `操作員：${operatorId}`);
}

/**
 * 禁用所有功能按鈕（當沒有操作員時）
 */
function disableAllFunctions() {
    const inboundBtn = document.getElementById('inboundBtn');
    const outboundBtn = document.getElementById('outboundBtn');
    const firstBtn = document.getElementById('firstBtn');
    const traceBtn = document.getElementById('traceBtn');
    
    if (inboundBtn) {
        inboundBtn.disabled = true;
        inboundBtn.style.opacity = '0.5';
        inboundBtn.style.cursor = 'not-allowed';
        inboundBtn.style.pointerEvents = 'none';
        inboundBtn.onmouseover = null;
        inboundBtn.onmouseout = null;
    }
    if (outboundBtn) {
        outboundBtn.disabled = true;
        outboundBtn.style.opacity = '0.5';
        outboundBtn.style.cursor = 'not-allowed';
        outboundBtn.style.pointerEvents = 'none';
        outboundBtn.onmouseover = null;
        outboundBtn.onmouseout = null;
    }
    if (firstBtn) {
        firstBtn.disabled = true;
        firstBtn.style.opacity = '0.5';
        firstBtn.style.cursor = 'not-allowed';
        firstBtn.style.pointerEvents = 'none';
        firstBtn.onmouseover = null;
        firstBtn.onmouseout = null;
    }
    if (traceBtn) {
        traceBtn.disabled = true;
        traceBtn.style.opacity = '0.5';
        traceBtn.style.cursor = 'not-allowed';
        traceBtn.style.pointerEvents = 'none';
    }
}

/**
 * 啟用所有功能按鈕（當有操作員時）
 */
function enableAllFunctions() {
    const inboundBtn = document.getElementById('inboundBtn');
    const outboundBtn = document.getElementById('outboundBtn');
    const firstBtn = document.getElementById('firstBtn');
    const traceBtn = document.getElementById('traceBtn');
    
    if (inboundBtn) {
        inboundBtn.disabled = false;
        inboundBtn.style.opacity = '1';
        inboundBtn.style.cursor = 'pointer';
        inboundBtn.style.pointerEvents = 'auto';
    }
    if (outboundBtn) {
        outboundBtn.disabled = false;
        outboundBtn.style.opacity = '1';
        outboundBtn.style.cursor = 'pointer';
        outboundBtn.style.pointerEvents = 'auto';
    }
    if (firstBtn) {
        firstBtn.disabled = false;
        firstBtn.style.opacity = '1';
        firstBtn.style.cursor = 'pointer';
        firstBtn.style.pointerEvents = 'auto';
    }
    if (traceBtn) {
        traceBtn.disabled = false;
        traceBtn.style.opacity = '1';
        traceBtn.style.cursor = 'pointer';
        traceBtn.style.pointerEvents = 'auto';
    }
}

/**
 * 檢查操作員是否已登入
 */
function checkOperatorLogin() {
    if (!AppState.operatorId || !/^\d{7}$/.test(AppState.operatorId)) {
        showMainPageMessage('請先登入操作員（工號必須為7位數字）', 'warning');
        return false;
    }
    return true;
}

/**
 * 根據當前站點更新首站遷出和貨物遷出按鈕的顯示/隱藏
 * 只有 P1 站才顯示首站遷出功能，其他站點顯示貨物遷出
 * 兩個按鈕同時只會出現一種
 * P1 站點時，遷入按鈕會被禁用（不隱藏）
 */
function updateFirstStationButtonVisibility() {
    const firstBtn = document.getElementById('firstBtn');
    const outboundBtn = document.getElementById('outboundBtn');
    const inboundBtn = document.getElementById('inboundBtn');
    
    if (!firstBtn || !outboundBtn || !inboundBtn) {
        return;
    }
    
    // 檢查當前站點是否為 P1
    const isP1 = AppState.currentStationId && AppState.currentStationId.toUpperCase() === 'P1';
    
    if (isP1) {
        // P1 站：顯示首站遷出按鈕，隱藏貨物遷出按鈕
        firstBtn.style.display = 'flex';
        outboundBtn.style.display = 'none';
        // P1 站：禁用遷入按鈕（不隱藏）
        inboundBtn.disabled = true;
        inboundBtn.style.opacity = '0.5';
        inboundBtn.style.cursor = 'not-allowed';
    } else {
        // 其他站點：隱藏首站遷出按鈕，顯示貨物遷出按鈕
        firstBtn.style.display = 'none';
        outboundBtn.style.display = 'flex';
        // 其他站點：啟用遷入按鈕
        inboundBtn.disabled = false;
        inboundBtn.style.opacity = '1';
        inboundBtn.style.cursor = 'pointer';
    }
}

/**
 * 載入設定選項（產品線、機種、容器和製程站點）
 * 返回 Promise，確保載入完成
 */
async function loadConfigOptions() {
    const errors = [];
    
    try {
        // 載入產品線選項
        try {
        const seriesResponse = await fetch('/api/config/series');
            if (seriesResponse.ok) {
        const seriesData = await seriesResponse.json();
        if (seriesData.success) {
            AppState.seriesOptions = seriesData.data;
            updateSeriesSelect();
                } else {
                    errors.push('產品線選項載入失敗');
                }
            } else {
                errors.push(`產品線 API 錯誤：${seriesResponse.status}`);
            }
        } catch (error) {
            console.error('載入產品線選項失敗：', error);
            errors.push('產品線選項載入失敗');
        }
        
        // 載入機種選項
        try {
        const modelResponse = await fetch('/api/config/models');
            if (modelResponse.ok) {
        const modelData = await modelResponse.json();
        if (modelData.success) {
            AppState.modelOptions = modelData.data;
            updateModelSelect();
                } else {
                    errors.push('機種選項載入失敗');
                }
            } else {
                errors.push(`機種 API 錯誤：${modelResponse.status}`);
            }
        } catch (error) {
            console.error('載入機種選項失敗：', error);
            errors.push('機種選項載入失敗');
        }
        
        // 載入容器選項
        try {
        const containerResponse = await fetch('/api/config/containers');
            if (containerResponse.ok) {
        const containerData = await containerResponse.json();
        if (containerData.success) {
            AppState.containerOptions = containerData.data;
                    console.log('載入容器選項成功：', AppState.containerOptions);
            updateContainerSelects();
                } else {
                    console.error('載入容器選項失敗：', containerData);
                    errors.push('容器選項載入失敗');
                }
            } else {
                errors.push(`容器 API 錯誤：${containerResponse.status}`);
        }
    } catch (error) {
            console.error('載入容器選項失敗：', error);
            errors.push('容器選項載入失敗');
        }
        
        // 載入製程站點選項（最重要，必須成功）
        try {
            const processResponse = await fetch('/api/config/processes');
            if (processResponse.ok) {
                const processData = await processResponse.json();
                if (processData.success) {
                    AppState.processOptions = processData.data;
                    console.log('載入製程站點選項成功：', AppState.processOptions);
                    updateProcessSelect();
                    // 更新主頁面顯示（如果已經登入）
                    if (AppState.currentStationId) {
                        updateStationDisplay();
                    }
                } else {
                    console.error('載入製程站點選項失敗：', processData);
                    errors.push('製程站點選項載入失敗');
                    // 製程站點載入失敗是嚴重錯誤，顯示提示
                    showAlert('錯誤', '無法載入站點選項，請檢查網路連線或重新整理頁面', 'error');
                }
            } else {
                console.error(`製程站點 API 錯誤：${processResponse.status}`);
                errors.push(`製程站點 API 錯誤：${processResponse.status}`);
                showAlert('錯誤', `無法連接到伺服器（錯誤碼：${processResponse.status}），請檢查後端服務是否運行`, 'error');
            }
        } catch (error) {
            console.error('載入製程站點選項失敗：', error);
            errors.push('製程站點選項載入失敗');
            // 網路錯誤或連接失敗
            const errorMessage = error.message || '未知錯誤';
            if (errorMessage.includes('fetch') || errorMessage.includes('Failed to fetch')) {
                showAlert('錯誤', '無法連接到伺服器，請檢查後端服務是否運行在 http://localhost:8000', 'error');
            } else {
                showAlert('錯誤', `載入站點選項失敗：${errorMessage}`, 'error');
            }
        }
        
        // 如果有其他錯誤（非製程站點），只在控制台記錄
        if (errors.length > 0) {
            console.warn('載入設定選項時發生部分錯誤：', errors);
        }
    } catch (error) {
        console.error('載入設定選項時發生未預期的錯誤：', error);
        showAlert('錯誤', `載入設定選項失敗：${error.message || '未知錯誤'}`, 'error');
    }
}

/**
 * 更新產品線下拉選單
 */
function updateSeriesSelect() {
    const select = document.getElementById('seriesSelect');
    // 保留第一個選項（請選擇產品線）
    select.innerHTML = '<option value="">請選擇產品線</option>';
    
    // 添加所有產品線選項（統一轉換為大寫顯示）
    AppState.seriesOptions.forEach(series => {
        const option = document.createElement('option');
        option.value = series.code;
        const codeUpper = series.code.toUpperCase();
        const nameUpper = series.name.toUpperCase();
        option.textContent = `${codeUpper} - ${nameUpper}`;
        select.appendChild(option);
    });
}

/**
 * 更新機種下拉選單
 */
function updateModelSelect() {
    const select = document.getElementById('modelSelect');
    // 保留第一個選項（請選擇機種）
    select.innerHTML = '<option value="">請選擇機種</option>';
    
    // 添加所有機種選項（統一轉換為大寫顯示）
    AppState.modelOptions.forEach(model => {
        const option = document.createElement('option');
        option.value = model.code;
        const codeUpper = model.code.toUpperCase();
        const nameUpper = model.name.toUpperCase();
        option.textContent = `${codeUpper} - ${nameUpper}`;
        select.appendChild(option);
    });
}

/**
 * 更新容器下拉選單（遷出和首站遷出）
 * 遷出功能現在有兩個容器選擇：良品和不良品
 */
function updateContainerSelects() {
    // 檢查是否有選項數據
    if (!AppState.containerOptions || AppState.containerOptions.length === 0) {
        console.warn('容器選項為空，無法更新下拉選單');
        return;
    }
    
    // 更新遷出良品容器選單
    const goodContainerSelect = document.getElementById('goodContainerSelect');
    if (goodContainerSelect) {
        goodContainerSelect.innerHTML = '<option value="">請選擇容器</option>';
        AppState.containerOptions.forEach(container => {
            const option = document.createElement('option');
            option.value = container.code;
            const codeUpper = container.code.toUpperCase();
            const displayText = container.name || (container.capacity > 0 ? `容量 ${container.capacity}` : '自訂');
            option.textContent = `${codeUpper} - ${displayText}`;
            goodContainerSelect.appendChild(option);
        });
    }
    
    // 更新遷出不良品容器選單
    const badContainerSelect = document.getElementById('badContainerSelect');
    if (badContainerSelect) {
        badContainerSelect.innerHTML = '<option value="">請選擇容器</option>';
        AppState.containerOptions.forEach(container => {
            const option = document.createElement('option');
            option.value = container.code;
            const codeUpper = container.code.toUpperCase();
            const displayText = container.name || (container.capacity > 0 ? `容量 ${container.capacity}` : '自訂');
            option.textContent = `${codeUpper} - ${displayText}`;
            badContainerSelect.appendChild(option);
        });
    }
    
    // 保留舊的 containerSelect（向後兼容）
    const outboundSelect = document.getElementById('containerSelect');
    if (outboundSelect) {
        outboundSelect.innerHTML = '<option value="">請選擇容器</option>';
        AppState.containerOptions.forEach(container => {
            const option = document.createElement('option');
            option.value = container.code;
            const codeUpper = container.code.toUpperCase();
            const displayText = container.name || (container.capacity > 0 ? `容量 ${container.capacity}` : '自訂');
            option.textContent = `${codeUpper} - ${displayText}`;
            outboundSelect.appendChild(option);
        });
    }
    
    // 更新首站遷出容器選單
    const firstSelect = document.getElementById('firstContainerSelect');
    if (firstSelect) {
        firstSelect.innerHTML = '<option value="">請選擇容器</option>';
        AppState.containerOptions.forEach(container => {
            const option = document.createElement('option');
            option.value = container.code;
            const codeUpper = container.code.toUpperCase();
            // 使用 name 顯示，如果沒有 name 則使用 capacity
            const displayText = container.name || (container.capacity > 0 ? `容量 ${container.capacity}` : '自訂');
            option.textContent = `${codeUpper} - ${displayText}`;
            firstSelect.appendChild(option);
        });
        console.log(`已更新首站遷出容器選單，共 ${firstSelect.options.length - 1} 個選項`);
    } else {
        console.warn('找不到首站遷出容器選單元素');
    }
}

/**
 * 更新製程站點下拉選單
 */
function updateProcessSelect() {
    const select = document.getElementById('stationSelect');
    if (!select) {
        console.warn('找不到站點下拉選單元素');
        return;
    }
    
    // 檢查是否有選項數據
    if (!AppState.processOptions || AppState.processOptions.length === 0) {
        console.warn('製程站點選項為空，無法更新下拉選單');
        return;
    }
    
    // 保留第一個選項（請選擇站點）
    select.innerHTML = '<option value="">請選擇站點</option>';
    
    // 添加所有站點選項（統一轉換為大寫顯示）
    // 過濾掉 ZZ 製程（新工單），不顯示在下拉選單中
    AppState.processOptions
        .filter(process => process.code.toUpperCase() !== 'ZZ')
        .forEach(process => {
            const option = document.createElement('option');
            option.value = process.code;
            const codeUpper = process.code.toUpperCase();
            const nameUpper = process.name.toUpperCase();
            option.textContent = `${codeUpper} - ${nameUpper}`;
            select.appendChild(option);
        });
    
    // 如果有已保存的站點，恢復選擇
    const savedStation = localStorage.getItem('currentStationId');
    if (savedStation) {
        select.value = savedStation;
    }
    
    console.log(`已更新站點下拉選單，共 ${select.options.length - 1} 個選項`);
}

/**
 * 開啟底部工作表
 */
function openBottomSheet(mode, title, barcode = '', hideInputAndSubmit = false) {
    console.log('[openBottomSheet] 被調用，參數：', { mode, title, barcode, hideInputAndSubmit });
    AppState.currentMode = mode;
    document.getElementById('sheetTitle').textContent = title;
    
    // 重置表單
    const barcodeInput = document.getElementById('barcodeInput');
    const submitBtn = document.getElementById('submitBtn');
    const confirmInboundBtn = document.getElementById('confirmInboundBtn');
    
    // 隱藏確認按鈕（如果存在）
    if (confirmInboundBtn) {
        confirmInboundBtn.style.display = 'none';
    }
    
    // 根據參數決定是否隱藏條碼輸入框和提交按鈕
    if (hideInputAndSubmit) {
        // URL 帶入條碼時，隱藏輸入框和提交按鈕
        if (barcodeInput) {
            barcodeInput.style.display = 'none';
            // 隱藏條碼標籤
            const barcodeLabel = barcodeInput.previousElementSibling;
            if (barcodeLabel && barcodeLabel.tagName === 'LABEL') {
                barcodeLabel.style.display = 'none';
            }
            if (barcode) {
                barcodeInput.value = barcode;
            } else {
                barcodeInput.value = '';
            }
        }
        if (submitBtn) {
            submitBtn.style.display = 'none';
        }
    } else {
        // 正常情況，顯示輸入框和提交按鈕
        if (barcodeInput) {
            barcodeInput.style.display = '';
            // 顯示條碼標籤
            const barcodeLabel = barcodeInput.previousElementSibling;
            if (barcodeLabel && barcodeLabel.tagName === 'LABEL') {
                barcodeLabel.style.display = '';
            }
            if (barcode) {
                barcodeInput.value = barcode;
            } else {
                barcodeInput.value = '';
            }
        }
        if (submitBtn) {
            submitBtn.style.display = '';
        }
    }
    
    const outboundFields = document.getElementById('outboundFields');
    if (outboundFields) {
        outboundFields.classList.add('hidden');
    }
    const firstFields = document.getElementById('firstFields');
    if (firstFields) {
        firstFields.classList.add('hidden');
    }
    const inboundBarcodeSelection = document.getElementById('inboundBarcodeSelection');
    if (inboundBarcodeSelection) {
        inboundBarcodeSelection.classList.add('hidden');
    }
    
    // 根據模式顯示對應欄位
    if (mode === 'outbound') {
        const outboundFields = document.getElementById('outboundFields');
        if (outboundFields) {
            outboundFields.classList.remove('hidden');
        } else {
            console.error('[openBottomSheet] 找不到 outboundFields 元素');
        }
        // 重置良品和不良品的容器選擇和數量
        const goodContainerSelect = document.getElementById('goodContainerSelect');
        const badContainerSelect = document.getElementById('badContainerSelect');
        const goodQtyInput = document.getElementById('goodQtyInput');
        const badQtyInput = document.getElementById('badQtyInput');
        
        if (goodContainerSelect) {
            goodContainerSelect.value = '';
        }
        if (badContainerSelect) {
            badContainerSelect.value = '';
        }
        if (goodQtyInput) {
            goodQtyInput.value = '';
        }
        if (badQtyInput) {
            badQtyInput.value = '';
        }
        
        // 重置投入量資訊
        AppState.currentInboundQty = null;
        
        // 隱藏箱數預覽
        const goodBoxPreview = document.getElementById('goodBoxPreview');
        const badBoxPreview = document.getElementById('badBoxPreview');
        if (goodBoxPreview) {
            goodBoxPreview.classList.add('hidden');
        }
        if (badBoxPreview) {
            badBoxPreview.classList.add('hidden');
        }
        
        // 確保容器選單已更新
        if (AppState.containerOptions && AppState.containerOptions.length > 0) {
            updateContainerSelects();
        }
        
        // 綁定自動計算箱數的事件監聽器
        setupOutboundBoxCalculation();
        
        // 查詢並顯示當前站點的投入量
        if (barcode) {
            loadOutboundInboundInfo(barcode);
        }
    } else if (mode === 'first') {
        const firstFields = document.getElementById('firstFields');
        if (firstFields) {
            firstFields.classList.remove('hidden');
        } else {
            console.error('[openBottomSheet] 找不到 firstFields 元素');
        }
        // 確保容器選單已更新
        if (AppState.containerOptions && AppState.containerOptions.length > 0) {
            updateContainerSelects();
        }
        // 重置產品線、機種和容器選擇
        const seriesSelect = document.getElementById('seriesSelect');
        if (seriesSelect) {
            seriesSelect.value = '';
        }
        const modelSelect = document.getElementById('modelSelect');
        if (modelSelect) {
            modelSelect.value = '';
        }
        const firstContainerSelect = document.getElementById('firstContainerSelect');
        if (firstContainerSelect) {
            firstContainerSelect.value = '';
        }
        // 重置工單號
        const orderInput = document.getElementById('orderInput');
        if (orderInput) {
            orderInput.value = '';
        }
    } else if (mode === 'inbound') {
        // 遷入模式：確保條碼選擇界面是隱藏的（會在查詢後顯示）
        document.getElementById('inboundBarcodeSelection').classList.add('hidden');
    }
    
    // 顯示背景遮罩和底部工作表
    const overlay = document.getElementById('bottomSheetOverlay');
    const sheet = document.getElementById('bottomSheet');
    console.log('[openBottomSheet] 準備顯示工作表，overlay:', overlay, 'sheet:', sheet);
    if (overlay) {
        overlay.classList.add('open');
        console.log('[openBottomSheet] overlay 已添加 open 類');
    } else {
        console.error('[openBottomSheet] 找不到 bottomSheetOverlay 元素');
    }
    if (sheet) {
        sheet.classList.add('open');
        console.log('[openBottomSheet] sheet 已添加 open 類');
    } else {
        console.error('[openBottomSheet] 找不到 bottomSheet 元素');
    }
    
    // 聚焦到條碼輸入框（如果不是首站遷出）
    if (mode !== 'first' && barcodeInput) {
        setTimeout(() => {
            if (barcodeInput) {
                barcodeInput.focus();
            }
        }, 300);
    }
}

/**
 * 關閉底部工作表
 */
function closeBottomSheet() {
    document.getElementById('bottomSheetOverlay').classList.remove('open');
    document.getElementById('bottomSheet').classList.remove('open');
    AppState.currentMode = null;
}

/**
 * 檢查條碼並自動切換到對應功能
 */
async function checkBarcodeAndSwitch(barcode) {
    if (!barcode || !AppState.operatorId || !AppState.currentStationId) {
        return;
    }
    
    // 清理條碼（移除可能的 b= 前綴）
    let cleanBarcode = barcode.trim();
    if (cleanBarcode.startsWith('b=')) {
        cleanBarcode = cleanBarcode.substring(2).trim();
    }
    
    // 顯示讀取中狀態
    const sheetTitle = document.getElementById('sheetTitle');
    const originalTitle = sheetTitle.textContent;
    sheetTitle.textContent = '讀取中...';
    
    // 禁用提交按鈕，避免重複提交
    const submitBtn = document.getElementById('submitBtn');
    const originalSubmitText = submitBtn.textContent;
    submitBtn.disabled = true;
    submitBtn.textContent = '讀取中...';
    
    try {
        const response = await fetch('/api/scan/check', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                barcode: cleanBarcode,
                current_station_id: AppState.currentStationId
            })
        });
        
        const data = await response.json();
        
        // 恢復提交按鈕
        submitBtn.disabled = false;
        submitBtn.textContent = originalSubmitText;
        
        if (!response.ok) {
            // 如果檢查失敗，恢復標題
            sheetTitle.textContent = originalTitle;
            showAlert('錯誤', data.detail || '檢查條碼失敗', 'error');
            return;
        }
        
        // 根據建議的操作類型自動切換
        const suggestedAction = data.suggested_action;
        
        if (suggestedAction === 'first') {
            // 切換到首站遷出
            closeBottomSheet();
            openBottomSheet('first', '首站遷出');
            // 如果有工單號、產品線和機種，自動填入
            if (data.data) {
                setTimeout(() => {
                    // 填入工單號
                    if (data.data.order) {
                        const orderInput = document.getElementById('orderInput');
                        if (orderInput) {
                            let orderValue = data.data.order.replace(/^0+/, '');
                            orderInput.value = orderValue || data.data.order;
                        }
                    }
                    // 填入產品線（如果 SKU 存在）
                    if (data.data.series_code) {
                        const seriesSelect = document.getElementById('seriesSelect');
                        if (seriesSelect) {
                            seriesSelect.value = data.data.series_code;
                            // 觸發產品線變更事件，更新機種選單
                            seriesSelect.dispatchEvent(new Event('change'));
                        }
                    }
                    // 填入機種（如果 SKU 存在）
                    if (data.data.model_code) {
                        const modelSelect = document.getElementById('modelSelect');
                        if (modelSelect) {
                            // 等待產品線選單更新後再設置機種
                            setTimeout(() => {
                                let modelCode = data.data.model_code;
                                // 嘗試直接匹配
                                if (modelSelect.querySelector(`option[value="${modelCode}"]`)) {
                                    modelSelect.value = modelCode;
                                } else {
                                    // 如果直接匹配失敗，嘗試去掉前導零匹配
                                    let modelCodeNoZero = modelCode.replace(/^0+/, '') || '0';
                                    if (modelSelect.querySelector(`option[value="${modelCodeNoZero}"]`)) {
                                        modelSelect.value = modelCodeNoZero;
                                    } else {
                                        // 如果還是失敗，嘗試補零到 3 碼匹配
                                        let modelCodePadded = modelCodeNoZero.padStart(3, '0');
                                        if (modelSelect.querySelector(`option[value="${modelCodePadded}"]`)) {
                                            modelSelect.value = modelCodePadded;
                                        }
                                    }
                                }
                            }, 100);
                        }
                    }
                    // 聚焦到工單號輸入框
                    const orderInput = document.getElementById('orderInput');
                    if (orderInput) {
                        orderInput.focus();
                    }
                }, 350);
            }
        } else if (suggestedAction === 'outbound') {
            // 切換到遷出
            closeBottomSheet();
            openBottomSheet('outbound', '貨物遷出', cleanBarcode);
        } else if (suggestedAction === 'inbound') {
            // 切換到遷入：查詢相同工單的上一站條碼，然後顯示選擇界面
            closeBottomSheet();
            
            // 解析條碼取得工單號
            const parsed = parseBarcode(cleanBarcode);
            if (parsed && parsed.order) {
                const order = parsed.order.replace(/^0+/, '') || parsed.order;
                
                // 顯示處理動畫
                showProcessing('查詢中...', '正在查詢相同工單的上一站條碼');
                
                // 查詢上一站條碼
                fetch(`/api/scan/previous-barcodes?order=${encodeURIComponent(order)}&current_station_id=${encodeURIComponent(AppState.currentStationId)}`)
                    .then(queryResponse => {
                        if (!queryResponse.ok) {
                            throw new Error('查詢上一站條碼失敗');
                        }
                        return queryResponse.json();
                    })
                    .then(queryData => {
                        // 隱藏處理動畫
                        hideProcessing();
                        
                        // 準備條碼列表（包含掃描的條碼）
                        let barcodesToShow = [];
                        
                        // 如果有上一站條碼，添加到列表
                        if (queryData.success && queryData.data && queryData.data.length > 0) {
                            barcodesToShow = [...queryData.data];
                            
                            // 檢查掃描的條碼是否也在列表中
                            const scannedBarcodeInList = barcodesToShow.some(item => item.barcode === cleanBarcode);
                            
                            // 如果掃描的條碼不在列表中，添加到列表開頭
                            if (!scannedBarcodeInList) {
                                if (parsed) {
                                    barcodesToShow.unshift({
                                        barcode: cleanBarcode,
                                        box_seq: parsed.box_seq || '',
                                        qty: parsed.qty || '',
                                        status: parsed.status || '',
                                        container: parsed.container || '',
                                        process: parsed.process || ''
                                    });
                                }
                            }
                        } else {
                            // 沒有上一站條碼，只顯示掃描的條碼
                            if (parsed) {
                                barcodesToShow = [{
                                    barcode: cleanBarcode,
                                    box_seq: parsed.box_seq || '',
                                    qty: parsed.qty || '',
                                    status: parsed.status || '',
                                    container: parsed.container || '',
                                    process: parsed.process || ''
                                }];
                            }
                        }
                        
                        // 打開遷入底部工作表（隱藏輸入框和提交按鈕）
                        openBottomSheet('inbound', '貨物遷入', cleanBarcode, true);
                        
                        // 直接顯示條碼選擇列表（預設全選）
                        setTimeout(() => {
                            if (barcodesToShow.length > 0) {
                                showBarcodeSelection(barcodesToShow, cleanBarcode, async (selectedBarcodesList) => {
                                    // 使用者確認選擇後，執行批量遷入
                                    await performInbound(selectedBarcodesList);
                                });
                            }
                        }, 100);
                    })
                    .catch(error => {
                        console.error('查詢上一站條碼失敗：', error);
                        // 查詢失敗，仍然打開遷入工作表
                        hideProcessing();
                        openBottomSheet('inbound', '貨物遷入', cleanBarcode);
                    });
            } else {
                // 無法解析條碼，直接打開遷入工作表
                openBottomSheet('inbound', '貨物遷入', cleanBarcode);
            }
        } else if (suggestedAction === 'trace') {
            // 切換到查詢（直接執行查詢，不顯示提示）
            closeBottomSheet();
            // 顯示處理動畫
            showProcessing('查詢中...', '正在查詢追溯記錄');
            // 自動執行查詢
            setTimeout(() => {
                const barcodeInput = document.getElementById('barcodeInput');
                if (barcodeInput) {
                    barcodeInput.value = cleanBarcode;
                }
                handleTrace();
            }, 300);
        } else {
            // 恢復標題
            sheetTitle.textContent = originalTitle;
        }
        
    } catch (error) {
        // 檢查失敗，恢復標題和按鈕
        sheetTitle.textContent = originalTitle;
        submitBtn.disabled = false;
        submitBtn.textContent = originalSubmitText;
        console.error('檢查條碼失敗：', error);
        showAlert('錯誤', '檢查條碼時發生錯誤', 'error');
    }
}

/**
 * 處理提交
 */
async function handleSubmit() {
    const mode = AppState.currentMode;
    
    // 如果是掃描模式，先檢查條碼
    if (mode === 'scan') {
        const barcode = document.getElementById('barcodeInput').value.trim();
        if (!barcode) {
            showAlert('錯誤', '請輸入或掃描條碼', 'error');
            return;
        }
        // 檢查條碼並自動切換
        await checkBarcodeAndSwitch(barcode);
        return;
    }
    
    if (mode === 'inbound') {
        await handleInbound();
    } else if (mode === 'outbound') {
        await handleOutbound();
    } else if (mode === 'trace') {
        await handleTrace();
    } else if (mode === 'first') {
        await handleFirst();
    }
}

/**
 * 處理遷入（樂觀 UI + 錯誤處理）
 */
async function handleInbound() {
    const barcode = document.getElementById('barcodeInput').value.trim();
    
    if (!barcode) {
        showAlert('錯誤', '請輸入或掃描條碼', 'error');
        return;
    }
    
    // 檢查是否為 ZZ 製程（新工單），如果是則自動切換到首站遷出
    // 移除所有 - 後解析條碼
    const parsed = parseBarcode(barcode);
    if (!parsed) {
        showAlert('錯誤', '無法解析條碼，請檢查條碼格式', 'error');
        return;
    }
    
    const processCode = parsed.process ? parsed.process.trim().toUpperCase() : '';
    if (processCode === 'ZZ') {
        // 關閉遷入工作表
    closeBottomSheet();
        // 開啟首站遷出
        openBottomSheet('first', '首站遷出');
        // 如果有工單號，自動填入
        if (parsed.order) {
            setTimeout(() => {
                const orderInput = document.getElementById('orderInput');
                if (orderInput) {
                    let orderValue = parsed.order.replace(/^0+/, '');
                    orderInput.value = orderValue || parsed.order;
                    orderInput.focus();
                }
            }, 350);
        }
        return;
    }
    
    // 解析條碼取得工單號
    if (!parsed.order) {
        showAlert('錯誤', '無法解析條碼工單號，請檢查條碼格式', 'error');
        return;
    }
    
    const order = parsed.order.replace(/^0+/, '') || parsed.order;
    
    // 先查詢相同工單的上一站條碼
    showProcessing('查詢中...', '正在查詢相同工單的上一站條碼');
    
    try {
        // 查詢上一站條碼
        console.log('查詢上一站條碼，工單:', order, '當前站點:', AppState.currentStationId);
        const queryResponse = await fetch(`/api/scan/previous-barcodes?order=${encodeURIComponent(order)}&current_station_id=${encodeURIComponent(AppState.currentStationId)}`);
        
        if (!queryResponse.ok) {
            console.error('查詢上一站條碼 API 失敗:', queryResponse.status, queryResponse.statusText);
            hideProcessing();
            await performInbound([barcode]);
            return;
        }
        
        const queryData = await queryResponse.json();
        console.log('查詢結果:', queryData);
        
        // 檢查掃描的條碼是否也在列表中（如果是上一站條碼）
        if (queryData.success && queryData.data && queryData.data.length > 0) {
            const scannedBarcodeInList = queryData.data.some(item => item.barcode === barcode);
            console.log('掃描的條碼是否在列表中:', scannedBarcodeInList);
            
            // 如果掃描的條碼不在列表中，添加到列表開頭
            if (!scannedBarcodeInList) {
                // 解析掃描的條碼，獲取資訊
                const scannedParsed = parseBarcode(barcode);
                if (scannedParsed) {
                    queryData.data.unshift({
                        barcode: barcode,
                        box_seq: scannedParsed.box_seq || '',
                        qty: scannedParsed.qty || '',
                        status: scannedParsed.status || '',
                        container: scannedParsed.container || '',
                        process: scannedParsed.process || ''
                    });
                    console.log('已添加掃描的條碼到列表開頭');
                }
            }
            
            // 有上一站條碼，顯示選擇界面
            hideProcessing();
            console.log('顯示條碼選擇界面，條碼數量:', queryData.data.length);
            
            // 顯示條碼選擇列表
            showBarcodeSelection(queryData.data, barcode, async (selectedBarcodesList) => {
                // 使用者確認選擇後，執行批量遷入
                console.log('使用者選擇的條碼:', selectedBarcodesList);
                await performInbound(selectedBarcodesList);
            });
            return;
        } else {
            // 沒有上一站條碼，直接執行單個遷入
            console.log('沒有上一站條碼，直接執行單個遷入');
            hideProcessing();
            await performInbound([barcode]);
            return;
        }
    } catch (error) {
        hideProcessing();
        console.error('查詢上一站條碼失敗：', error);
        // 查詢失敗，仍然嘗試單個遷入
        await performInbound([barcode]);
        return;
    }
}

/**
 * 執行遷入操作
 */
async function performInbound(selectedBarcodes) {
    if (!selectedBarcodes || selectedBarcodes.length === 0) {
        showAlert('錯誤', '請至少選擇一個條碼', 'error');
        return;
    }
    
    // 顯示處理動畫
    showProcessing('處理中...', '正在驗證流程並記錄遷入');
    
    try {
        const response = await fetch('/api/scan/inbound', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                barcode: selectedBarcodes[0], // 主要條碼（用於流程驗證）
                operator_id: AppState.operatorId,
                current_station_id: AppState.currentStationId,
                selected_barcodes: selectedBarcodes // 批量遷入的條碼列表
            })
        });
        
        const data = await response.json();
        
        // 檢查是否需要切換到遷出功能
        if (data.should_switch_to_outbound) {
            hideProcessing();
            // 關閉遷入工作表
            closeBottomSheet();
            // 開啟遷出功能
            openBottomSheet('outbound', '貨物遷出');
            // 自動填入條碼
            setTimeout(() => {
                const barcodeInput = document.getElementById('barcodeInput');
                if (barcodeInput) {
                    barcodeInput.value = data.data.barcode;
                    barcodeInput.focus();
                }
            }, 350);
            // 顯示提示訊息
            showAlert('提示', data.message || '該條碼已有遷入記錄，已自動切換到遷出功能', 'warning');
            return;
        }
        
        if (!response.ok) {
            // 檢查是否為寫入失敗錯誤（500）
            const isWriteError = response.status === 500 && 
                                 (data.detail && data.detail.includes('寫入 Google Sheets 失敗'));
            
            if (isWriteError) {
                // 寫入失敗：不關閉工作表，顯示錯誤訊息，讓使用者可以再次提交
                hideProcessing();
                showAlert('寫入失敗', data.detail || '寫入 Google Sheets 失敗，請稍後再試', 'error');
                playSound('error');
                if (navigator.vibrate) {
                    navigator.vibrate([200, 100, 200]);
                }
                return; // 不關閉工作表，讓使用者可以重試
            } else {
                // 其他錯誤（400 流程錯誤等）：關閉工作表並顯示錯誤
                hideProcessing();
                closeBottomSheet();
            throw new Error(data.detail || '遷入失敗');
            }
        }
        
        // 成功：關閉工作表並顯示成功訊息
        hideProcessing();
        closeBottomSheet();
        
        // 顯示成功訊息（包含成功筆數）
        const successMsg = data.data.success_count > 1 
            ? `遷入成功（共 ${data.data.success_count} 筆）\n工單：${data.data.order}`
            : `遷入成功\n工單：${data.data.order}，SKU：${data.data.sku}`;
        showSuccess('遷入成功', successMsg);
        
        // 播放成功音效（如果有）
        playSound('success');
        
    } catch (error) {
        // 錯誤：檢查是否為網路錯誤（可能是寫入失敗）
        const isNetworkError = error.message.includes('fetch') || 
                               error.message.includes('Network') ||
                               error.message.includes('Failed to fetch');
        
        if (isNetworkError) {
            // 網路錯誤：不關閉工作表，顯示錯誤訊息
            hideProcessing();
            showAlert('網路錯誤', '無法連接到伺服器，請檢查網路連線後再試', 'error');
            playSound('error');
            if (navigator.vibrate) {
                navigator.vibrate([200, 100, 200]);
            }
        } else {
            // 其他錯誤：關閉工作表並顯示錯誤
            hideProcessing();
            closeBottomSheet();
        showAlert('流程錯誤', error.message, 'error');
        playSound('error');
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200]);
            }
        }
    }
}

/**
 * 載入遷出頁面的投入量資訊
 */
async function loadOutboundInboundInfo(barcode) {
    // 解析條碼獲取工單號
    const parsed = parseBarcode(barcode);
    if (!parsed || !parsed.order) {
        // 無法解析條碼，隱藏投入量顯示
        const inboundInfo = document.getElementById('outboundInboundInfo');
        if (inboundInfo) {
            inboundInfo.classList.add('hidden');
        }
        return;
    }
    
    // 顯示投入量區塊
    const inboundInfo = document.getElementById('outboundInboundInfo');
    const inboundQty = document.getElementById('outboundInboundQty');
    
    if (inboundInfo) {
        inboundInfo.classList.remove('hidden');
    }
    
    if (inboundQty) {
        inboundQty.textContent = '查詢中...';
    }
    
    // 取得工單號（去除前導零）
    const order = parsed.order.replace(/^0+/, '') || parsed.order;
    
    try {
        const response = await fetch(`/api/scan/inbound-quantity?order=${encodeURIComponent(order)}&station_id=${encodeURIComponent(AppState.currentStationId)}`);
        const data = await response.json();
        
        if (data.success && inboundQty) {
            const totalQty = data.data.total_inbound_qty;
            inboundQty.textContent = `${totalQty} 件`;
            // 存儲投入量到 AppState，供驗證使用
            AppState.currentInboundQty = totalQty;
        } else {
            if (inboundQty) {
                inboundQty.textContent = '查詢失敗';
            }
            AppState.currentInboundQty = null;
        }
    } catch (error) {
        console.error('查詢投入量失敗：', error);
        if (inboundQty) {
            inboundQty.textContent = '查詢失敗';
        }
    }
}

/**
 * 設置遷出功能的自動計算箱數功能
 */
function setupOutboundBoxCalculation() {
    const goodQtyInput = document.getElementById('goodQtyInput');
    const goodContainerSelect = document.getElementById('goodContainerSelect');
    const badQtyInput = document.getElementById('badQtyInput');
    const badContainerSelect = document.getElementById('badContainerSelect');
    
    // 移除舊的事件監聽器（如果有的話）
    if (goodQtyInput && goodQtyInput._boxCalcHandler) {
        goodQtyInput.removeEventListener('input', goodQtyInput._boxCalcHandler);
        goodContainerSelect.removeEventListener('change', goodQtyInput._boxCalcHandler);
    }
    if (badQtyInput && badQtyInput._boxCalcHandler) {
        badQtyInput.removeEventListener('input', badQtyInput._boxCalcHandler);
        badContainerSelect.removeEventListener('change', badQtyInput._boxCalcHandler);
    }
    
    // 良品箱數計算
    const calculateGoodBoxes = () => {
        const qty = parseInt(goodQtyInput.value) || 0;
        const containerCode = goodContainerSelect.value;
        
        if (qty > 0 && containerCode) {
            const container = AppState.containerOptions.find(c => c.code === containerCode);
            if (container && container.capacity > 0) {
                const boxCount = Math.ceil(qty / container.capacity);
                const goodBoxCount = document.getElementById('goodBoxCount');
                const goodBoxPreview = document.getElementById('goodBoxPreview');
                if (goodBoxCount) {
                    goodBoxCount.textContent = boxCount;
                }
                if (goodBoxPreview) {
                    goodBoxPreview.classList.remove('hidden');
                }
            } else {
                const goodBoxPreview = document.getElementById('goodBoxPreview');
                if (goodBoxPreview) {
                    goodBoxPreview.classList.add('hidden');
                }
            }
        } else {
            const goodBoxPreview = document.getElementById('goodBoxPreview');
            if (goodBoxPreview) {
                goodBoxPreview.classList.add('hidden');
            }
        }
    };
    
    // 不良品箱數計算
    const calculateBadBoxes = () => {
        const qty = parseInt(badQtyInput.value) || 0;
        const containerCode = badContainerSelect.value;
        
        if (qty > 0 && containerCode) {
            const container = AppState.containerOptions.find(c => c.code === containerCode);
            if (container && container.capacity > 0) {
                const boxCount = Math.ceil(qty / container.capacity);
                const badBoxCount = document.getElementById('badBoxCount');
                const badBoxPreview = document.getElementById('badBoxPreview');
                if (badBoxCount) {
                    badBoxCount.textContent = boxCount;
                }
                if (badBoxPreview) {
                    badBoxPreview.classList.remove('hidden');
                }
            } else {
                const badBoxPreview = document.getElementById('badBoxPreview');
                if (badBoxPreview) {
                    badBoxPreview.classList.add('hidden');
                }
            }
        } else {
            const badBoxPreview = document.getElementById('badBoxPreview');
            if (badBoxPreview) {
                badBoxPreview.classList.add('hidden');
            }
        }
    };
    
    // 綁定事件
    if (goodQtyInput && goodContainerSelect) {
        goodQtyInput._boxCalcHandler = calculateGoodBoxes;
        goodContainerSelect._boxCalcHandler = calculateGoodBoxes;
        goodQtyInput.addEventListener('input', calculateGoodBoxes);
        goodContainerSelect.addEventListener('change', calculateGoodBoxes);
    }
    
    if (badQtyInput && badContainerSelect) {
        badQtyInput._boxCalcHandler = calculateBadBoxes;
        badContainerSelect._boxCalcHandler = calculateBadBoxes;
        badQtyInput.addEventListener('input', calculateBadBoxes);
        badContainerSelect.addEventListener('change', calculateBadBoxes);
    }
}

/**
 * 處理遷出（樂觀 UI + 錯誤處理）
 */
async function handleOutbound() {
    const barcode = document.getElementById('barcodeInput').value.trim();
    const goodQty = document.getElementById('goodQtyInput').value.trim();
    const goodContainer = document.getElementById('goodContainerSelect').value;
    const badQty = document.getElementById('badQtyInput').value.trim();
    const badContainer = document.getElementById('badContainerSelect').value;
    
    if (!barcode) {
        showAlert('錯誤', '請輸入或掃描條碼', 'error');
        return;
    }
    
    // 至少需要填寫一組（良品或不良品）
    if ((!goodQty || !goodContainer) && (!badQty || !badContainer)) {
        showAlert('錯誤', '請至少填寫一組（良品或不良品）的數量和容器', 'error');
        return;
    }
    
    // 驗證良品數據
    if (goodQty && !goodContainer) {
        showAlert('錯誤', '請選擇良品容器', 'error');
        return;
    }
    if (goodContainer && !goodQty) {
        showAlert('錯誤', '請輸入良品數量', 'error');
        return;
    }
    
    // 驗證不良品數據
    if (badQty && !badContainer) {
        showAlert('錯誤', '請選擇不良品容器', 'error');
        return;
    }
    if (badContainer && !badQty) {
        showAlert('錯誤', '請輸入不良品數量', 'error');
        return;
    }
    
    // 防呆驗證：良品與不良品數的加總要等於投入數
    const goodQtyNum = parseInt(goodQty) || 0;
    const badQtyNum = parseInt(badQty) || 0;
    const totalOutboundQty = goodQtyNum + badQtyNum;
    
    // 如果有投入量資訊，進行驗證
    if (AppState.currentInboundQty !== null && AppState.currentInboundQty !== undefined) {
        if (totalOutboundQty !== AppState.currentInboundQty) {
            showAlert(
                '數量不符', 
                `加總 ${totalOutboundQty} 件與投入量 ${AppState.currentInboundQty} 件不符`,
                'error'
            );
            return;
        }
    } else {
        // 如果沒有投入量資訊，嘗試查詢一次
        const parsed = parseBarcode(barcode);
        if (parsed && parsed.order) {
            const order = parsed.order.replace(/^0+/, '') || parsed.order;
            try {
                const response = await fetch(`/api/scan/inbound-quantity?order=${encodeURIComponent(order)}&station_id=${encodeURIComponent(AppState.currentStationId)}`);
                const data = await response.json();
                
                if (data.success) {
                    const inboundQty = data.data.total_inbound_qty;
                    if (totalOutboundQty !== inboundQty) {
                        showAlert(
                            '數量不符', 
                            `加總 ${totalOutboundQty} 件與投入量 ${inboundQty} 件不符`,
                            'error'
                        );
                        return;
                    }
                }
            } catch (error) {
                console.error('查詢投入量失敗：', error);
                // 查詢失敗時，仍然允許提交（避免因為查詢失敗而阻止正常操作）
            }
        }
    }
    
    // 不立即關閉工作表，等待 API 回應後再決定
    showProcessing('處理中...', '正在計算箱子數量並生成條碼');
    
    try {
        // 準備請求數據
        const requestData = {
            barcode: barcode,
            operator_id: AppState.operatorId,
            current_station_id: AppState.currentStationId,
            good_items: null,
            bad_items: null
        };
        
        // 如果有良品，添加到請求
        if (goodQty && goodContainer) {
            requestData.good_items = {
                qty: goodQty,
                container: goodContainer,
                status: 'G'
            };
        }
        
        // 如果有不良品，添加到請求
        if (badQty && badContainer) {
            requestData.bad_items = {
                qty: badQty,
                container: badContainer,
                status: 'N'
            };
        }
        
        const response = await fetch('/api/scan/outbound', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // 檢查是否為寫入失敗錯誤（500）
            const isWriteError = response.status === 500 && 
                                 (data.detail && data.detail.includes('寫入 Google Sheets 失敗'));
            
            if (isWriteError) {
                // 寫入失敗：不關閉工作表，顯示錯誤訊息，讓使用者可以再次提交
                hideProcessing();
                showAlert('寫入失敗', data.detail || '寫入 Google Sheets 失敗，請稍後再試', 'error');
                playSound('error');
                if (navigator.vibrate) {
                    navigator.vibrate([200, 100, 200]);
                }
                return; // 不關閉工作表，讓使用者可以重試
            } else {
                // 其他錯誤：關閉工作表並顯示錯誤
                hideProcessing();
                closeBottomSheet();
            throw new Error(data.detail || '遷出失敗');
        }
        }
        
        // 成功：關閉工作表並顯示多箱子資訊
        hideProcessing();
        closeBottomSheet();
        
        // 顯示多箱子資訊
        showMultiBoxInfo(data.data);
        
        playSound('success');
        
    } catch (error) {
        // 檢查是否為網路錯誤（可能是寫入失敗）
        const isNetworkError = error.message.includes('fetch') || 
                               error.message.includes('Network') ||
                               error.message.includes('Failed to fetch');
        
        if (isNetworkError) {
            // 網路錯誤：不關閉工作表，顯示錯誤訊息
            hideProcessing();
            showAlert('網路錯誤', '無法連接到伺服器，請檢查網路連線後再試', 'error');
            playSound('error');
            if (navigator.vibrate) {
                navigator.vibrate([200, 100, 200]);
            }
        } else {
            // 其他錯誤：關閉工作表並顯示錯誤
            hideProcessing();
            closeBottomSheet();
        showAlert('錯誤', error.message, 'error');
        playSound('error');
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200]);
            }
        }
    }
}

/**
 * 處理追溯查詢
 */
async function handleTrace() {
    const barcode = document.getElementById('barcodeInput').value.trim();
    
    if (!barcode) {
        hideProcessing();
        showAlert('錯誤', '請輸入或掃描條碼', 'error');
        return;
    }
    
    // 如果還沒有顯示處理動畫，則顯示（可能從其他地方調用）
    const processingOverlay = document.getElementById('processingOverlay');
    if (processingOverlay && processingOverlay.classList.contains('hidden')) {
        showProcessing('查詢中...', '正在查詢追溯記錄');
    }
    
    try {
        const response = await fetch('/api/scan/trace', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                barcode: barcode
            })
        });
        
        const data = await response.json();
        
        // 隱藏處理動畫
        hideProcessing();
        
        if (!response.ok) {
            throw new Error(data.detail || '查詢失敗');
        }
        
        // 顯示追溯結果頁面
        showTracePage(data.data);
        playSound('success');
        
    } catch (error) {
        hideProcessing();
        showAlert('錯誤', error.message, 'error');
        playSound('error');
    }
}

/**
 * 顯示追溯結果頁面
 */
function showTracePage(traceData) {
    const tracePage = document.getElementById('tracePage');
    const traceOrderTitle = document.getElementById('traceOrderTitle');
    const traceSkuInfo = document.getElementById('traceSkuInfo');
    const traceContent = document.getElementById('traceContent');
    
    // 設置標題
    traceOrderTitle.textContent = `工單：${traceData.order}`;
    
    // 顯示產品線和型號信息
    if (traceData.series_code && traceData.model_code) {
        const seriesName = traceData.series_name || traceData.series_code;
        const modelName = traceData.model_name || traceData.model_code;
        traceSkuInfo.textContent = `${traceData.series_code} - ${traceData.model_code} | ${seriesName} - ${modelName}`;
    } else {
        traceSkuInfo.textContent = `SKU：${traceData.sku || ''}`;
    }
    
    // 清空內容
    traceContent.innerHTML = '';
    
    // 獲取製程站點名稱映射（統一轉換為大寫）
    const processNameMap = {};
    AppState.processOptions.forEach(p => {
        processNameMap[p.code.toUpperCase()] = p.name.toUpperCase();
    });
    
    // 顯示統計信息（根據新的邏輯）
    const stats = traceData.statistics;
    const statsCard = document.createElement('div');
    statsCard.className = 'card glass p-4 mb-4 bg-blue-50 border-2 border-blue-200';
    statsCard.innerHTML = `
        <div class="grid grid-cols-3 gap-4 text-center mb-4">
            <div>
                <p class="text-sm text-gray-600">總數量</p>
                <p class="text-xl font-bold text-gray-900">${stats.total_qty || 0}</p>
                <p class="text-xs text-gray-500 mt-1">（首站遷出）</p>
            </div>
            <div>
                <p class="text-sm text-gray-600">最終站良品</p>
                <p class="text-xl font-bold text-green-600">${stats.final_good_qty || 0}</p>
            </div>
            <div>
                <p class="text-sm text-gray-600">全製程不良品</p>
                <p class="text-xl font-bold text-red-600">${stats.total_defect_qty || 0}</p>
            </div>
        </div>
        <div class="grid grid-cols-2 gap-4 pt-2 border-t border-blue-300">
            <div class="text-center">
                <p class="text-sm text-gray-600">直通率</p>
                <p class="text-2xl font-bold text-blue-600">${stats.first_pass_rate || 0}%</p>
            </div>
            <div class="text-center">
                <p class="text-sm text-gray-600">全製程用時</p>
                <p class="text-2xl font-bold text-purple-600">${stats.total_process_time || '00:00:00'}</p>
            </div>
        </div>
    `;
    traceContent.appendChild(statsCard);
    
    // 顯示各站點時間軸
    if (traceData.station_timeline && traceData.station_timeline.length > 0) {
        traceData.station_timeline.forEach((station, index) => {
            const stationCard = document.createElement('div');
            stationCard.className = 'trace-station-card';
            
            const processName = processNameMap[station.process] || station.process.toUpperCase();
            const processCodeUpper = station.process.toUpperCase();
            const stationTitle = `${processCodeUpper} - ${processName}`;
            
            let html = `
                <div class="trace-station-header">${stationTitle}</div>
            `;
            
            if (station.in_time) {
                html += `
                    <div class="trace-info-row">
                        <span class="trace-info-label">遷入時間</span>
                        <span class="trace-info-value">${station.in_time}</span>
                    </div>
                `;
            }
            
            if (station.out_time) {
                html += `
                    <div class="trace-info-row">
                        <span class="trace-info-label">遷出時間</span>
                        <span class="trace-info-value">${station.out_time}</span>
                    </div>
                `;
            }
            
            if (station.total_time) {
                html += `
                    <div class="trace-info-row">
                        <span class="trace-info-label">總耗時間</span>
                        <span class="trace-info-value">${station.total_time}</span>
                    </div>
                `;
            }
            
            html += `
                <div class="trace-info-row">
                    <span class="trace-info-label">投入數量</span>
                    <span class="trace-info-value">${station.input_qty || 0}</span>
                </div>
            `;
            
            // 顯示產出良品和不良品詳細信息（如果有）
            if (station.output_good_qty !== undefined || station.output_bad_qty !== undefined) {
                const goodQty = station.output_good_qty || 0;
                const badQty = station.output_bad_qty || 0;
                html += `
                    <div class="trace-info-row">
                        <span class="trace-info-label">產出良品</span>
                        <span class="trace-info-value text-green-600">${goodQty}</span>
                    </div>
                    <div class="trace-info-row">
                        <span class="trace-info-label">產出不良品</span>
                        <span class="trace-info-value text-red-600">${badQty}</span>
                    </div>
                `;
            }
            
            // 顯示該站的良率（如果有遷出記錄）
            if (traceData.statistics.station_yield_rates && traceData.statistics.station_yield_rates[station.process]) {
                const stationYield = traceData.statistics.station_yield_rates[station.process];
                html += `
                    <div class="trace-info-row">
                        <span class="trace-info-label">當站良率</span>
                        <span class="trace-info-value text-blue-600 font-semibold">${stationYield}%</span>
                    </div>
                `;
            }
            
            stationCard.innerHTML = html;
            traceContent.appendChild(stationCard);
        });
    } else {
        const emptyCard = document.createElement('div');
        emptyCard.className = 'card glass p-8 text-center';
        emptyCard.innerHTML = '<p class="text-gray-500">暫無追溯記錄</p>';
        traceContent.appendChild(emptyCard);
    }
    
    // 顯示頁面
    tracePage.classList.add('open');
    
    // 啟動當前站點遷入條碼的自動更新（每30秒）
    startTraceInboundBarcodesUpdate();
}

// 追溯頁面自動更新定時器
let traceInboundBarcodesUpdateInterval = null;

/**
 * 啟動追溯頁面當前站點遷入條碼的自動更新
 */
function startTraceInboundBarcodesUpdate() {
    // 清除舊的定時器
    if (traceInboundBarcodesUpdateInterval) {
        clearInterval(traceInboundBarcodesUpdateInterval);
    }
    
    // 立即更新一次
    updateTraceInboundBarcodes();
    
    // 每30秒更新一次
    traceInboundBarcodesUpdateInterval = setInterval(() => {
        updateTraceInboundBarcodes();
    }, 30000);
}

/**
 * 停止追溯頁面當前站點遷入條碼的自動更新
 */
function stopTraceInboundBarcodesUpdate() {
    if (traceInboundBarcodesUpdateInterval) {
        clearInterval(traceInboundBarcodesUpdateInterval);
        traceInboundBarcodesUpdateInterval = null;
    }
}

/**
 * 更新追溯頁面當前站點的遷入條碼列表
 */
async function updateTraceInboundBarcodes() {
    if (!AppState.currentStationId) {
        return;
    }
    
    const section = document.getElementById('traceInboundBarcodesSection');
    const list = document.getElementById('traceInboundBarcodesList');
    const updateTime = document.getElementById('traceInboundBarcodesUpdateTime');
    
    if (!section || !list) {
        return;
    }
    
    try {
        const response = await fetch(`/api/scan/current-station-inbound-barcodes?station_id=${AppState.currentStationId}`);
        if (!response.ok) {
            throw new Error('獲取遷入條碼失敗');
        }
        
        const data = await response.json();
        if (!data.success) {
            throw new Error(data.message || '獲取遷入條碼失敗');
        }
        
        const barcodes = data.data || [];
        
        // 更新時間戳記
        if (updateTime) {
            const now = new Date();
            const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
            updateTime.textContent = `更新於 ${timeStr}`;
        }
        
        // 清空列表
        list.innerHTML = '';
        
        if (barcodes.length === 0) {
            const emptyItem = document.createElement('div');
            emptyItem.className = 'text-small text-center';
            emptyItem.style.color = 'var(--ios-text-tertiary)';
            emptyItem.style.padding = '16px';
            emptyItem.textContent = '目前沒有遷入條碼';
            list.appendChild(emptyItem);
        } else {
            // 顯示條碼列表
            barcodes.forEach((item, index) => {
                const barcodeItem = document.createElement('div');
                barcodeItem.className = 'card glass';
                barcodeItem.style.padding = '12px';
                barcodeItem.style.borderRadius = '12px';
                barcodeItem.style.border = '0.5px solid var(--ios-separator)';
                barcodeItem.style.marginBottom = index < barcodes.length - 1 ? '8px' : '0';
                
                barcodeItem.innerHTML = `
                    <div class="flex items-center justify-between">
                        <div class="flex-1">
                            <p class="text-small" style="color: var(--ios-text-primary); font-weight: 500; margin-bottom: 4px;">${item.barcode || '-'}</p>
                            <div class="flex gap-4 text-label" style="color: var(--ios-text-secondary);">
                                <span>工單：${item.order || '-'}</span>
                                <span>數量：${item.qty || '0'}</span>
                                <span>容器：${item.container || '-'}</span>
                            </div>
                        </div>
                    </div>
                `;
                
                list.appendChild(barcodeItem);
            });
        }
        
        // 顯示區塊
        section.style.display = 'block';
        
    } catch (error) {
        console.error('更新遷入條碼列表失敗：', error);
        // 錯誤時不顯示區塊
        if (section) {
            section.style.display = 'none';
        }
    }
}

/**
 * 更新主頁面當前站點的遷入條碼列表
 */
async function updateMainPageInboundBarcodes() {
    console.log('[updateMainPageInboundBarcodes] 開始執行，當前站點：', AppState.currentStationId);
    
    if (!AppState.currentStationId) {
        console.warn('[updateMainPageInboundBarcodes] 當前站點為空，跳過更新');
        return;
    }
    
    const list = document.getElementById('inboundBarcodesList');
    const updateTime = document.getElementById('inboundBarcodesUpdateTime');
    
    if (!list) {
        console.error('[updateMainPageInboundBarcodes] 找不到 inboundBarcodesList 元素');
        return;
    }
    
    try {
        console.log('[updateMainPageInboundBarcodes] 發送 API 請求，站點：', AppState.currentStationId);
        const response = await fetch(`/api/scan/current-station-inbound-barcodes?station_id=${AppState.currentStationId}`);
        if (!response.ok) {
            throw new Error(`獲取遷入條碼失敗：${response.status}`);
        }
        
        const data = await response.json();
        console.log('[updateMainPageInboundBarcodes] API 響應：', data);
        
        if (!data.success) {
            throw new Error(data.message || '獲取遷入條碼失敗');
        }
        
        const barcodes = data.data || [];
        console.log('[updateMainPageInboundBarcodes] 獲取到條碼數量：', barcodes.length);
        
        // 更新時間戳記
        if (updateTime) {
            const now = new Date();
            const timeStr = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
            updateTime.textContent = `更新於 ${timeStr}`;
        }
        
        // 清空列表
        list.innerHTML = '';
        
        if (barcodes.length === 0) {
            console.log('[updateMainPageInboundBarcodes] 沒有遷入條碼，顯示空狀態');
            const emptyItem = document.createElement('div');
            emptyItem.className = 'text-small text-center';
            emptyItem.style.color = 'var(--ios-text-tertiary)';
            emptyItem.style.padding = '16px';
            emptyItem.textContent = '目前沒有遷入條碼';
            list.appendChild(emptyItem);
        } else {
            console.log('[updateMainPageInboundBarcodes] 開始渲染條碼列表，共', barcodes.length, '個條碼');
            // 顯示條碼列表
            barcodes.forEach((item, index) => {
                const barcodeItem = document.createElement('div');
                barcodeItem.className = 'card glass';
                barcodeItem.style.padding = '16px';
                barcodeItem.style.borderRadius = '12px';
                barcodeItem.style.border = '0.5px solid var(--ios-separator)';
                barcodeItem.style.marginBottom = index < barcodes.length - 1 ? '8px' : '0';
                
                // 從 SKU 提取產品線和型號（SKU 格式：前2碼為產品線，後3碼為型號）
                let seriesCode = '';
                let seriesName = '';
                let modelCode = '';
                let modelName = '';
                
                if (item.sku && item.sku.length >= 5) {
                    seriesCode = item.sku.substring(0, 2).toUpperCase();
                    modelCode = item.sku.substring(2, 5).toUpperCase();
                    
                    // 從 INI 設定查找產品線名稱
                    if (AppState.seriesOptions && AppState.seriesOptions.length > 0) {
                        const seriesOption = AppState.seriesOptions.find(s => s.code.toUpperCase() === seriesCode);
                        if (seriesOption) {
                            seriesName = seriesOption.name || '';
                        }
                    }
                    
                    // 從 INI 設定查找型號名稱
                    if (AppState.modelOptions && AppState.modelOptions.length > 0) {
                        const modelOption = AppState.modelOptions.find(m => m.code.toUpperCase() === modelCode);
                        if (modelOption) {
                            modelName = modelOption.name || '';
                        }
                    }
                }
                
                // 查找容器名稱（從 INI 設定）
                let containerName = item.container || '-';
                if (item.container && AppState.containerOptions && AppState.containerOptions.length > 0) {
                    const containerOption = AppState.containerOptions.find(c => c.code.toUpperCase() === item.container.toUpperCase());
                    if (containerOption) {
                        const codeUpper = containerOption.code.toUpperCase();
                        const displayText = containerOption.name || (containerOption.capacity > 0 ? `容量 ${containerOption.capacity}` : '自訂');
                        containerName = `${codeUpper} - ${displayText}`;
                    } else {
                        containerName = item.container.toUpperCase();
                    }
                }
                
                // 構建型號顯示文字
                let modelDisplay = '';
                if (modelCode && modelName) {
                    modelDisplay = `${modelCode} - ${modelName}`;
                } else if (modelCode) {
                    modelDisplay = modelCode;
                } else if (item.sku) {
                    modelDisplay = `SKU: ${item.sku.toUpperCase()}`;
                }
                
                // 格式化遷入時間
                let timeDisplay = '-';
                if (item.timestamp) {
                    try {
                        // 嘗試解析時間戳記（可能是 ISO 格式或自定義格式）
                        const timestamp = item.timestamp;
                        // 如果是 ISO 格式，提取日期和時間部分
                        if (timestamp.includes('T')) {
                            const datePart = timestamp.split('T')[0];
                            const timePart = timestamp.split('T')[1].split('.')[0];
                            timeDisplay = `${datePart} ${timePart}`;
                        } else if (timestamp.includes(' ')) {
                            // 已經是 "YYYY-MM-DD HH:MM:SS" 格式
                            timeDisplay = timestamp;
                        } else {
                            timeDisplay = timestamp;
                        }
                    } catch (e) {
                        timeDisplay = item.timestamp;
                    }
                }
                
                barcodeItem.innerHTML = `
                    <div style="display: flex; width: 100%; gap: 16px;">
                        <div class="flex-1">
                            <!-- 第一行：型號和數量 -->
                            <div class="flex gap-6 items-center" style="margin-bottom: 8px;">
                                <div class="flex-1">
                                    <p class="text-label" style="color: var(--ios-text-secondary); margin-bottom: 2px;">型號</p>
                                    <p class="text-body" style="color: var(--ios-text-primary); font-weight: 600; font-size: 17px;">${modelDisplay || '-'}</p>
                                </div>
                                <div>
                                    <p class="text-label" style="color: var(--ios-text-secondary); margin-bottom: 2px;">數量</p>
                                    <p class="text-body" style="color: var(--ios-text-primary); font-weight: 600; font-size: 17px;">${item.qty || '0'}</p>
                                </div>
                            </div>
                            <!-- 第二行：工單和容器 -->
                            <p class="text-label" style="color: var(--ios-text-secondary); font-size: 13px; margin-top: 4px;">
                                工單：${item.order || '-'} | 容器：${containerName}
                            </p>
                        </div>
                        <!-- 右側：時間和條碼 -->
                        <div style="text-align: right; min-width: 140px;">
                            <p class="text-label" style="color: var(--ios-text-secondary); margin-bottom: 2px;">遷入時間</p>
                            <p class="text-body" style="color: var(--ios-text-primary); font-weight: 600; font-size: 17px; margin-bottom: 8px;">${timeDisplay}</p>
                            <p class="text-label" style="color: var(--ios-text-tertiary); font-size: 11px; word-break: break-all;">${item.barcode || '-'}</p>
                        </div>
                    </div>
                `;
                
                list.appendChild(barcodeItem);
            });
            console.log('[updateMainPageInboundBarcodes] 條碼列表渲染完成');
        }
        
    } catch (error) {
        console.error('[updateMainPageInboundBarcodes] 更新遷入條碼列表失敗：', error);
        if (list) {
            list.innerHTML = '<p class="text-small text-center" style="color: var(--ios-text-tertiary); padding: 16px;">載入失敗：' + error.message + '</p>';
        }
    }
}

// 主頁面遷入條碼自動更新定時器
let mainPageInboundBarcodesUpdateInterval = null;

/**
 * 啟動主頁面遷入條碼的自動更新（每30秒）
 */
function startMainPageInboundBarcodesUpdate() {
    // 清除舊的定時器
    if (mainPageInboundBarcodesUpdateInterval) {
        clearInterval(mainPageInboundBarcodesUpdateInterval);
    }
    
    // 立即更新一次
    updateMainPageInboundBarcodes();
    
    // 每30秒更新一次
    mainPageInboundBarcodesUpdateInterval = setInterval(() => {
        updateMainPageInboundBarcodes();
    }, 30000);
}

/**
 * 停止主頁面遷入條碼的自動更新
 */
function stopMainPageInboundBarcodesUpdate() {
    if (mainPageInboundBarcodesUpdateInterval) {
        clearInterval(mainPageInboundBarcodesUpdateInterval);
        mainPageInboundBarcodesUpdateInterval = null;
    }
}

/**
 * 關閉追溯結果頁面
 */
function closeTracePage() {
    document.getElementById('tracePage').classList.remove('open');
    // 停止自動更新
    stopTraceInboundBarcodesUpdate();
}

/**
 * 處理首站遷出
 */
async function handleFirst() {
    const order = document.getElementById('orderInput').value.trim().toUpperCase();
    const seriesCode = document.getElementById('seriesSelect').value;
    const modelCode = document.getElementById('modelSelect').value;
    const container = document.getElementById('firstContainerSelect').value;
    const status = document.getElementById('firstStatusSelect').value;
    const qty = document.getElementById('firstQtyInput').value.trim();
    
    if (!order || !seriesCode || !modelCode || !container || !qty) {
        showAlert('錯誤', '請填寫所有必填欄位', 'error');
        return;
    }
    
    // 不立即關閉工作表，等待 API 回應後再決定
    showProcessing('處理中...', '正在計算箱子數量並生成條碼');
    
    try {
        const response = await fetch('/api/scan/first', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                order: order,
                operator_id: AppState.operatorId,
                current_station_id: AppState.currentStationId,
                series_code: seriesCode,
                model_code: modelCode,
                container: container,
                box_seq: null,  // 不再傳遞箱號，由系統自動計算
                status: status,
                qty: qty
            })
        });
        
        let data;
        try {
            data = await response.json();
        } catch (error) {
            // 如果無法解析 JSON，可能是服務器錯誤
            hideProcessing();
            closeBottomSheet();
            showAlert('錯誤', `伺服器回應格式錯誤：${response.status} ${response.statusText}`, 'error');
            playSound('error');
            if (navigator.vibrate) {
                navigator.vibrate([200, 100, 200]);
            }
            return;
        }
        
        if (!response.ok) {
            // 檢查是否為寫入失敗錯誤（500）
            const isWriteError = response.status === 500 && 
                                 (data.detail && data.detail.includes('寫入 Google Sheets 失敗'));
            
            if (isWriteError) {
                // 寫入失敗：不關閉工作表，顯示錯誤訊息，讓使用者可以再次提交
                hideProcessing();
                showAlert('寫入失敗', data.detail || '寫入 Google Sheets 失敗，請稍後再試', 'error');
                playSound('error');
                if (navigator.vibrate) {
                    navigator.vibrate([200, 100, 200]);
                }
                return; // 不關閉工作表，讓使用者可以重試
            } else {
                // 其他錯誤：關閉工作表並顯示錯誤
                hideProcessing();
                closeBottomSheet();
                // 422 錯誤通常是驗證錯誤，顯示詳細訊息
                const errorMessage = data.detail || (Array.isArray(data.detail) ? data.detail.map(e => e.msg || e).join(', ') : JSON.stringify(data));
                showAlert('錯誤', errorMessage || '首站遷出失敗', 'error');
                playSound('error');
                if (navigator.vibrate) {
                    navigator.vibrate([200, 100, 200]);
                }
                return;
            }
        }
        
        // 成功：關閉工作表並顯示多箱子資訊
        hideProcessing();
        closeBottomSheet();
        
        // 顯示多箱子資訊（與遷出一樣）
        showMultiBoxInfo(data.data);
        
        playSound('success');
        
    } catch (error) {
        // 檢查是否為網路錯誤（可能是寫入失敗）
        const isNetworkError = error.message.includes('fetch') || 
                               error.message.includes('Network') ||
                               error.message.includes('Failed to fetch');
        
        if (isNetworkError) {
            // 網路錯誤：不關閉工作表，顯示錯誤訊息
            hideProcessing();
            showAlert('網路錯誤', '無法連接到伺服器，請檢查網路連線後再試', 'error');
            playSound('error');
            if (navigator.vibrate) {
                navigator.vibrate([200, 100, 200]);
            }
        } else {
            // 其他錯誤：關閉工作表並顯示錯誤
            hideProcessing();
            closeBottomSheet();
        showAlert('錯誤', error.message, 'error');
        playSound('error');
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200]);
            }
        }
    }
}

/**
 * 顯示成功訊息卡片
 */
/**
 * 顯示處理中動畫
 */
function showProcessing(title = '處理中...', message = '正在寫入 Google Sheets') {
    const overlay = document.getElementById('processingOverlay');
    const titleEl = document.getElementById('processingTitle');
    const messageEl = document.getElementById('processingMessage');
    
    if (titleEl) titleEl.textContent = title;
    if (messageEl) messageEl.textContent = message;
    if (overlay) overlay.classList.remove('hidden');
}

/**
 * 隱藏處理中動畫
 */
function hideProcessing() {
    const overlay = document.getElementById('processingOverlay');
    if (overlay) overlay.classList.add('hidden');
}

function showSuccess(message, detail) {
    const card = document.getElementById('successCard');
    const warningCard = document.getElementById('warningCard');
    // 隱藏警告卡片
    if (warningCard) {
        warningCard.classList.add('hidden');
        warningCard.style.transform = 'translateY(-100%)';
        warningCard.style.opacity = '0';
    }
    document.getElementById('successMessage').textContent = message;
    document.getElementById('successDetail').textContent = detail;
    
    // 移除 hidden class
    card.classList.remove('hidden');
    
    // 觸發動畫：從頂部滑入
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            card.style.transform = 'translateY(0)';
            card.style.opacity = '1';
        });
    });
    
    // 3 秒後自動隱藏（帶動畫）
    setTimeout(() => {
        card.style.transform = 'translateY(-100%)';
        card.style.opacity = '0';
        setTimeout(() => {
            card.classList.add('hidden');
        }, 300); // 等待動畫完成
    }, 3000);
}

/**
 * 在主頁面訊息區域顯示訊息
 */
function showMainPageMessage(message, type = 'warning') {
    const successCard = document.getElementById('successCard');
    const warningCard = document.getElementById('warningCard');
    
    // 隱藏成功卡片（帶動畫）
    if (successCard) {
        successCard.style.transform = 'translateY(-100%)';
        successCard.style.opacity = '0';
        setTimeout(() => {
            successCard.classList.add('hidden');
        }, 300);
    }
    
    if (type === 'warning' && warningCard) {
        document.getElementById('warningMessage').textContent = message;
        // 移除 hidden class
        warningCard.classList.remove('hidden');
        // 觸發動畫：從頂部滑入
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                warningCard.style.transform = 'translateY(0)';
                warningCard.style.opacity = '1';
            });
        });
    } else if (successCard) {
        // 如果沒有警告卡片，使用成功卡片顯示
        document.getElementById('successMessage').textContent = message;
        document.getElementById('successDetail').textContent = '';
        // 移除 hidden class
        successCard.classList.remove('hidden');
        // 觸發動畫：從頂部滑入
        requestAnimationFrame(() => {
            requestAnimationFrame(() => {
                successCard.style.transform = 'translateY(0)';
                successCard.style.opacity = '1';
            });
        });
    }
}

/**
 * 顯示多箱子資訊（彈出視窗）
 */
function showMultiBoxInfo(data) {
    const qrcodeOverlay = document.getElementById('qrcodeOverlay');
    const qrcodeContainer = document.getElementById('qrcodeContainer');
    
    // 清空容器
    qrcodeContainer.innerHTML = '';
    
    // 創建多箱子資訊顯示
    // 1. 遷出資訊顯示在最上方
    let html = `
        <div class="mb-4 p-4 bg-blue-50 rounded-lg border-2 border-blue-200">
            <h4 class="font-semibold text-lg mb-2 text-blue-900">📦 遷出資訊</h4>
            <div class="text-sm text-blue-800 space-y-1">
                <p><strong>總箱子數：</strong>${data.total_boxes} 箱</p>
                <p><strong>總數量：</strong>${data.total_qty}</p>
                ${data.good_boxes > 0 ? `<p><strong>良品箱數：</strong>${data.good_boxes} 箱</p>` : ''}
                ${data.bad_boxes > 0 ? `<p><strong>不良品箱數：</strong>${data.bad_boxes} 箱</p>` : ''}
                ${data.next_station ? `<p><strong>下一站建議：</strong>${data.next_station}</p>` : ''}
            </div>
        </div>
        
        <div class="mb-4">
            <h4 class="font-semibold text-lg mb-3 text-gray-900">各箱子明細</h4>
    `;
    
    // 分組顯示：先顯示良品，再顯示不良品
    const goodBoxes = data.boxes.filter(box => box.item_type === '良品');
    const badBoxes = data.boxes.filter(box => box.item_type === '不良品');
    
    // 良品箱子
    if (goodBoxes.length > 0) {
        html += `
            <div class="mb-4">
                <h5 class="font-semibold text-md mb-2 text-green-700 flex items-center">
                    <span class="w-3 h-3 rounded-full bg-green-500 mr-2"></span>
                    良品（${goodBoxes.length} 箱）
                </h5>
                <div class="space-y-3" id="goodBoxesList">
        `;
        
        goodBoxes.forEach((box, index) => {
            html += `
                <div class="p-3 bg-green-50 rounded-lg border border-green-200">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-semibold text-gray-900">第 ${box.box_num} 箱（箱號：${box.box_seq}）</span>
                        <span class="text-green-600 font-semibold">數量：${box.qty}</span>
                    </div>
                    <div class="text-xs text-gray-600 mb-2">條碼：${box.barcode}</div>
                    <div class="flex justify-center" id="qrcode-box-${box.box_num}">
                        ${box.qr_code_svg}
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    // 不良品箱子
    if (badBoxes.length > 0) {
        html += `
            <div class="mb-4">
                <h5 class="font-semibold text-md mb-2 text-red-700 flex items-center">
                    <span class="w-3 h-3 rounded-full bg-red-500 mr-2"></span>
                    不良品（${badBoxes.length} 箱）
                </h5>
                <div class="space-y-3" id="badBoxesList">
        `;
        
        badBoxes.forEach((box, index) => {
            html += `
                <div class="p-3 bg-red-50 rounded-lg border border-red-200">
                    <div class="flex items-center justify-between mb-2">
                        <span class="font-semibold text-gray-900">第 ${box.box_num} 箱（箱號：${box.box_seq}）</span>
                        <span class="text-red-600 font-semibold">數量：${box.qty}</span>
                    </div>
                    <div class="text-xs text-gray-600 mb-2">條碼：${box.barcode}</div>
                    <div class="flex justify-center" id="qrcode-box-${box.box_num}">
                        ${box.qr_code_svg}
                    </div>
                </div>
            `;
        });
        
        html += `
                </div>
            </div>
        `;
    }
    
    html += `
            </div>
        </div>
        
        <!-- 下載按鈕維持出現在最下面 -->
        <button 
            id="downloadAllQRCodesBtn" 
            class="btn-capsule w-full bg-blue-500 text-white mb-2"
        >
            📥 下載所有 QR Code（PDF）
        </button>
    `;
    
    qrcodeContainer.innerHTML = html;
    
    // 儲存所有箱子的資料供下載使用
    qrcodeContainer.dataset.boxesData = JSON.stringify(data.boxes);
    qrcodeContainer.dataset.order = data.order;
    
    // 綁定下載按鈕事件
    const downloadBtn = document.getElementById('downloadAllQRCodesBtn');
    if (downloadBtn) {
        // 移除舊的事件監聽器（如果有的話）
        downloadBtn.replaceWith(downloadBtn.cloneNode(true));
        // 重新綁定事件
        const downloadAllBtn = document.getElementById('downloadAllQRCodesBtn');
        if (downloadAllBtn) {
            downloadAllBtn.addEventListener('click', () => downloadAllQRCodes(data));
        }
    }
    
    // 顯示 QR Code 彈出視窗
    if (qrcodeOverlay) {
        qrcodeOverlay.classList.remove('hidden');
    }
    
    // 顯示成功訊息
    let detail = `共產生 ${data.total_boxes} 個箱子\n總數量：${data.total_qty}`;
    if (data.next_station) {
        detail += `\n下一站建議：${data.next_station}`;
    }
    showSuccess('遷出成功', detail);
}

/**
 * 顯示 QR Code（單個，保留用於其他功能）
 */
function showQRCode(svgString, barcode) {
    const qrcodeOverlay = document.getElementById('qrcodeOverlay');
    const qrcodeContainer = document.getElementById('qrcodeContainer');
    
    // 清空容器
    qrcodeContainer.innerHTML = '';
    
    // 創建單個 QR Code 顯示
    qrcodeContainer.innerHTML = `
        <div class="flex justify-center mb-4">
            ${svgString}
        </div>
        <div class="text-center mb-4">
            <p class="text-sm text-gray-600 mb-2">條碼：${barcode}</p>
        </div>
        <button 
            id="downloadQrcodeBtn" 
            class="btn-capsule w-full bg-blue-500 text-white"
        >
            📥 下載 QR Code
        </button>
    `;
    
    // 儲存條碼供下載使用
    qrcodeContainer.dataset.barcode = barcode;
    qrcodeContainer.dataset.svg = svgString;
    
    // 綁定下載按鈕事件
    const downloadBtn = document.getElementById('downloadQrcodeBtn');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', downloadQRCode);
    }
    
    // 顯示 QR Code 彈出視窗
    if (qrcodeOverlay) {
        qrcodeOverlay.classList.remove('hidden');
    }
}

/**
 * 關閉 QR Code 彈出視窗
 */
function closeQRCodeModal() {
    const qrcodeOverlay = document.getElementById('qrcodeOverlay');
    if (qrcodeOverlay) {
        qrcodeOverlay.classList.add('hidden');
    }
}

/**
 * 顯示條碼選擇界面（全畫面彈出視窗）
 */
function showBarcodeSelection(barcodes, scannedBarcode, onConfirm) {
    console.log('showBarcodeSelection 被調用，條碼數量:', barcodes ? barcodes.length : 0, '掃描的條碼:', scannedBarcode);
    console.log('條碼數據:', barcodes);
    
    // 檢查數據有效性
    if (!barcodes || !Array.isArray(barcodes) || barcodes.length === 0) {
        console.error('條碼數據無效或為空:', barcodes);
        showAlert('提示', '沒有找到可遷入的條碼', 'info');
        return;
    }
    
    const overlay = document.getElementById('barcodeSelectionOverlay');
    if (!overlay) {
        console.error('找不到條碼選擇彈出視窗元素');
        // 如果找不到元素，直接執行遷入
        performInbound([scannedBarcode]);
        return;
    }
    
    // 在彈出視窗中查找列表元素（避免找到底部工作表中的舊元素）
    const listDiv = overlay.querySelector('#barcodeSelectionList');
    
    if (!listDiv) {
        console.error('找不到條碼選擇列表元素');
        // 如果找不到元素，直接執行遷入
        performInbound([scannedBarcode]);
        return;
    }
    
    // 清空列表
    listDiv.innerHTML = '';
    
    // 預設選中的條碼（包含掃描的條碼）
    const selectedBarcodes = new Set([scannedBarcode]);
    
    // 輔助函數：取得貨態說明文字
    function getStatusName(statusCode) {
        if (!statusCode) return 'N/A';
        
        // 如果 statusOptions 已載入，使用配置檔中的名稱
        if (AppState.statusOptions && AppState.statusOptions.length > 0) {
            const status = AppState.statusOptions.find(s => s.code === statusCode.toUpperCase());
            if (status) {
                return status.name;
            }
        }
        
        // 如果找不到配置，使用預設映射
        const statusMap = {
            'G': '良品',
            'N': '不良',
            'S': '特採',
            'R': '返工',
            'E': '遺失'
        };
        
        return statusMap[statusCode.toUpperCase()] || statusCode;
    }
    
    // 輔助函數：取得容器說明文字
    function getContainerName(containerCode) {
        if (!containerCode) return 'N/A';
        const container = AppState.containerOptions.find(c => c.code.toUpperCase() === containerCode.toUpperCase());
        return container ? container.name : containerCode;
    }
    
    // 儲存所有 checkbox 引用，用於全選/全部取消
    const checkboxElements = [];
    
    // 為每個條碼創建選擇項目
    barcodes.forEach((item, index) => {
        const isSelected = selectedBarcodes.has(item.barcode);
        const itemDiv = document.createElement('div');
        itemDiv.className = `flex items-center p-3 bg-white rounded-lg border-2 ${isSelected ? 'border-blue-500 bg-blue-50' : 'border-gray-200'}`;
        itemDiv.innerHTML = `
            <input 
                type="checkbox" 
                class="w-5 h-5 text-blue-600 rounded focus:ring-blue-500 mr-3" 
                data-barcode="${item.barcode}"
                ${isSelected ? 'checked' : ''}
            >
            <div class="flex-1">
                <div class="font-semibold text-sm text-gray-900">條碼：${item.barcode}</div>
                <div class="text-xs text-gray-600 mt-1">
                    箱號：${item.box_seq || 'N/A'} | 數量：<span class="font-bold text-blue-600">${item.qty || 'N/A'}</span> | 貨態：${getStatusName(item.status)} | 容器：${getContainerName(item.container)}
                </div>
            </div>
        `;
        
        // 綁定 checkbox 事件
        const checkbox = itemDiv.querySelector('input[type="checkbox"]');
        if (checkbox) {
            checkboxElements.push({ checkbox, itemDiv, barcode: item.barcode });
            
            checkbox.addEventListener('change', (e) => {
                if (e.target.checked) {
                    selectedBarcodes.add(item.barcode);
                    itemDiv.classList.remove('border-gray-200');
                    itemDiv.classList.add('border-blue-500', 'bg-blue-50');
                } else {
                    selectedBarcodes.delete(item.barcode);
                    itemDiv.classList.remove('border-blue-500', 'bg-blue-50');
                    itemDiv.classList.add('border-gray-200');
                }
            });
        }
        
        listDiv.appendChild(itemDiv);
    });
    
    // 綁定全選按鈕（從彈出視窗中查找）
    const selectAllBtn = overlay.querySelector('#selectAllBarcodesBtn');
    if (selectAllBtn) {
        selectAllBtn.onclick = () => {
            checkboxElements.forEach(({ checkbox, itemDiv, barcode }) => {
                checkbox.checked = true;
                selectedBarcodes.add(barcode);
                itemDiv.classList.remove('border-gray-200');
                itemDiv.classList.add('border-blue-500', 'bg-blue-50');
            });
        };
    }
    
    // 綁定全部取消按鈕（從彈出視窗中查找）
    const deselectAllBtn = overlay.querySelector('#deselectAllBarcodesBtn');
    if (deselectAllBtn) {
        deselectAllBtn.onclick = () => {
            checkboxElements.forEach(({ checkbox, itemDiv, barcode }) => {
                checkbox.checked = false;
                selectedBarcodes.delete(barcode);
                itemDiv.classList.remove('border-blue-500', 'bg-blue-50');
                itemDiv.classList.add('border-gray-200');
            });
        };
    }
    
    // 綁定確認按鈕（從彈出視窗中查找）
    const confirmBtn = overlay.querySelector('#confirmInboundBtn');
    if (!confirmBtn) {
        console.error('找不到確認按鈕元素');
    } else {
        // 移除舊的事件監聽器（如果有的話）
        const newConfirmBtn = confirmBtn.cloneNode(true);
        confirmBtn.parentNode.replaceChild(newConfirmBtn, confirmBtn);
        
        // 重新綁定事件
        const currentConfirmBtn = overlay.querySelector('#confirmInboundBtn');
        currentConfirmBtn.onclick = function handleConfirm(e) {
            e.preventDefault();
            e.stopPropagation();
            
            const selectedList = Array.from(selectedBarcodes);
            console.log('確認遷入，選中的條碼:', selectedList);
            
            if (selectedList.length === 0) {
                showAlert('錯誤', '請至少選擇一個條碼', 'error');
                return;
            }
            
            // 隱藏彈出視窗
            overlay.classList.add('hidden');
            
            // 執行確認回調
            onConfirm(selectedList);
        };
        
        // 確保按鈕可見
        currentConfirmBtn.style.display = 'block';
        console.log('確認按鈕已綁定並顯示');
    }
    
    // 綁定關閉按鈕（從彈出視窗中查找）
    const closeBtn = overlay.querySelector('#closeBarcodeSelectionBtn');
    if (closeBtn) {
        closeBtn.onclick = () => {
            overlay.classList.add('hidden');
        };
    }
    
    // 顯示全畫面彈出視窗
    overlay.classList.remove('hidden');
    console.log('條碼選擇界面已顯示，條碼數量:', barcodes.length);
}

/**
 * 下載所有 QR Code 為 PDF
 */
async function downloadAllQRCodes(data) {
    try {
        // 使用 jsPDF 和 html2canvas 來生成 PDF
        // 如果沒有這些庫，我們使用 SVG 轉換的方式
        
        // 創建一個臨時的 HTML 頁面來包含所有 QR Code
        const htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>QR Codes - ${data.order}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 20px;
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .header p {
            margin: 5px 0;
            color: #666;
        }
        .box-container {
            page-break-inside: avoid;
            margin-bottom: 30px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }
        .box-header {
            font-weight: bold;
            font-size: 16px;
            margin-bottom: 10px;
        }
        .box-info {
            font-size: 12px;
            color: #666;
            margin-bottom: 10px;
        }
        .qrcode {
            text-align: center;
            margin: 10px 0;
        }
        .qrcode svg {
            max-width: 200px;
            height: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>遷出條碼 QR Code</h1>
        <p>工單號：${data.order}</p>
        <p>總箱子數：${data.total_boxes} 箱 | 總數量：${data.total_qty}</p>
        <p>容器：${data.container_code}（容量：${data.container_capacity}）</p>
    </div>
    
    ${data.boxes.map((box, index) => `
        <div class="box-container">
            <div class="box-header">第 ${box.box_num} 箱（箱號：${box.box_seq}）</div>
            <div class="box-info">
                數量：${box.qty}<br>
                條碼：${box.barcode}
            </div>
            <div class="qrcode">
                ${box.qr_code_svg}
            </div>
        </div>
    `).join('')}
</body>
</html>
        `;
        
        // 創建 Blob 並下載為 HTML（用戶可以在瀏覽器中列印為 PDF）
        const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = `QRCodes_${data.order}_${new Date().getTime()}.html`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        // 釋放 URL
        setTimeout(() => {
            URL.revokeObjectURL(url);
        }, 100);
        
        showSuccess('下載成功', `所有 QR Code 已下載為 HTML 檔案，可在瀏覽器中開啟並列印為 PDF`);
        
    } catch (error) {
        console.error('下載 QR Code 失敗：', error);
        showAlert('錯誤', '下載 QR Code 時發生錯誤', 'error');
    }
}

/**
 * 下載 QR Code SVG（單個，保留用於其他功能）
 */
function downloadQRCode() {
    const qrcodeContainer = document.getElementById('qrcodeCard');
    const container = document.getElementById('qrcodeContainer');
    
    if (!container || !container.dataset.svg || !container.dataset.barcode) {
        showAlert('錯誤', '沒有可下載的 QR Code', 'error');
        return;
    }
    
    const svgString = container.dataset.svg;
    const barcode = container.dataset.barcode;
    
    // 創建 Blob
    const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
    
    // 創建下載連結
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `QRCode_${barcode.replace(/[^A-Z0-9]/g, '_')}.svg`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // 釋放 URL
    setTimeout(() => {
        URL.revokeObjectURL(url);
    }, 100);
    
    // 顯示成功訊息
    showSuccess('下載成功', `QR Code 已下載：${link.download}`);
}

/**
 * 顯示警示視窗
 */
function showAlert(title, message, type = 'error') {
    const overlay = document.getElementById('alertOverlay');
    document.getElementById('alertTitle').textContent = title;
    document.getElementById('alertMessage').textContent = message;
    
    // 根據類型設定圖示和顏色
    if (type === 'error') {
        document.getElementById('alertIcon').textContent = '❌';
        document.getElementById('alertOkBtn').className = 'btn-capsule w-full bg-red-500 text-white';
    } else {
        document.getElementById('alertIcon').textContent = '⚠️';
        document.getElementById('alertOkBtn').className = 'btn-capsule w-full bg-blue-500 text-white';
    }
    
    overlay.classList.remove('hidden');
}

/**
 * 關閉警示視窗
 */
function closeAlert() {
    document.getElementById('alertOverlay').classList.add('hidden');
}

/**
 * 播放音效
 */
function playSound(type) {
    // 嘗試播放音效檔（如果存在）
    try {
        const audio = new Audio(`/static/sounds/${type}.mp3`);
        audio.play().catch(() => {
            // 如果音效檔不存在或播放失敗，忽略錯誤
        });
    } catch (e) {
        // 忽略錯誤
    }
}

