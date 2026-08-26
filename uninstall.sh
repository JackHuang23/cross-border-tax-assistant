#!/usr/bin/env bash
cd "$(dirname "$0")"
echo "[卸载] 跨境个人税务助理（Python 版）"
if [ -d .venv ]; then
  rm -rf .venv
  echo "已删除虚拟环境 .venv"
else
  echo "未找到 .venv（可能已清理）"
fi
echo "完成。现在删除整个文件夹即可彻底卸载：$(pwd)"
