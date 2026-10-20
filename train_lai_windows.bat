@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Hãy mở cai_dat_windows.bat trước.
    pause
    exit /b 1
)
if not exist "data\mrlEyes_2018_01.zip" (
    echo Đang tải bộ dữ liệu MRL Eye gốc khoảng 326 MB...
    ".venv\Scripts\python.exe" download_data.py
    if errorlevel 1 (
        echo Tải dữ liệu thất bại. Hãy kiểm tra Internet.
        pause
        exit /b 1
    )
)
echo Đang huấn luyện mô hình từ MRL và ảnh mắt do bạn tự thu...
".venv\Scripts\python.exe" train.py --dataset "data\mrlEyes_2018_01.zip"
if errorlevel 1 (
    echo Huấn luyện thất bại.
    pause
    exit /b 1
)
echo Đã cập nhật mô hình! Xem models\evaluation.json để xem kết quả.
pause
