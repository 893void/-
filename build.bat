@echo off
chcp 65001 > nul
echo ============================================================
echo ほあんペディア ビルドシステム
echo ============================================================
echo.

python build.py %*

if errorlevel 1 (
    echo.
    echo [エラー] ビルドに失敗しました。
    pause
) else (
    echo.
    echo ビルドが完了しました。
    timeout /t 3 > nul
)
