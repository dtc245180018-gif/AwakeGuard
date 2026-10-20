@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo [1/2] Đang tạo môi trường Python riêng...
py -3.12 -m venv .venv
if errorlevel 1 (
    echo Lỗi: Hãy cài Python 3.12 từ python.org và bật Python Launcher.
    pause
    exit /b 1
)
echo [2/2] Đang cài các thư viện cần thiết...
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Cài thư viện thất bại. Kiểm tra Internet và chạy lại.
    pause
    exit /b 1
)
echo Đã cài đặt. Mở file chay_camera_windows.bat để sử dụng.
pause
