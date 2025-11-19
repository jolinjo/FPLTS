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
    containerOptions: [] // 容器選項
};

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    setupEventListeners();
    loadConfigOptions();
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
    
    // 載入已儲存的值（如果有的話）
    const savedOperator = localStorage.getItem('operatorId');
    const savedStation = localStorage.getItem('currentStationId');
    
    if (savedOperator) {
        document.getElementById('operatorInput').value = savedOperator;
    }
    if (savedStation) {
        document.getElementById('stationSelect').value = savedStation;
    }
}

/**
 * 顯示主功能頁
 */
function showMainPage() {
    document.getElementById('setupPage').classList.add('hidden');
    document.getElementById('mainPage').classList.remove('hidden');
    
    // 更新顯示資訊
    document.getElementById('operatorDisplay').textContent = AppState.operatorId;
    document.getElementById('stationDisplay').textContent = AppState.currentStationId;
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
        processPendingBarcode();
    }
}

/**
 * 處理待處理的條碼（從 sessionStorage 或 URL 參數）
 * 預設開啟遷入功能
 */
function processPendingBarcode() {
    const pendingBarcode = sessionStorage.getItem('pendingBarcode');
    
    if (pendingBarcode && AppState.operatorId && AppState.currentStationId) {
        // 清除待處理的條碼
        sessionStorage.removeItem('pendingBarcode');
        
        // 等待頁面完全載入後處理
        setTimeout(() => {
            // 預設開啟遷入功能
            openBottomSheet('inbound', '貨物遷入');
            
            // 自動填入條碼
            setTimeout(() => {
                const barcodeInput = document.getElementById('barcodeInput');
                if (barcodeInput) {
                    barcodeInput.value = pendingBarcode;
                    // 自動聚焦到輸入框
                    barcodeInput.focus();
                }
            }, 350);
        }, 500);
    }
}

/**
 * 設定事件監聽器
 */
function setupEventListeners() {
    // 設定頁
    document.getElementById('saveSetupBtn').addEventListener('click', saveSetup);
    
    // 主功能頁
    document.getElementById('changeSetupBtn').addEventListener('click', () => {
        showSetupPage();
    });
    
    document.getElementById('inboundBtn').addEventListener('click', () => {
        openBottomSheet('inbound', '貨物遷入');
    });
    
    document.getElementById('outboundBtn').addEventListener('click', () => {
        openBottomSheet('outbound', '貨物遷出');
    });
    
    document.getElementById('traceBtn').addEventListener('click', () => {
        openBottomSheet('trace', '追溯查詢');
    });
    
    document.getElementById('firstBtn').addEventListener('click', () => {
        openBottomSheet('first', '首站遷出');
    });
    
    // 底部工作表
    document.getElementById('closeSheetBtn').addEventListener('click', closeBottomSheet);
    document.getElementById('submitBtn').addEventListener('click', handleSubmit);
    
    // 警示視窗
    document.getElementById('alertOkBtn').addEventListener('click', closeAlert);
    
    // 條碼輸入框 Enter 鍵
    document.getElementById('barcodeInput').addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            handleSubmit();
        }
    });
    
    // 工單號輸入框自動轉換為大寫
    const orderInput = document.getElementById('orderInput');
    if (orderInput) {
        orderInput.addEventListener('input', (e) => {
            e.target.value = e.target.value.toUpperCase();
        });
    }
}

/**
 * 儲存設定
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
    
    // 顯示成功訊息
    showSuccess('設定已儲存', `操作員：${operatorId}，站點：${currentStationId}`);
    
    // 檢查是否有待處理的條碼（從 QR code 掃描）
    processPendingBarcode();
}

/**
 * 載入設定選項（產品線、機種和容器）
 */
async function loadConfigOptions() {
    try {
        // 載入產品線選項
        const seriesResponse = await fetch('/api/config/series');
        const seriesData = await seriesResponse.json();
        if (seriesData.success) {
            AppState.seriesOptions = seriesData.data;
            updateSeriesSelect();
        }
        
        // 載入機種選項
        const modelResponse = await fetch('/api/config/models');
        const modelData = await modelResponse.json();
        if (modelData.success) {
            AppState.modelOptions = modelData.data;
            updateModelSelect();
        }
        
        // 載入容器選項
        const containerResponse = await fetch('/api/config/containers');
        const containerData = await containerResponse.json();
        if (containerData.success) {
            AppState.containerOptions = containerData.data;
            updateContainerSelects();
        }
    } catch (error) {
        console.error('載入設定選項失敗：', error);
    }
}

/**
 * 更新產品線下拉選單
 */
function updateSeriesSelect() {
    const select = document.getElementById('seriesSelect');
    // 保留第一個選項（請選擇產品線）
    select.innerHTML = '<option value="">請選擇產品線</option>';
    
    // 添加所有產品線選項
    AppState.seriesOptions.forEach(series => {
        const option = document.createElement('option');
        option.value = series.code;
        option.textContent = `${series.code} - ${series.name}`;
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
    
    // 添加所有機種選項
    AppState.modelOptions.forEach(model => {
        const option = document.createElement('option');
        option.value = model.code;
        option.textContent = `${model.code} - ${model.name}`;
        select.appendChild(option);
    });
}

/**
 * 更新容器下拉選單（遷出和首站遷出）
 */
function updateContainerSelects() {
    // 更新遷出容器選單
    const outboundSelect = document.getElementById('containerSelect');
    if (outboundSelect) {
        outboundSelect.innerHTML = '<option value="">請選擇容器</option>';
        AppState.containerOptions.forEach(container => {
            const option = document.createElement('option');
            option.value = container.code;
            option.textContent = `${container.code} - 容量 ${container.capacity}`;
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
            option.textContent = `${container.code} - 容量 ${container.capacity}`;
            firstSelect.appendChild(option);
        });
    }
}

/**
 * 開啟底部工作表
 */
function openBottomSheet(mode, title) {
    AppState.currentMode = mode;
    document.getElementById('sheetTitle').textContent = title;
    
    // 重置表單
    document.getElementById('barcodeInput').value = '';
    document.getElementById('outboundFields').classList.add('hidden');
    document.getElementById('firstFields').classList.add('hidden');
    
    // 根據模式顯示對應欄位
    if (mode === 'outbound') {
        document.getElementById('outboundFields').classList.remove('hidden');
        // 重置容器選擇
        document.getElementById('containerSelect').value = '';
    } else if (mode === 'first') {
        document.getElementById('firstFields').classList.remove('hidden');
        // 重置產品線、機種和容器選擇
        document.getElementById('seriesSelect').value = '';
        document.getElementById('modelSelect').value = '';
        document.getElementById('firstContainerSelect').value = '';
        // 重置工單號
        document.getElementById('orderInput').value = '';
    }
    
    // 顯示底部工作表
    document.getElementById('bottomSheet').classList.add('open');
    
    // 聚焦到條碼輸入框（如果不是首站遷出）
    if (mode !== 'first') {
        setTimeout(() => {
            document.getElementById('barcodeInput').focus();
        }, 300);
    }
}

/**
 * 關閉底部工作表
 */
function closeBottomSheet() {
    document.getElementById('bottomSheet').classList.remove('open');
    AppState.currentMode = null;
}

/**
 * 處理提交
 */
async function handleSubmit() {
    const mode = AppState.currentMode;
    
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
    
    // 樂觀 UI：立即顯示成功（假設會成功）
    closeBottomSheet();
    showSuccess('處理中...', '正在驗證流程並記錄遷入');
    
    try {
        const response = await fetch('/api/scan/inbound', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                barcode: barcode,
                operator_id: AppState.operatorId,
                current_station_id: AppState.currentStationId
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            // 收到 400 錯誤（流程錯誤等）
            throw new Error(data.detail || '遷入失敗');
        }
        
        // 成功：更新成功訊息
        showSuccess('遷入成功', `工單：${data.data.order}，SKU：${data.data.sku}`);
        
        // 播放成功音效（如果有）
        playSound('success');
        
    } catch (error) {
        // 錯誤：立即彈出紅色警示視窗
        showAlert('流程錯誤', error.message, 'error');
        playSound('error');
        
        // 震動（如果支援）
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200]);
        }
    }
}

/**
 * 處理遷出（樂觀 UI + 錯誤處理）
 */
async function handleOutbound() {
    const barcode = document.getElementById('barcodeInput').value.trim();
    const container = document.getElementById('containerSelect').value;
    const boxSeq = document.getElementById('boxSeqInput').value.trim();
    const status = document.getElementById('statusSelect').value;
    const qty = document.getElementById('qtyInput').value.trim();
    
    if (!barcode) {
        showAlert('錯誤', '請輸入或掃描條碼', 'error');
        return;
    }
    
    // 樂觀 UI
    closeBottomSheet();
    showSuccess('處理中...', '正在生成新條碼並記錄遷出');
    
    try {
        const response = await fetch('/api/scan/outbound', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                barcode: barcode,
                operator_id: AppState.operatorId,
                current_station_id: AppState.currentStationId,
                container: container || null,
                box_seq: boxSeq || null,
                status: status || null,
                qty: qty || null
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '遷出失敗');
        }
        
        // 成功：顯示新條碼和下一站建議
        let detail = `新條碼：${data.data.new_barcode}`;
        if (data.data.next_station) {
            detail += `\n下一站建議：${data.data.next_station}`;
        }
        showSuccess('遷出成功', detail);
        playSound('success');
        
    } catch (error) {
        showAlert('錯誤', error.message, 'error');
        playSound('error');
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200]);
        }
    }
}

/**
 * 處理追溯查詢
 */
async function handleTrace() {
    const barcode = document.getElementById('barcodeInput').value.trim();
    
    if (!barcode) {
        showAlert('錯誤', '請輸入或掃描條碼', 'error');
        return;
    }
    
    closeBottomSheet();
    showSuccess('查詢中...', '正在查詢追溯記錄');
    
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
        
        if (!response.ok) {
            throw new Error(data.detail || '查詢失敗');
        }
        
        // 顯示追溯結果
        const stats = data.data.statistics;
        const detail = `工單：${data.data.order}\n總數量：${stats.total_qty}\n良品：${stats.good_qty}\n良率：${stats.yield_rate}%`;
        showSuccess('查詢成功', detail);
        playSound('success');
        
    } catch (error) {
        showAlert('錯誤', error.message, 'error');
        playSound('error');
    }
}

/**
 * 處理首站遷出
 */
async function handleFirst() {
    const order = document.getElementById('orderInput').value.trim().toUpperCase();
    const seriesCode = document.getElementById('seriesSelect').value;
    const modelCode = document.getElementById('modelSelect').value;
    const container = document.getElementById('firstContainerSelect').value;
    const boxSeq = document.getElementById('firstBoxSeqInput').value.trim();
    const status = document.getElementById('firstStatusSelect').value;
    const qty = document.getElementById('firstQtyInput').value.trim();
    
    if (!order || !seriesCode || !modelCode || !container || !boxSeq || !qty) {
        showAlert('錯誤', '請填寫所有必填欄位', 'error');
        return;
    }
    
    closeBottomSheet();
    showSuccess('處理中...', '正在生成首站條碼');
    
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
                box_seq: boxSeq,
                status: status,
                qty: qty
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || '首站遷出失敗');
        }
        
        // 成功：顯示新條碼
        let detail = `新條碼：${data.data.barcode}`;
        if (data.data.sku) {
            detail += `\nSKU：${data.data.sku}`;
        }
        if (data.data.next_station) {
            detail += `\n下一站建議：${data.data.next_station}`;
        }
        showSuccess('首站遷出成功', detail);
        playSound('success');
        
    } catch (error) {
        showAlert('錯誤', error.message, 'error');
        playSound('error');
        if (navigator.vibrate) {
            navigator.vibrate([200, 100, 200]);
        }
    }
}

/**
 * 顯示成功訊息卡片
 */
function showSuccess(message, detail) {
    const card = document.getElementById('successCard');
    document.getElementById('successMessage').textContent = message;
    document.getElementById('successDetail').textContent = detail;
    card.classList.remove('hidden');
    
    // 3 秒後自動隱藏
    setTimeout(() => {
        card.classList.add('hidden');
    }, 3000);
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

