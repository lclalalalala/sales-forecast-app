@echo off
REM ============================================================
REM Windows 桌面应用构建脚本
REM ------------------------------------------------------------
REM 依次：构建前端 -> PyInstaller 打包 -> 产物在 dist\库存预测系统.exe
REM
REM 前置：
REM   conda activate dev
REM   pip install -r requirements-desktop.txt
REM   (前端) cd app ^&^& npm install
REM   Windows 需安装 Microsoft Edge WebView2 Runtime（多数系统已内置）
REM ============================================================
setlocal
cd /d "%~dp0"

echo ==^> [1/3] 构建前端 (vite build, 使用 .env.production)
pushd app
call npm run build
if errorlevel 1 goto :error
popd

echo ==^> [2/3] 清理旧产物
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo ==^> [3/3] PyInstaller 打包
pyinstaller desktop.spec --noconfirm
if errorlevel 1 goto :error

echo.
echo [OK] 构建完成：%cd%\dist\库存预测系统.exe
goto :eof

:error
echo.
echo [ERROR] 构建失败，请检查上方日志。
exit /b 1
