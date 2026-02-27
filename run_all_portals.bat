@echo off
REM 引数なし: G:\共有ドライブ\★OD\99_Ops\アーカイブ(Stock) 配下の直近日付(yyyy-MM-dd)を対象
REM 引数あり: 第1引数をベースディレクトリ、第2引数を setting.json のパスとして使用
chcp 65001 >nul 2>&1
pushd "%~dp0."
python run_all_portals.py %*
set EXIT_CODE=%ERRORLEVEL%
popd
exit /b %EXIT_CODE%
