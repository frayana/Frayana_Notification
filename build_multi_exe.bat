@echo off
REM Build script for creating Multi-Feed Viewer executable

echo ========================================
echo Building Multi-Feed Viewer GUI
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>NUL
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    echo.
)

REM Build the executable (--noconsole hides the command prompt window)
echo Building executable...
pyinstaller --onefile --noconsole --name "MultiFeedViewer" feed_viewer_multi.py

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Your executable is located at: dist\MultiFeedViewer.exe
echo.
echo This version has TABS for multiple feeds!
echo - Soul of Fire feed
echo - NeoDarkLand feed
echo.
echo Just double-click to run - no command prompt needed!
echo.
pause
