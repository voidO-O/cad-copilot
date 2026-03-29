@echo off
echo ==========================
echo   CAD Copilot 
echo ==========================

REM 激活conda
call D:\conda\Scripts\activate.bat cad

REM 进入项目目录
cd /d "D:\cad copilot\cad-copilot\src"

REM 启动程序
python main.py

pause