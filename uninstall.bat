@echo off
cd /d %~dp0
echo [卸载] 跨境个人税务助理（Python 版）
echo.
if exist .venv (
  rmdir /s /q .venv
  echo 已删除虚拟环境 .venv
) else (
  echo 未找到 .venv（可能已清理）
)
echo.
echo 完成。现在删除整个「temporaryPythonRelease」文件夹即可彻底卸载。
echo.
pause
