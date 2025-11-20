#!/bin/bash
# 啟動腳本 - 自動啟動虛擬環境並運行服務

# 切換到專案根目錄（腳本位於 scripts/ 目錄下）
cd "$(dirname "$0")/.."

# 檢查虛擬環境是否存在
if [ ! -d "venv" ]; then
    echo "正在建立虛擬環境..."
    python3 -m venv venv
fi

# 啟動虛擬環境
source venv/bin/activate

# 檢查依賴是否已安裝
if ! python -c "import fastapi" 2>/dev/null; then
    echo "正在安裝依賴套件..."
    pip install -r requirements.txt
fi

# 啟動 FastAPI 服務
echo "正在啟動服務..."
echo "訪問 http://localhost:8000 查看應用程式"
python main.py


