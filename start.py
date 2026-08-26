#!/usr/bin/env python3
"""一键启动：创建虚拟环境 → 安装依赖 → 运行 App。

前提：系统已安装 Python 3.9 或更高版本（无需 Docker / 无需编译）。
用法：
    Windows:    python start.py   （或双击 run.bat）
    Linux/macOS: python3 start.py （或 ./run.sh）
首次运行会自动联网安装依赖（Flask、waitress），之后打开 http://localhost:5000。
"""
import os
import subprocess
import sys
import venv

BASE = os.path.dirname(os.path.abspath(__file__))
VENV_DIR = os.path.join(BASE, ".venv")
IS_WIN = os.name == "nt"
PY = os.path.join(VENV_DIR, "Scripts", "python.exe") if IS_WIN else os.path.join(VENV_DIR, "bin", "python")


def ensure_venv():
    if os.path.exists(PY):
        return
    print("[1/3] 创建虚拟环境 .venv ...")
    venv.EnvBuilder(with_pip=True).create(VENV_DIR)
    print("[2/3] 安装依赖（首次需要联网）...")
    subprocess.check_call([PY, "-m", "pip", "install", "--upgrade", "pip"])
    subprocess.check_call([PY, "-m", "pip", "install", "-r", os.path.join(BASE, "requirements.txt")])
    print("[3/3] 依赖安装完成。")


def main():
    ensure_venv()
    os.chdir(BASE)
    print("启动服务：http://localhost:5000  （Ctrl+C 退出）")
    os.execv(PY, [PY, os.path.join(BASE, "app.py")])


if __name__ == "__main__":
    main()
